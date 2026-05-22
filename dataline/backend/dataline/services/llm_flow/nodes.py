from abc import ABC, abstractmethod
from typing import cast

from langchain_core.messages import AIMessage, BaseMessage, ToolCall, ToolMessage
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_community.chat_models import ChatLiteLLM
from langgraph.graph import END
import litellm

from dataline.errors import UserFacingError
from dataline.models.llm_flow.schema import QueryResultSchema
from dataline.services.llm_flow.llm_provider import (
    set_provider_key,
    restore_provider_key,
)
from dataline.services.llm_flow.toolkit import (
    ChartGeneratorTool,
    QueryGraphState,
    QueryGraphStateUpdate,
    StateUpdaterTool,
    state_update,
)

NodeName = str


class Node(ABC):
    name: NodeName

    @classmethod
    @abstractmethod
    def run(cls, state: QueryGraphState) -> QueryGraphStateUpdate:
        raise NotImplementedError


class Edge(ABC):
    @classmethod
    @abstractmethod
    def run(cls, state: QueryGraphState) -> NodeName:
        raise NotImplementedError


class Condition(ABC):
    @classmethod
    @abstractmethod
    def run(cls, state: QueryGraphState) -> NodeName:
        raise NotImplementedError


class CallModelNode(Node):
    __name__ = "call_model"

    @classmethod
    def run(cls, state: QueryGraphState) -> QueryGraphStateUpdate:
        api_key = state.options.openai_api_key.get_secret_value()
        model_name = state.options.llm_model
        api_base = state.options.openai_base_url

        # Set provider-specific env var (thread-safe with restore)
        env_var, original_val = set_provider_key(model_name, api_key)

        try:
            model = ChatLiteLLM(
                model=model_name,
                api_base=api_base,
                temperature=0,
                streaming=True,
            )
            sql_tools = state.sql_toolkit.get_tools()
            all_tools = sql_tools + [ChartGeneratorTool()]
            tools = [convert_to_openai_function(t) for t in all_tools]
            model = cast(ChatLiteLLM, model.bind_tools(tools))

            try:
                response = model.invoke(state.messages)
            except litellm.exceptions.RateLimitError:
                raise UserFacingError("LLM API rate limit exceeded. Please wait a moment and try again.")
            except litellm.exceptions.AuthenticationError:
                raise UserFacingError("LLM API key rejected. Please check your API key in Settings.")
            except litellm.exceptions.BadRequestError as e:
                raise UserFacingError(f"LLM request error: {str(e)}")
            except Exception as e:
                raise UserFacingError(str(e))
        finally:
            restore_provider_key(env_var, original_val)

        return state_update(messages=[response])


class CallToolNode(Node):
    __name__ = "perform_action"

    @classmethod
    def run(cls, state: QueryGraphState) -> QueryGraphStateUpdate:
        messages = state.messages
        last_message = cast(AIMessage, messages[-1])

        output_messages: list[BaseMessage] = []
        results: list[QueryResultSchema] = []

        if len(last_message.tool_calls) == 1 and last_message.tool_calls[0]["name"] == "multi_tool_use.parallel":
            last_message.tool_calls = cls.fix_openai_multi_tool_use_bug(last_message.tool_calls[0])

        for tool_call in last_message.tool_calls:
            tool = state.tool_executor.tool_map[tool_call["name"]]
            if isinstance(tool, StateUpdaterTool):
                updates = tool.get_response(state, tool_call["args"], str(tool_call["id"]))
                output_messages.extend(updates["messages"])
                results.extend(updates["results"])
            else:
                response = tool.run(tool_call["args"])
                tool_message = ToolMessage(
                    content=str(response), name=tool_call["name"], tool_call_id=str(tool_call["id"])
                )
                output_messages.append(tool_message)

        return state_update(messages=output_messages, results=results)

    @staticmethod
    def fix_openai_multi_tool_use_bug(buggy_tool_call: ToolCall) -> list[ToolCall]:
        tool_uses = buggy_tool_call["args"]["tool_uses"]
        return [
            ToolCall(
                name=tool_use["recipient_name"].split(".")[-1],
                args=tool_use["parameters"],
                id=f"call_{i}",
                type="tool_call",
            )
            for i, tool_use in enumerate(tool_uses)
        ]


class ShouldCallToolCondition(Condition):
    @classmethod
    def run(cls, state: QueryGraphState) -> NodeName:
        messages = state.messages
        last_message = messages[-1]
        if "tool_calls" not in last_message.additional_kwargs:
            return END
        else:
            return CallToolNode.__name__
