import { useState } from "react";
import { enqueueSnackbar } from "notistack";
import { Button } from "../Catalyst/button";
import { Input } from "../Catalyst/input";
import MaskedInput from "./MaskedInput";
import { useGetLlmConnections, useCreateLlmConnection } from "@/hooks";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { backendApi } from "@/services/api_client";
import { ILlmConnection } from "@/api";

const LLM_CONNECTIONS_QUERY_KEY = ["LLM_CONNECTIONS"];

export default function LlmConnectionManager() {
  const queryClient = useQueryClient();
  const { data: connections = [], isLoading } = useGetLlmConnections();

  const [provider, setProvider] = useState("openai");
  const [model, setModel] = useState("gpt-4o-mini");
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");

  const { mutate: createConnection, isPending: isCreating } = useCreateLlmConnection({
    onSuccess: () => {
      setApiKey("");
      setBaseUrl("");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await backendApi({ url: `/api/llm-connections/${id}`, method: "DELETE" });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: LLM_CONNECTIONS_QUERY_KEY });
      enqueueSnackbar({ variant: "success", message: "Connection deleted" });
    },
    onError: () => enqueueSnackbar({ variant: "error", message: "Failed to delete connection" }),
  });

  const setDefaultMutation = useMutation({
    mutationFn: async (id: string) => {
      return (await backendApi<ILlmConnection>({
        url: `/api/llm-connections/${id}/default`,
        method: "POST",
      })).data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: LLM_CONNECTIONS_QUERY_KEY });
      enqueueSnackbar({ variant: "success", message: "Default connection updated" });
    },
    onError: () => enqueueSnackbar({ variant: "error", message: "Failed to set default" }),
  });

  const handleAdd = () => {
    createConnection({
      provider,
      model,
      api_key: apiKey || undefined,
      base_url: baseUrl || undefined,
      is_default: !connections || connections.length === 0,
    });
  };

  return (
    <div className="grid max-w-7xl grid-cols-1 gap-x-8 gap-y-10 px-4 py-16 sm:px-6 md:grid-cols-3 lg:px-8">
      <div>
        <h2 className="text-base font-semibold leading-7 text-white">LLM Connections</h2>
        <p className="mt-1 text-sm leading-6 text-gray-400">
          Manage your AI models and providers (OpenAI, Anthropic, Gemini, Groq, etc.).
        </p>
      </div>

      <div className="md:col-span-2">
        <div className="bg-white/5 p-4 rounded-lg shadow-sm border border-white/10">
          <h3 className="text-sm font-medium text-white mb-4">Add New Connection</h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 mb-4">
            <div>
              <label className="block text-xs font-medium text-gray-400">Provider (e.g. openai, anthropic, gemini, groq, ollama)</label>
              <Input
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="mt-1 text-sm bg-white/5"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-400">Model Name (e.g. gpt-4o, claude-3-5-sonnet-20240620)</label>
              <Input
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="mt-1 text-sm bg-white/5"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-xs font-medium text-gray-400">API Key</label>
              <MaskedInput
                value={apiKey}
                onChange={setApiKey}
              />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-xs font-medium text-gray-400">Base URL (Optional)</label>
              <Input
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                className="mt-1 text-sm font-mono bg-white/5"
              />
            </div>
          </div>
          <Button color="green" onClick={handleAdd} disabled={isCreating}>
            {isCreating ? "Adding..." : "Add Connection"}
          </Button>
        </div>

        <div className="mt-8">
          <h3 className="text-sm font-medium text-white mb-4">Active Connections</h3>
          {isLoading ? (
            <p className="text-gray-400 text-sm">Loading...</p>
          ) : connections.length === 0 ? (
            <p className="text-gray-400 text-sm">No connections added yet.</p>
          ) : (
            <ul className="divide-y divide-white/10 border border-white/10 rounded-lg overflow-hidden bg-white/5">
              {connections.map((c) => (
                <li key={c.id} className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-white flex items-center gap-2">
                      {c.provider} / {c.model}
                      {c.is_default && (
                        <span className="inline-flex items-center rounded-md bg-green-500/10 px-2 py-1 text-xs font-medium text-green-400 ring-1 ring-inset ring-green-500/20">
                          Default
                        </span>
                      )}
                    </p>
                    {c.base_url && <p className="text-xs text-gray-500 mt-1">{c.base_url}</p>}
                  </div>
                  <div className="flex gap-2">
                    {!c.is_default && (
                      <Button plain onClick={() => setDefaultMutation.mutate(c.id)}>
                        Set Default
                      </Button>
                    )}
                    <Button plain className="text-red-400 hover:text-red-300" onClick={() => deleteMutation.mutate(c.id)}>
                      Delete
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
