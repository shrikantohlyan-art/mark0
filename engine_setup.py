"""
Engine setup: registers tools and exposes a single `run_jarvis(query)` entrypoint.
Includes a simple CLI when invoked directly.
"""

from autonomous_engine import AutonomousEngine, ToolRegistry, Tool
from tools_impl import search_tool, crawl_tool, analyze_tool, summarize_tool, direct_tool
import logging

logger = logging.getLogger("engine_setup")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)

registry = ToolRegistry()
registry.register(Tool("search", search_tool, max_retries=1))
registry.register(Tool("crawl", crawl_tool, max_retries=1))
registry.register(Tool("analyze", analyze_tool, max_retries=0))
registry.register(Tool("summarize", summarize_tool, max_retries=0))
registry.register(Tool("direct", direct_tool, max_retries=0))

engine = AutonomousEngine(registry)


def run_jarvis(query: str):
    return engine.run(query)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="+", help="Query to run")
    args = parser.parse_args()
    q = " ".join(args.query)
    out = run_jarvis(q)
    import json
    print(json.dumps(out, ensure_ascii=False, indent=2))
