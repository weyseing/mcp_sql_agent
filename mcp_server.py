import sys
import logging
import sqlite3
from loguru import logger
from mcp.server.fastmcp import FastMCP

# logging
logging.basicConfig(
    stream=sys.stderr,
    format="\033[94m%(asctime)s\033[0m - \033[92m%(levelname)s\033[0m - \033[93m%(filename)s:%(lineno)d\033[0m: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

mcp = FastMCP("MCP Server")

@mcp.tool()
def query_data(sql: str) -> str:
    """
    Execute SQL queries safely on a SQLite database.

    This function connects to the SQLite database located at './database.db',
    executes the provided SQL query, and returns the results as a string.
    If an error occurs during execution, it returns an error message.

    **Important**: When referencing table names in the SQL query, enclose them
    in backticks (``) to handle reserved keywords or special characters properly.
    For example, use `` `transaction` `` instead of `transaction`.

    Args:
        sql (str): The SQL query to execute.

    Returns:
        str: The query results as a string, with each row separated by a newline,
             or an error message if the query fails.
    """
    logging.info(f"Executing SQL query: {sql}")
    conn = sqlite3.connect("./database.db")
    try:
        result = conn.execute(sql).fetchall()
        conn.commit()
        return "\n".join(str(row) for row in result)
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        conn.close()

@mcp.prompt()
def example_prompt(code: str) -> str:
    return f"Please review this code:\n\n{code}"

if __name__ == "__main__":
    print("Starting server...")
    mcp.run(transport="stdio")