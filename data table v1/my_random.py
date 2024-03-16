from sqlalchemy import create_engine
import pandas as pd

# Create engine
engine = create_engine(
    "mysql+mysqlconnector://root:Hallo123@localhost/nc_coffee", echo=True
)

# Query to get table sizes
query = """
SELECT 
    table_schema || '.' || table_name AS table_name,
    pg_size_pretty(pg_total_relation_size(quote_ident(table_schema) || '.' || quote_ident(table_name))) AS total_size
FROM 
    information_schema.tables
WHERE 
    table_schema = 'public';  -- or specify the schema where your tables reside
"""

# Execute query and load results into a DataFrame
df = pd.read_sql_query(query, engine)

# Display the DataFrame
print(df)
