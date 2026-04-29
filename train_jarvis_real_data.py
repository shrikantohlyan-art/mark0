#!/usr/bin/env python3
"""Seed Jarvis with web-search and intent training examples."""

import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

try:
    from Core.god_mode import SelfLearningEngine
    from Core.learning_loop import get_learning_loop
    from Core.learning_report import get_learning_report
except Exception as exc:
    raise SystemExit(f"Failed to import Jarvis modules: {exc}")

TRAINING_SEED_MARKER = "__seeded_web_intent_examples__"


def generate_training_examples() -> list[dict]:
    timestamp = datetime.now(timezone.utc).isoformat()
    examples = [
        {
            "prompt": "Search online for the latest Android phone prices in India.",
            "intent": "search",
            "tool": "web_search",
            "notes": "Web surfing for current product prices.",
        },
        {
            "prompt": "Compare iPhone 15 and Samsung Galaxy S24 for features, battery life, and price.",
            "intent": "compare",
            "tool": "web_search",
            "notes": "Data collection and comparison across web sources.",
        },
        {
            "prompt": "Find the best 5 hotels near Bangalore railway station.",
            "intent": "local_info",
            "tool": "web_search",
            "notes": "Directory-style search and local business discovery.",
        },
        {
            "prompt": "Summarize the latest news about AI regulation in Europe.",
            "intent": "summarize",
            "tool": "web_search",
            "notes": "Collection of news and summary generation.",
        },
        {
            "prompt": "mujhe nearby restaurant dhundo jo budget-friendly ho.",
            "intent": "search",
            "tool": "web_search",
            "notes": "Hinglish intent with local search and data extraction.",
        },
        {
            "prompt": "batado top 3 online business ideas for small shops.",
            "intent": "research",
            "tool": "web_search",
            "notes": "Collect business idea resources and summaries.",
        },
        {
            "prompt": "kya mujhe best wifi plans milenge in Delhi?",
            "intent": "search",
            "tool": "web_search",
            "notes": "Find local service plans and compare offers.",
        },
        {
            "prompt": "Find reviews for Samsung washing machines.",
            "intent": "review",
            "tool": "web_search",
            "notes": "Product research and source aggregation.",
        },
        {
            "prompt": "List top 10 Netflix shows streaming right now.",
            "intent": "list",
            "tool": "web_search",
            "notes": "Collect current entertainment recommendations.",
        },
        {
            "prompt": "Collect sources for organic snack market research.",
            "intent": "collect",
            "tool": "web_search",
            "notes": "Data collection for market analysis.",
        },
        {
            "prompt": "Compare Tesla and Lucid in terms of range, price, and charging.",
            "intent": "compare",
            "tool": "web_search",
            "notes": "Automated comparative research.",
        },
        {
            "prompt": "Summarize the GitHub readme for a fine-tuning data preparation tool.",
            "intent": "summarize",
            "tool": "web_search",
            "notes": "Summarize repository documentation.",
        },
        {
            "prompt": "kahan milta hai ac repair service ka best address?",
            "intent": "local_info",
            "tool": "web_search",
            "notes": "Hinglish local search for service providers.",
        },
        {
            "prompt": "Search for the cheapest flight tickets from Mumbai to Delhi.",
            "intent": "search",
            "tool": "web_search",
            "notes": "Travel price comparison and web surfing.",
        },
        {
            "prompt": "What are the latest AI product launches this week?",
            "intent": "news",
            "tool": "web_search",
            "notes": "Collect and summarize current technology news.",
        },
        {
            "prompt": "kya iss website ke baare mein kuch reviews mil sakte hain?",
            "intent": "review",
            "tool": "web_search",
            "notes": "Hinglish prompt for reputation and review data.",
        },
        {
            "prompt": "Find the contact number and address for a nearby pharmacy.",
            "intent": "local_info",
            "tool": "web_search",
            "notes": "Extract contact details from web sources.",
        },
        {
            "prompt": "Search for top-rated online course platforms for Python.",
            "intent": "search",
            "tool": "web_search",
            "notes": "Web research for learning resources.",
        },
        {
            "prompt": "Compare the best home loan interest rates available today.",
            "intent": "compare",
            "tool": "web_search",
            "notes": "Financial comparison using current online data.",
        },
        {
            "prompt": "Collect sources to build a shopping list for healthy snacks.",
            "intent": "collect",
            "tool": "web_search",
            "notes": "Aggregate product information and nutrition details.",
        },
        {
            "prompt": "Search for a tutorial on creating a local website scraper.",
            "intent": "search",
            "tool": "web_search",
            "notes": "Research coding and scraping tutorials.",
        },
        {
            "prompt": "mujhe batao top online stock analysis tools kaun se hain.",
            "intent": "search",
            "tool": "web_search",
            "notes": "Hinglish search for investment tools.",
        },
        {
            "prompt": "Find the best restaurant menu options near my area.",
            "intent": "local_info",
            "tool": "web_search",
            "notes": "Local restaurant discovery and data collection.",
        },
        {
            "prompt": "Summarize the key differences between Python 3.11 and 3.12.",
            "intent": "summarize",
            "tool": "web_search",
            "notes": "Summarize technical release differences.",
        },
        {
            "prompt": "Compare Android and iOS features for a mobile developer.",
            "intent": "compare",
            "tool": "web_search",
            "notes": "Collect comparative analysis for platform selection.",
        },
        {
            "prompt": "Collect sources for the best study apps for students.",
            "intent": "collect",
            "tool": "web_search",
            "notes": "Gather educational app recommendations.",
        },
        {
            "prompt": "Find news articles about electric vehicle subsidies in India.",
            "intent": "news",
            "tool": "web_search",
            "notes": "Collect policy news and source citations.",
        },
        {
            "prompt": "kya mujhe latest phone deals mil sakte hain?",
            "intent": "search",
            "tool": "web_search",
            "notes": "Hinglish prompt for current deals and offers.",
        },
        {
            "prompt": "Search for GitHub examples of data collection scripts.",
            "intent": "search",
            "tool": "web_search",
            "notes": "Code research and example gathering.",
        },
        {
            "prompt": "List the best review sources for budget laptops.",
            "intent": "review",
            "tool": "web_search",
            "notes": "Research and consolidate review sources.",
        },
        {
            "prompt": "Compare coffee machine models under 15000.",
            "intent": "compare",
            "tool": "web_search",
            "notes": "Shopping comparison and feature extraction.",
        },
        {
            "prompt": "Search for the top ways to improve website SEO.",
            "intent": "search",
            "tool": "web_search",
            "notes": "Research and summarize SEO best practices.",
        },
        {
            "prompt": "Collect citation sources for a presentation on renewable energy.",
            "intent": "collect",
            "tool": "web_search",
            "notes": "Academic-style source gathering.",
        },
        {
            "prompt": "Find a list of nearby laptop repair shops with ratings.",
            "intent": "local_info",
            "tool": "web_search",
            "notes": "Local business search with review signals.",
        },
        {
            "prompt": "Summarize the advantages of using local-first AI tools.",
            "intent": "summarize",
            "tool": "web_search",
            "notes": "Collect and summarize web content about local AI.",
        },
        {
            "prompt": "Compare energy-efficient refrigerator brands available now.",
            "intent": "compare",
            "tool": "web_search",
            "notes": "Product comparison and energy savings research.",
        },
        {
            "prompt": "Search for Hindi tutorials on small business marketing.",
            "intent": "search",
            "tool": "web_search",
            "notes": "Hinglish learning resource search.",
        },
        {
            "prompt": "Collect sources for healthy meal prep ideas.",
            "intent": "collect",
            "tool": "web_search",
            "notes": "Gather recipe and nutrition information.",
        },
        {
            "prompt": "Find the latest software updates for Windows 11.",
            "intent": "news",
            "tool": "web_search",
            "notes": "Current update and release note research.",
        },
        {
            "prompt": "List the best online marketplaces for handmade goods.",
            "intent": "list",
            "tool": "web_search",
            "notes": "Collect marketplace comparison data.",
        },
    ]
    return examples


def seed_training_data():
    engine = SelfLearningEngine()
    examples = generate_training_examples()
    print(f"Seeding {len(examples)} training examples into Brain_Logs/training_data.jsonl...")
    result = engine.train(examples)
    print("Training result:", result)

    learning_loop = get_learning_loop()
    try:
        insight = learning_loop._analyze_recent_patterns()
        print("Updated learning insights:", insight)
    except Exception as exc:
        print("Could not refresh learning insights:", exc)

    report = get_learning_report("Brain_Logs")
    daily_report = report.generate_daily_report()
    print("Daily report summary:\n", daily_report.get("summary", "<none>"))
    print("Report file written to Brain_Logs/reports")


if __name__ == "__main__":
    seed_training_data()
