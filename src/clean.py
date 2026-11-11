import duckdb

con = duckdb.connect("olist.duckdb")

con.sql("""
    CREATE OR REPLACE TABLE clean_orders AS
    SELECT *
    FROM raw_orders
""")

print("clean_orders created")

con.sql("""
    CREATE OR REPLACE TABLE clean_order_payments AS
    SELECT *
    FROM raw_order_payments
    WHERE NOT (
        payment_value = 0
        AND payment_type = 'not_defined'
    )
""")

print("clean_order_payments created")

con.sql("""
    CREATE OR REPLACE TABLE clean_products AS
    SELECT
        * EXCLUDE (product_category_name),
        COALESCE(product_category_name, 'unknown') AS product_category_name
    FROM raw_products
""")

print("clean_products created")

con.sql("""
    CREATE OR REPLACE TABLE clean_customers AS
    SELECT *
    FROM raw_customers
""")

print("clean_customers created")

con.sql("""
    CREATE OR REPLACE TABLE clean_order_items AS
    SELECT *
    FROM raw_order_items
""")

print("clean_order_items created")

con.sql("""
    CREATE OR REPLACE TABLE clean_order_reviews AS
    SELECT *
    FROM raw_order_reviews
""")

print("clean_order_reviews created")

con.sql("""
    CREATE OR REPLACE TABLE clean_sellers AS
    SELECT *
    FROM raw_sellers
""")

print("clean_sellers created")

con.sql("""
    CREATE OR REPLACE TABLE clean_geolocation AS
    SELECT *
    FROM raw_geolocation
""")

print("clean_geolocation created")

con.sql("""
    CREATE OR REPLACE TABLE clean_product_category_name_translation AS
    SELECT *
    FROM raw_product_category_name_translation
""")

print("clean_product_category_name_translation created")

tables = [
    "clean_orders",
    "clean_order_items",
    "clean_order_payments",
    "clean_customers",
    "clean_products",
    "clean_sellers",
    "clean_order_reviews",
    "clean_geolocation",
    "clean_product_category_name_translation"
]

print("\nCleaning complete:\n")

for table in tables:
    count = con.sql(f"""
        SELECT COUNT(*)
        FROM {table}
    """).fetchall()[0][0]

    print(f"{table}: {count:,} rows")

# Close connection only after all tables are processed
con.close()