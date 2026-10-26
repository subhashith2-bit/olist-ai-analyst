import duckdb
import pathlib

RAW = pathlib.Path("data/raw")

con = duckdb.connect("olist.duckdb")

for f in sorted(RAW.glob("*.csv")):
    name = f.stem.replace("olist_", "").replace("_dataset", "")

    con.execute(
        f"""
        CREATE OR REPLACE TABLE raw_{name} AS
        SELECT *
        FROM read_csv_auto('{f.as_posix()}')
        """
    )

    n = con.execute(
        f"SELECT COUNT(*) FROM raw_{name}"
    ).fetchone()[0]

    print(f"raw_{name}: {n:,} rows")