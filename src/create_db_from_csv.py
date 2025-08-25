import os
import glob
import pandas as pd
import logging
from sqlalchemy import create_engine

logging.basicConfig(level=logging.INFO)

def create_db_from_csv(path_to_csv_dir, username, password, host, port, dbname):
    # Build dynamic PostgreSQL connection URL
    db_url = f"postgresql://{username}:{password}@{host}:{port}/{dbname}"

    # Create PostgreSQL engine
    engine = create_engine(db_url)

    csv_files = glob.glob(os.path.join(path_to_csv_dir, "*.csv"))

    for csv_file in csv_files:
        table_name = os.path.basename(csv_file).split(".")[0]
        logging.info(f"Creating Table {table_name}")
        try:
            df = pd.read_csv(csv_file)
            df.to_sql(name=table_name, con=engine, if_exists="replace", index=False)
            logging.info(f"Table {table_name} created successfully.")
        except Exception as e:
            logging.error(f"Error Processing File {csv_file}: {e}")

if __name__ == "__main__":
    # Take user inputs for PostgreSQL connection
    username = input("Enter PostgreSQL username: ")
    password = input("Enter PostgreSQL password: ")
    host = input("Enter PostgreSQL host (default: localhost): ") or "localhost"
    port = input("Enter PostgreSQL port (default: 5432): ") or "5432"
    dbname = input("Enter PostgreSQL database name: ")

    # Path to cricket CSV files
    path_to_csv_dir = input("Enter path to cricket CSV folder: ")

    create_db_from_csv(path_to_csv_dir, username, password, host, port, dbname)
