import argparse

# empty import; seems to fix an internal plotly bug where pandas is not initialized properly
import pandas  # type: ignore

# import cProfile
from crisprmutsim.webapp.app import run as run_webapp
from crisprmutsim.csv_parser import load_csv


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description="CRISPR Mutation Simulation", usage="%(prog)s [folder-path]"
    )
    argparser.add_argument(
        "folder_path",
        type=str,
        nargs="?",
        default=".",
        help="Database folder path (defaults to current directory)",
        metavar="PATH_TO_DB_FOLDER",
    )
    argparser.add_argument(
        "--csv",
        type=str,
        nargs=2,
        metavar=("CSV_FILE", "DB_FILE"),
        help="Load data from CSV file into database (provide CSV file path and DB file path)",
    )

    args = argparser.parse_args()

    if args.csv:
        csv_file_path, db_file_path = args.csv
        load_csv(csv_file_path, db_file_path)
    else:
        run_webapp(args.folder_path)
