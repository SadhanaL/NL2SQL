# Natural Language to SQL (LangChain + OpenAI + SQLite)

This repo turns plain English business questions into **syntactically correct SQL queries**, execute them on a **SQLite** sales database, and optionally generate **natural-language answers**; all powered by LangChain and OpenAI.


## Features

--> Convert plain-English questions into valid SQLite queries  
--> Execute queries directly on your local database  
--> Get natural-language explanations of query results  
--> Prompts are editable as standalone markdown files  

---

## Requirements

- Python ≥ 3.10  
- SQLite database file (e.g., `sales.db`)  
- [OpenAI API key](https://platform.openai.com/account/api-keys)

---

## Installation

```bash
# 1 Clone the repo
git clone https://github.com/SadhanaL/NL2SQL.git
cd NL2SQL

# 2 Create a virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows

# 3 Install dependencies
pip install -r requirements.txt

# 4 Set your OpenAI API key
setx OPENAI_API_KEY "your-key-here"     # Windows   PowerShell
```

## Example usage

Generate only SQL

```bash
python main.py "List the top 5 customers by total spend in the last year"
```

Generate sql and execute it against the sales db

```bash
python main.py --execute "List the top 5 customers by total spend in the last year" 
```

