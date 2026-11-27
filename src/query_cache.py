
import duckdb
import hashlib
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CACHE_DB = PROJECT_ROOT / "llm_runs.duckdb"
SCHEMA_FILE = PROJECT_ROOT / "docs" / "schema_for_llm.md"

PROMPT_VERSION = "v1"


def normalize_question(question):
    return re.sub(r"\s+", " ", question.strip().lower())


def get_schema_hash():
    schema_content = SCHEMA_FILE.read_bytes()
    return hashlib.sha256(schema_content).hexdigest()


def make_cache_key(question, model):
    schema_hash = get_schema_hash()

    raw_key = (
        f"{normalize_question(question)}|"
        f"{model}|"
        f"{schema_hash}|"
        f"{PROMPT_VERSION}"
    )

    return hashlib.sha256(raw_key.encode()).hexdigest()


def get_cached_sql(question, model):

    con = duckdb.connect(str(CACHE_DB))

    try:
        con.execute("""
            CREATE TABLE IF NOT EXISTS sql_cache (
                cache_key VARCHAR PRIMARY KEY,
                question VARCHAR,
                model VARCHAR,
                generated_sql VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        key = make_cache_key(question, model)

        result = con.execute("""
            SELECT generated_sql
            FROM sql_cache
            WHERE cache_key = ?
        """, [key]).fetchone()

        return result[0] if result else None

    finally:
        con.close()


def save_cached_sql(question, model, generated_sql):

    con = duckdb.connect(str(CACHE_DB))

    try:
        con.execute("""
            CREATE TABLE IF NOT EXISTS sql_cache (
                cache_key VARCHAR PRIMARY KEY,
                question VARCHAR,
                model VARCHAR,
                generated_sql VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        key = make_cache_key(question, model)

        con.execute("""
            INSERT OR REPLACE INTO sql_cache (
                cache_key,
                question,
                model,
                generated_sql
            )
            VALUES (?, ?, ?, ?)
        """, [key, question, model, generated_sql])

    finally:
        con.close()
