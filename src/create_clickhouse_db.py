import clickhouse_connect
import os
import pandas as pd

# Path to your cricket dataset (CSV)
path_to_cricket_csv = "data/cricket_data.csv"

# Connect to ClickHouse
client = clickhouse_connect.get_client()

# Create cricket table
create_cricket_table = """
CREATE TABLE IF NOT EXISTS cricket_data (
    match_id UInt32,
    inning UInt8,
    batting_team String,
    bowling_team String,
    over UInt8,
    ball UInt8,
    batsman String,
    non_striker String,
    bowler String,
    is_super_over UInt8,
    wide_runs UInt8,
    bye_runs UInt8,
    legbye_runs UInt8,
    noball_runs UInt8,
    penalty_runs UInt8,
    batsman_runs UInt8,
    extra_runs UInt8,
    total_runs UInt8,
    player_dismissed Nullable(String),
    dismissal_kind Nullable(String),
    fielder Nullable(String)
) ENGINE = MergeTree()
ORDER BY (match_id, inning, over, ball)
"""

# Execute table creation
client.command(create_cricket_table)

# Load CSV using pandas
df = pd.read_csv(path_to_cricket_csv)

# Insert into ClickHouse
client.insert_df(
    "cricket_data",
    df,
    column_names=[
        "match_id", "inning", "batting_team", "bowling_team", "over", "ball",
        "batsman", "non_striker", "bowler", "is_super_over", "wide_runs", 
        "bye_runs", "legbye_runs", "noball_runs", "penalty_runs", 
        "batsman_runs", "extra_runs", "total_runs", 
        "player_dismissed", "dismissal_kind", "fielder"
    ]
)

# Verify tables
result = client.query("SHOW TABLES")
print("Tables in DB:")
for table in result.result_rows:
    print(table)

# Sample query: first 5 rows
result = client.query("SELECT * FROM cricket_data LIMIT 5;")
print("Sample rows:")
for row in result.result_rows:
    print(row)
