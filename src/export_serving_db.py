import duckdb
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SOURCE_DB = PROJECT_ROOT / "olist.duckdb"
SERVING_DB = PROJECT_ROOT / "olist_serving.duckdb"

TABLES = [
    "fact_orders",
    "customer_metrics",
    "category_metrics",
    "monthly_kpis"
]


def main():
    print("\n===== EXPORTING SERVING DATABASE =====\n")

    con = duckdb.connect(str(SERVING_DB))

    try:
        source_path = SOURCE_DB.as_posix().replace("'", "''")

        con.execute(
            f"ATTACH '{source_path}' AS source (READ_ONLY)"
        ).fetchall()

        for table in TABLES:
            con.execute(f"""
                CREATE OR REPLACE TABLE {table} AS
                SELECT * FROM source.main.{table}
            """).fetchall()

            row_count = con.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            print(f"{table}: {row_count:,} rows copied")

        con.execute("DETACH source").fetchall()

        print("\nServing database created successfully.")

    finally:
        con.close()


if __name__ == "__main__":
    main()