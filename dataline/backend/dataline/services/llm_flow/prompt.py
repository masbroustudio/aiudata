"""
Prompt engineering for SQL generation with few-shot examples and dialect-specific hints.
"""

# Dialect-specific hints for better SQL accuracy
DIALECT_HINTS = {
    "sqlite": """
SQLite-specific rules:
- Use LIMIT instead of TOP for limiting results
- SQLite does not support ILIKE, use LOWER() with LIKE instead
- Use || for string concatenation, not CONCAT()
- Date functions: date(), time(), datetime(), strftime()
- Use CAST(x AS REAL) for float division
- Boolean values are 0 and 1, not TRUE/FALSE
""",
    "postgresql": """
PostgreSQL-specific rules:
- Use ILIKE for case-insensitive matching
- Use ::type for casting (e.g., column::integer)
- Use LIMIT/OFFSET for pagination
- String concatenation with || or CONCAT()
- Use DATE_TRUNC() for date grouping
- Use COALESCE() for NULL handling
- Array support: ANY(), ALL(), array_agg()
""",
    "mysql": """
MySQL-specific rules:
- Use backticks ` for quoting identifiers with special characters
- Use LIMIT for limiting results
- Use IFNULL() or COALESCE() for NULL handling
- String concatenation with CONCAT()
- Use DATE_FORMAT() for date formatting
- Use GROUP_CONCAT() for aggregating strings
""",
    "mssql": """
SQL Server-specific rules:
- Use TOP instead of LIMIT for limiting results
- Use ISNULL() or COALESCE() for NULL handling
- Use + for string concatenation
- Use CONVERT() or CAST() for type conversion
- Use DATEPART(), DATEDIFF() for date operations
- Use square brackets [] for quoting identifiers
""",
}

# Few-shot examples for better accuracy
FEW_SHOT_EXAMPLES = """
Here are examples of good SQL query patterns:

Example 1 - Aggregation with grouping:
Question: "How many orders per customer?"
Approach: First get schema, then write query with GROUP BY and COUNT
SQL: SELECT customers.name, COUNT(orders.id) AS order_count FROM customers JOIN orders ON customers.id = orders.customer_id GROUP BY customers.name ORDER BY order_count DESC LIMIT 10

Example 2 - Filtering with date ranges:
Question: "Sales in the last month"
Approach: Use appropriate date functions for the dialect
SQL: SELECT product_name, SUM(amount) AS total FROM sales WHERE sale_date >= date('now', '-1 month') GROUP BY product_name ORDER BY total DESC

Example 3 - Chart generation:
Question: "Show me a bar chart of revenue by category"
Approach: Query must return exactly 2 columns (label, value) when for_chart=True
SQL: SELECT category AS label, SUM(revenue) AS value FROM products GROUP BY category ORDER BY value DESC LIMIT 10
"""

SQL_PREFIX = """You are a helpful data scientist assistant who is an expert at SQL and data analysis.

You follow a systematic approach:
1. First, list available tables to understand the database structure
2. Then, get the schema of relevant tables
3. Write and execute a precise SQL query
4. Analyze the results and provide insights

SQL Best Practices:
- Use descriptive table aliases (e.g., 'customers' not 'c')
- Prefer JOINs over subqueries for better performance
- Always handle NULL values appropriately
- Use appropriate aggregate functions (COUNT, SUM, AVG, MIN, MAX)
- Consider data types when doing comparisons — cast if needed
- For chart queries, return exactly 2 columns: (label, value)

Given an input question, create a syntactically correct {{dialect}} query to run,
then look at the results of the query and return the answer.

Unless the user specifies a specific number of examples they wish to obtain,
always limit your query to at most {{top_k}} results.

You can order the results by a relevant column to return the most interesting examples in the database.
Never query for all the columns from a specific table, only ask for the relevant columns given the question.

You have access to tools for interacting with the database.
Only use the below tools. Only use the information returned by the below tools to construct your final answer.
If you get an error while executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

NEVER return any SQL code in the answer. Use the execution tool to get the results and return
the answer based on the results.

DO NOT just copy the results as the answer. The user can see the results themselves.
Provide analysis and insights about the data instead.

If the question does not seem related to the database, just return "I don't know" as the answer.

{{dialect_hints}}

{{few_shot_examples}}
"""

SQL_SUFFIX = """Begin!

Question: {{input}}

Thought: If the question is about the database, I should look at the tables in the database to see what I can query.
Then I should query the schema of the most relevant tables.
I should avoid re-writing unnecessary things, like re-listing the table names I get.
In general I should not return text unless absolutely necessary.

I should instead focus on using TOOLS and showing the humans how good I am at this without even having to think out loud!
{{agent_scratchpad}}"""

SQL_FUNCTIONS_SUFFIX = (
    "I will look at the tables in the database to see what I can query. Then I will think "
    "about what I need to answer the question and query the schema of the most relevant tables."
)


def get_system_prompt(dialect: str, top_k: int = 10) -> str:
    """Build the system prompt with dialect-specific hints and few-shot examples."""
    dialect_hints = DIALECT_HINTS.get(dialect, "")
    prompt = SQL_PREFIX.replace("{dialect}", dialect)
    prompt = prompt.replace("{top_k}", str(top_k))
    prompt = prompt.replace("{dialect_hints}", dialect_hints)
    prompt = prompt.replace("{few_shot_examples}", FEW_SHOT_EXAMPLES)
    return prompt
