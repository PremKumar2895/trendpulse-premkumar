"""Create TrendPulse charts and a combined dashboard from analysed CSV data."""

from pathlib import Path

import matplotlib

# Use a non-interactive backend so the script also works without a GUI window.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


INPUT_PATH = Path("data/trends_analysed.csv")
OUTPUT_DIRECTORY = Path("outputs")


def shorten_title(title):
    """Keep long story titles readable on the horizontal bar chart."""
    return title if len(title) <= 50 else f"{title[:47]}..."


def popular_mask(dataframe):
    """Return a Boolean popularity series, including safely read CSV values."""
    return dataframe["is_popular"].astype(str).str.lower().eq("true")


def draw_top_stories(axis, dataframe):
    """Draw the top-ten score chart on the supplied Matplotlib axis."""
    top_stories = dataframe.nlargest(10, "score").sort_values("score")
    labels = top_stories["title"].map(shorten_title)
    axis.barh(labels, top_stories["score"], color="#4C78A8")
    axis.set_title("Top 10 Stories by Score")
    axis.set_xlabel("Score")
    axis.set_ylabel("Story title")


def draw_categories(axis, dataframe):
    """Draw a separate-colour bar chart of story totals by category."""
    category_counts = dataframe["category"].value_counts().sort_index()
    colours = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#B279A2"]
    axis.bar(category_counts.index, category_counts.values, color=colours[: len(category_counts)])
    axis.set_title("Stories per Category")
    axis.set_xlabel("Category")
    axis.set_ylabel("Number of stories")
    axis.tick_params(axis="x", rotation=30)


def draw_scatter(axis, dataframe):
    """Draw scores versus comments, using colour and labels for popularity."""
    popular = popular_mask(dataframe)
    axis.scatter(
        dataframe.loc[~popular, "score"],
        dataframe.loc[~popular, "num_comments"],
        color="#8C8C8C",
        alpha=0.75,
        label="Not popular",
    )
    axis.scatter(
        dataframe.loc[popular, "score"],
        dataframe.loc[popular, "num_comments"],
        color="#E45756",
        alpha=0.85,
        label="Popular",
    )
    axis.set_title("Score vs Comments")
    axis.set_xlabel("Score")
    axis.set_ylabel("Number of comments")
    axis.legend()


def save_individual_charts(dataframe):
    """Create and save each required chart before any possible display call."""
    figure, axis = plt.subplots(figsize=(12, 7))
    draw_top_stories(axis, dataframe)
    figure.tight_layout()
    plt.savefig(OUTPUT_DIRECTORY / "chart1_top_stories.png", dpi=150, bbox_inches="tight")
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(10, 6))
    draw_categories(axis, dataframe)
    figure.tight_layout()
    plt.savefig(OUTPUT_DIRECTORY / "chart2_categories.png", dpi=150, bbox_inches="tight")
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(10, 6))
    draw_scatter(axis, dataframe)
    figure.tight_layout()
    plt.savefig(OUTPUT_DIRECTORY / "chart3_scatter.png", dpi=150, bbox_inches="tight")
    plt.close(figure)


def save_dashboard(dataframe):
    """Combine the three charts into the requested TrendPulse dashboard."""
    figure, axes = plt.subplots(1, 3, figsize=(22, 8))
    draw_top_stories(axes[0], dataframe)
    draw_categories(axes[1], dataframe)
    draw_scatter(axes[2], dataframe)
    figure.suptitle("TrendPulse Dashboard", fontsize=18, fontweight="bold")
    figure.tight_layout(rect=(0, 0, 1, 0.94))
    plt.savefig(OUTPUT_DIRECTORY / "dashboard.png", dpi=150, bbox_inches="tight")
    plt.close(figure)


def main():
    """Load analysed data and create all required PNG visualisations."""
    try:
        trends = pd.read_csv(INPUT_PATH)
    except (FileNotFoundError, pd.errors.EmptyDataError, OSError) as error:
        print(f"Could not load {INPUT_PATH}: {error}")
        return

    required_columns = {"title", "category", "score", "num_comments", "is_popular"}
    missing_columns = required_columns.difference(trends.columns)
    if missing_columns:
        print("Cannot create charts. Missing columns: " + ", ".join(sorted(missing_columns)))
        return
    if trends.empty:
        print("The analysed CSV has no stories to visualise.")
        return

    OUTPUT_DIRECTORY.mkdir(exist_ok=True)
    save_individual_charts(trends)
    save_dashboard(trends)
    print("Saved chart1_top_stories.png, chart2_categories.png, chart3_scatter.png, and dashboard.png to outputs/")


if __name__ == "__main__":
    main()
