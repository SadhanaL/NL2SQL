from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import re
from pathlib import Path
from models.llm import get_llm

# Initialize DB and LLMs
db = SQLDatabase.from_uri("sqlite:///sales.db")
llm = get_llm()

# Load prompts
ROOT = Path(__file__).resolve().parent
system_message = (ROOT / "prompts/sql_system.md").read_text(encoding="utf-8")
user_prompt = (ROOT / "prompts/sql_user.md").read_text(encoding="utf-8")

# Parser that expects/parse JSON from the model
parser = JsonOutputParser()

query_prompt_template = ChatPromptTemplate(
    [("system", system_message), ("system", "{format_instructions}"), ("user", user_prompt)]
)

def write_query(question: str) -> dict:
    """
    Generate a syntactically valid SQL query for the given business question using an LLM.

    Parameters
    ----------
    question : str
        The business question to translate into an SQL query.

    Returns
    -------
    dict
        Dictionary containing the generated SQL query with key 'SQL'.
    """
    try:
        vague_terms = ["best", "top", "most", "highest", "biggest", "popular", "trending", "leading"]
        text = question.lower()

        # Basic vague term detection
        contains_vague = any(term in text for term in vague_terms)

        # Check for "by <metric>" clarification (e.g. "by revenue", "by total spend")
        has_by_clause = bool(re.search(r"\bby\s+\w+", text))

        # Check for numeric qualifier after 'top' or 'best' (e.g. "top 5")
        has_numeric_limit = bool(re.search(r"\b(?:top|best)\s+\d+", text))

        # Flag as vague only if no clarifying metric and no numeric limit
        if contains_vague and not (has_by_clause or has_numeric_limit):
            return {
                "error": True,
                "message": (
                    "Your question includes a vague term like 'best', 'top', or 'most'. "
                    "Could you clarify what metric defines 'best'? For example, highest revenue or most units sold?"
                ),
            }

        chain = query_prompt_template | llm | parser

        """Generate SQL query to fetch information."""
        result = chain.invoke(
            {
                "dialect": db.dialect,
                "top_k": 10,
                "table_info": db.get_table_info(),
                "input": question,
                "format_instructions": parser.get_format_instructions(),
            }
        )

        # Handle empty or incomplete SQL
        if not result["SQL"] or len(result["SQL"].split()) < 3:
            return {
                "error": True,
                "message": (
                    "Your question seems a bit unclear. "
                    "Could you please specify what metric or time period you’re interested in?"
                ),
            }

        return result
    except Exception as e:
        return {
            "error": True,
            "message": (
                f"Unable to generate a valid SQL query due to: {str(e)}. "
                "Please rephrase your question or provide more details."
            ),
        }

def execute_query(sql: str) -> dict:
    """
    Execute the provided SQL query against the connected SQLite database.

    Parameters
    ----------
    sql : str
        The SQL query string to execute.

    Returns
    -------
    dict
        Dictionary containing the query result with key 'result', or error information if execution fails.
    """
    try:
        result = db.run(sql)
        return {"result": result}
    except Exception as e:
        return {
            "error": True,
            "message": (
                f"Query execution failed: {str(e)}. "
                "Please check if your question references valid columns or tables."
            ),
        }


