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

def is_ambiguous(question: str) -> bool:
    """
    Determine if a natural language question is ambiguous for SQL generation.

    This function checks if the input question is too vague or lacks sufficient detail
    to generate a precise SQL query. It flags questions as ambiguous if they are too short,
    contain superlative or ranking terms (e.g., "best", "top", "most"), and do not include
    clarifying details such as a metric, numeric limit, grouping clause, or time context.

    Parameters
    ----------
    question : str
        The user's natural language question about the data.

    Returns
    -------
    bool
        True if the question is ambiguous and needs clarification, False otherwise.
    """
    text = question.lower()

    min_word_count = 4
    if len(text.split()) < min_word_count:
        return True

    # Only ranking/superlative words can be ambiguous.
    vague_terms = ("best","top","most","highest","lowest","biggest","popular","trending","leading","fastest")
    contains_vague = any(re.search(rf"\b{t}\b", text) for t in vague_terms)

    # If there's no superlative/ranking word, it's not ambiguous (filter queries pass).
    if not contains_vague:
        return False

    # For superlative/ranking queries, allow if any clarifier exists.
    has_by_clause      = bool(re.search(r"\bby\s+[\w\- ]{2,}", text))                 # e.g., "by total spend"
    has_numeric_limit  = bool(re.search(r"\b(?:top|best|bottom|highest|lowest|fastest)\s+\d+\b", text))
    has_metric_term    = any(m in text for m in (
        "revenue","sales","profit","spend","order value","aov","margin","gmv",
        "units","quantity","orders","growth","grew","increase","decrease",
        "rate","avg","average","mean"
    ))
    has_time_context   = bool(re.search(
        r"""\b(20\d{2})\b
            | \bq[1-4]\s*20\d{2}\b
            | \b(last|past|this)\s+(year|quarter|month|week|day|\d+\s+(days|weeks|months|years))\b
            | \bmonth[-\s]?over[-\s]?month\b
        """, text, re.IGNORECASE | re.VERBOSE))

    # Ambiguous only if NONE of the clarifiers are present.
    has_clarity = has_metric_term or has_by_clause or has_numeric_limit or has_time_context
    return not has_clarity

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


