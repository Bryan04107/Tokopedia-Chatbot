import pandas as pd
import sqlite3

conn = sqlite3.connect('database.db')
query = "SELECT * FROM items"
df = pd.read_sql_query(query, conn)
conn.close()

print(df.head())

df['features'] = (
    df['query'] + " " + df['name'] + " " + df['price'] + " " + df['discount_percent'] + " " + df['discount_price'] + " " + 
    df['rating'] + " " + df['sold'] + " " + df['seller'] + " " + df['location'] + " " + df['badge'] + " " + df['link']
)

print("\nCombine:")
print(df['features'][50:55])
