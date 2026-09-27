"""Analyse cleaned TrendPulse data with Pandas and NumPy."""

from pathlib import Path

import numpy as np
import pandas as pd


INPUT_PATH = Path("data/trends_clean.csv")
OUTPUT_PATH = Path("data/trends_analysed.csv")


def main():
    """Load the cleaned data, print analysis results, and save new columns."""
    try:
        trends = pd.read_csv(INPUT_PATH)
    except (FileNotFoundError, pd.errors.EmptyDataError, OSError) as error:
        print(f"Could not load {INPUT_PATH}: {error}")
        return

    required_columns = {"title", "category", "score", "num_comments"}
    missing_columns = required_columns.difference(trends.columns)
    if missing_columns:
        print("Cannot analyse the file. Missing columns: " + ", ".join(sorted(missing_columns)))
        return
    if trends.empty:
        print("The cleaned CSV has no stories to analyse.")
        return

    print(f"Loaded data: {trends.shape}")
    print("\nFirst 5 rows:")
    print(trends.head())

    # Pandas calculates overall averages for the two engagement measures.
    average_score = trends["score"].mean()
    average_comments = trends["num_comments"].mean()
    print(f"\nAverage score   : {average_score:,.2f}")
    print(f"Average comments: {average_comments:,.2f}")

    # Convert scores to a NumPy array for the requested statistical analysis.
    scores = trends["score"].to_numpy(dtype=float)
    mean_score = np.mean(scores)
    median_score = np.median(scores)
    standard_deviation = np.std(scores)

    print("\n--- NumPy Stats ---")
    print(f"Mean score   : {mean_score:,.2f}")
    print(f"Median score : {median_score:,.2f}")
    print(f"Std deviation: {standard_deviation:,.2f}")
    print(f"Max score    : {np.max(scores):,.0f}")
    print(f"Min score    : {np.min(scores):,.0f}")

    category_counts = trends["category"].value_counts()
    top_category = category_counts.idxmax()
    print(f"\nMost stories in: {top_category} ({category_counts[top_category]} stories)")

    most_commented_story = trends.loc[trends["num_comments"].idxmax()]
    print(
        "Most commented story: "
        f'"{most_commented_story["title"]}" — '
        f'{most_commented_story["num_comments"]:,} comments'
    )

    # Add the two columns needed by the final TrendPulse visualisation task.
    trends["engagement"] = trends["num_comments"] / (trends["score"] + 1)
    trends["is_popular"] = trends["score"] > average_score

    trends.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"\nSaved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
