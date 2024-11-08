import sqlite3
import os
import glob
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)


def create_db_from_csv(path_to_csv_dir, db_filename, db_type="sqlite"):
        if db_type.lower() != "sqlite":
        raise ValueError(f"Database type {db_type} is not supported yet.")

    csv_files = glob.glob(os.path.join(path_to_csv_dir, "*.csv"))

    with sqlite3.connect(db_filename) as conn:
        for csv_file in csv_files:
            table_name = os.path.basename(csv_file).split(".")[0]
            logging.info(f"Creating Table {table_name}")
            try:
                df = pd.read_csv(csv_file)
                df.to_sql(name=table_name, con=conn, if_exists="replace", index=False)
            except Exception as e:
                logging.error(f"Error Processing File {csv_file}: {e}")


if __name__ == "__main__":
    path_to_csv_dir = "/Users/melvin/data/synthea_sample_data_csv_apr2020/csv"
    db_filename = "patient_health_data.db"

    create_db_from_csv(path_to_csv_dir, db_filename)
