
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import query_cache


def main():

    # Use a temporary database so existing project logs are untouched.
    with tempfile.TemporaryDirectory() as temp_dir:

        query_cache.CACHE_DB = Path(temp_dir) / "test_cache.duckdb"

        question = "How many delivered orders?"
        model = "gemini-2.5-flash"
        sql = "SELECT COUNT(*) FROM fact_orders"

        # Test 1: Cache miss
        result = query_cache.get_cached_sql(question, model)

        assert result is None
        print("PASS: Cache miss for a new question.")

        # Test 2: Save SQL
        query_cache.save_cached_sql(question, model, sql)

        # Test 3: Cache hit
        result = query_cache.get_cached_sql(question, model)

        assert result == sql
        print("PASS: Previously generated SQL retrieved.")

        # Test 4: Normalization
        result = query_cache.get_cached_sql(
            "  HOW MANY DELIVERED ORDERS?  ",
            model
        )

        assert result == sql
        print("PASS: Case and whitespace normalization works.")

        # Test 5: Different model
        result = query_cache.get_cached_sql(
            question,
            "gemini-3.5-flash-lite"
        )

        assert result is None
        print("PASS: Different models use separate cache entries.")

    print("\nAll query cache tests passed.")


if __name__ == "__main__":
    main()
