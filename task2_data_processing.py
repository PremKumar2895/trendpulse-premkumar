"""Clean TrendPulse JSON data and save the result as a CSV file."""

from pathlib import Path

import pandas as pd


DATA_DIRECTORY = Path("data")
OUTPUT_PATH = DATA_DIRECTORY / "trends_clean.csv"


def latest_json_file():
    """Return the newest Task 1 JSON export in the data folder."""
    json_files = list(DATA_DIRECTORY.glob("trends_*.json"))
    if not json_files:
        return None
    return max(json_files, key=lambda file_path: file_path.stat().st_mtime)


def clean_trends(dataframe):
    """Apply the required duplicate, null, type, score, and title cleanup."""
    # Remove records that refer to the same Hacker News story.
    dataframe = dataframe.drop_duplicates(subset="post_id")
    print(f"After removing duplicates: {len(dataframe)}")

    # Convert score before checking nulls so invalid score text is treated as
    # missing. Strip title spaces after required title values are retained.
    dataframe = dataframe.copy()
    dataframe["score"] = pd.to_numeric(dataframe["score"], errors="coerce")
    dataframe = dataframe.dropna(subset=["post_id", "title", "score"])
    dataframe["title"] = dataframe["title"].str.strip()
    print(f"After removing nulls: {len(dataframe)}")

    # Hacker News scores and comment counts are whole numbers. Missing or
    # invalid comment counts mean the story has no recorded comments yet.
    dataframe["score"] = dataframe["score"].astype(int)
    dataframe["num_comments"] = (
        pd.to_numeric(dataframe["num_comments"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    dataframe = dataframe[dataframe["score"] >= 5].copy()
    print(f"After removing low scores: {len(dataframe)}")
    return dataframe


def main():
    """Load the latest raw JSON file, clean it, and write trends_clean.csv."""
    input_path = latest_json_file()
    if input_path is None:
        print("No trends_YYYYMMDD.json file was found in the data folder.")
        return

    try:
        trends = pd.read_json(input_path)
    except (ValueError, OSError) as error:
        print(f"Could not load {input_path}: {error}")
        return

    required_columns = {"post_id", "title", "score", "num_comments", "category"}
    missing_columns = required_columns.difference(trends.columns)
    if missing_columns:
        print("Cannot clean the file. Missing columns: " + ", ".join(sorted(missing_columns)))
        return

    print(f"Loaded {len(trends)} stories from {input_path}")
    cleaned_trends = clean_trends(trends)

    DATA_DIRECTORY.mkdir(exist_ok=True)
    cleaned_trends.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"\nSaved {len(cleaned_trends)} rows to {OUTPUT_PATH}")

    print("\nStories per category:")
    for category, count in cleaned_trends["category"].value_counts().items():
        print(f"  {category:<15} {count}")


if __name__ == "__main__":
    main()
