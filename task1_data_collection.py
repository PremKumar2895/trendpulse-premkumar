"""Collect currently trending Hacker News stories for the TrendPulse pipeline.

The script downloads the first 500 Hacker News top-story IDs, fetches their
details, labels title matches into the required TrendPulse categories, and
writes the result to a dated JSON file in ``data/``.
"""

import json
import time
from datetime import datetime
from pathlib import Path

import requests


TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
HEADERS = {"User-Agent": "TrendPulse/1.0"}
MAX_STORIES_PER_CATEGORY = 25

CATEGORY_KEYWORDS = {
    "technology": ["AI", "software", "tech", "code", "computer", "data", "cloud", "API", "GPU", "LLM"],
    "worldnews": ["war", "government", "country", "president", "election", "climate", "attack", "global"],
    "sports": ["NFL", "NBA", "FIFA", "sport", "game", "team", "player", "league", "championship"],
    "science": ["research", "study", "space", "physics", "biology", "discovery", "NASA", "genome"],
    "entertainment": ["movie", "film", "music", "Netflix", "game", "book", "show", "award", "streaming"],
}


def get_json(url: str):
    """Fetch JSON without stopping the whole collection if one request fails."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        print(f"Request failed for {url}: {error}")
    except ValueError as error:
        print(f"Invalid JSON returned by {url}: {error}")
    return None


def title_matches_category(title: str, keywords):
    """Check a title for any category keyword, ignoring case."""
    normalised_title = title.casefold()
    return any(keyword.casefold() in normalised_title for keyword in keywords)


def collect_trends():
    """Fetch, classify, and return up to 25 stories for each category."""
    top_story_ids = get_json(TOP_STORIES_URL)
    if not isinstance(top_story_ids, list):
        print("Could not retrieve the top-story ID list; saving an empty result.")
        return []

    # Fetch each of the first 500 story records once. Items that fail are
    # skipped, allowing a temporary API error to affect only that story.
    stories = []
    for story_id in top_story_ids[:500]:
        story = get_json(ITEM_URL.format(story_id=story_id))
        if isinstance(story, dict):
            stories.append(story)

    collected_at = datetime.now().astimezone().isoformat(timespec="seconds")
    collected = []

    # Process one category at a time so every category has an independent cap.
    # A title can be stored in more than one category when it contains keywords
    # from more than one list (for example, "NASA movie").
    # Sleeping once per loop (rather than per story request) follows the task
    # requirement while avoiding an unnecessary delay for every API call.
    for index, (category, keywords) in enumerate(CATEGORY_KEYWORDS.items()):
        if index > 0:
            time.sleep(2)

        category_count = 0
        for story in stories:
            title = story.get("title")
            if not isinstance(title, str) or not title_matches_category(title, keywords):
                continue

            collected.append(
                {
                    "post_id": story.get("id"),
                    "title": title,
                    "category": category,
                    "score": story.get("score", 0),
                    "num_comments": story.get("descendants", 0),
                    "author": story.get("by", "unknown"),
                    "collected_at": collected_at,
                }
            )
            category_count += 1
            if category_count == MAX_STORIES_PER_CATEGORY:
                break

    return collected


def save_trends(stories):
    """Create the output folder and save the collected records as JSON."""
    data_directory = Path("data")
    data_directory.mkdir(exist_ok=True)
    output_path = data_directory / f"trends_{datetime.now():%Y%m%d}.json"

    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(stories, output_file, indent=2, ensure_ascii=False)

    print(f"Collected {len(stories)} stories. Saved to {output_path}")


if __name__ == "__main__":
    trend_stories = collect_trends()
    save_trends(trend_stories)
