import argparse
from app import write_query, execute_query

def main():
    """
    Command-line interface for generating SQL queries and optionally executing them.

    Usage
    -----
    python app.py "Your question here"
        Only generates the SQL query.

    python app.py --execute "Your question here" 
        Generates the SQL query and executes it on the database.
    """
    parser = argparse.ArgumentParser(
        description="Generate and optionally execute SQL queries from natural language."
    )
    parser.add_argument("question", type=str, help="Business question to translate into SQL.")
    parser.add_argument("--execute", action="store_true", help="Execute the generated SQL query.")
    args = parser.parse_args()

    # Prepare state
    state = {"question": args.question, "SQL": "", "result": ""}

    # Generate SQL
    sql_output = write_query(state["question"])
    print("\nGenerated SQL:\n", sql_output)

    # Execute SQL against the database 
    if args.execute:
        result_output = execute_query(sql_output["SQL"])
        print("\nQuery Result:\n", result_output)

if __name__ == "__main__":
    main()