"""
AutonomousEngine - a local-first, tool-chaining autonomous execution engine.
Provides: Memory (disk-persisted), Tool, ToolRegistry, Planner, Evaluator,
SelfImprover and AutonomousEngine orchestration loop with retries, chaining,
and learning (persisted logs).
"""

import time
import json
import os
import threading
import logging
import traceback
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

logger = logging.getLogger("autonomous_engine")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

DEFAULT_MEMORY_FILE = Path(__file__).resolve().parent / "memory" / "autonomous_memory.json"


class Memory:
    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else DEFAULT_MEMORY_FILE
        self.lock = threading.RLock()
        self.data: Dict[str, Any] = {"kv": {}, "learning_log": []}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self) -> None:
        with self.lock:
            if self.path.exists():
                try:
                    with open(self.path, "r", encoding="utf-8") as f:
                        self.data = json.load(f)
                except Exception:
                    logger.exception("Failed to load memory file, starting fresh")
                    self.data = {"kv": {}, "learning_log": []}
            else:
                self._save()

    def _save(self) -> None:
        tmp = str(self.path) + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, str(self.path))
        except Exception:
            logger.exception("Failed to save memory")

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            return self.data.get("kv", {}).get(key)

    def set(self, key: str, value: Any) -> None:
        with self.lock:
            self.data.setdefault("kv", {})[key] = value
            self._save()

    def learn(self, query: str, result: Any) -> None:
        with self.lock:
            entry = {"query": query, "result": result, "timestamp": time.time()}
            self.data.setdefault("learning_log", []).append(entry)
            if len(self.data["learning_log"]) > 1000:
                self.data["learning_log"] = self.data["learning_log"][-1000:]
            self._save()


class Tool:
    def __init__(self, name: str, func: Callable[..., Any], timeout: Optional[float] = None, max_retries: int = 2, retry_backoff: float = 1.0):
        self.name = name
        self.func = func
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

    def execute(self, input_data: Any) -> Dict[str, Any]:
        last_exc = None
        for attempt in range(self.max_retries + 1):
            try:
                # Call tool with input payload when appropriate
                result = self.func(input_data) if self._expects_arg() else self.func()
                return self._normalize(result)
            except Exception as exc:
                last_exc = exc
                logger.debug(f"Tool {self.name} attempt {attempt} failed: {exc}")
                time.sleep(self.retry_backoff * (2 ** attempt))
        return {"success": False, "error": f"tool_error: {str(last_exc)}", "trace": traceback.format_exc()}

    def _expects_arg(self) -> bool:
        import inspect
        try:
            sig = inspect.signature(self.func)
            return len(sig.parameters) >= 1
        except Exception:
            return True

    def _normalize(self, out: Any) -> Dict[str, Any]:
        if isinstance(out, dict):
            if "success" not in out:
                out["success"] = True
            return out
        if out is None:
            return {"success": False, "data": None}
        return {"success": True, "data": out}


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._lock = threading.RLock()

    def register(self, tool: Tool) -> None:
        with self._lock:
            self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        with self._lock:
            return self._tools.get(name)

    def all(self) -> List[str]:
        with self._lock:
            return list(self._tools.keys())


class Planner:
    def create_plan(self, query: str) -> List[Dict[str, Any]]:
        q = (query or "").lower()
        plan: List[Dict[str, Any]] = []

        if any(x in q for x in ["compare", " vs ", " best ", " top ", "which is better", "evaluate", "compare"]):
            plan = [
                {"tool": "search", "input": query},
                {"tool": "crawl", "input": query},
                {"tool": "analyze", "input": None},
                {"tool": "summarize", "input": None},
            ]
            return plan

        if any(x in q for x in ["research", "expert", "deep research", "latest", "study"]):
            return [
                {"tool": "search", "input": query},
                {"tool": "crawl", "input": query},
                {"tool": "analyze", "input": None},
                {"tool": "summarize", "input": None},
            ]

        if "github" in q and any(x in q for x in ["open", "go to", "visit"]):
            return [{"tool": "direct", "input": query}]

        # default: attempt a direct execution first
        return [{"tool": "direct", "input": query}]


class Evaluator:
    def score(self, result: Optional[Dict[str, Any]]) -> float:
        if not result or not isinstance(result, dict):
            return 0.0
        if result.get("success") is False:
            return 0.0
        conf = float(result.get("confidence", 0.0) or 0.0)
        if conf:
            return min(0.99, conf)
        data = result.get("data") or ""
        data_str = str(data)
        if "ERROR" in data_str.upper():
            return 0.0
        length_score = min(0.9, len(data_str) / 1000.0)
        source_bonus = 0.2 if result.get("sources") and len(result.get("sources")) > 1 else 0.0
        return min(0.99, length_score + source_bonus)

    def is_strong(self, result: Optional[Dict[str, Any]], threshold: float = 0.6) -> bool:
        return self.score(result) >= threshold


class SelfImprover:
    def refine_query(self, query: str, previous_results: Optional[List[Dict[str, Any]]] = None) -> str:
        suffix = " detailed analysis and latest sources"
        try:
            weak = []
            if previous_results:
                for r in previous_results:
                    res = r.get("result")
                    if not res or res.get("success") is False:
                        weak.append(r.get("step", {}).get("tool"))
            if weak:
                suffix += " focusing on " + ", ".join([str(x) for x in weak if x])
        except Exception:
            pass
        return query + suffix


class AutonomousEngine:
    def __init__(self, registry: ToolRegistry, memory_path: Optional[Path] = None, max_loops: int = 8):
        self.registry = registry
        self.memory = Memory(memory_path)
        self.planner = Planner()
        self.evaluator = Evaluator()
        self.improver = SelfImprover()
        self.max_loops = max_loops

    def run(self, query: str, cancellation_check: Optional[Callable[[], bool]] = None) -> Dict[str, Any]:
        start = time.time()
        if not query:
            return {"success": False, "error": "empty_query"}

        cached = self.memory.get(query)
        if cached is not None:
            logger.info("Memory cache hit")
            return {"success": True, "data": cached, "cached": True}

        current_query = query
        final_result: Optional[Dict[str, Any]] = None
        full_step_results: List[Dict[str, Any]] = []

        for iteration in range(self.max_loops):
            logger.info(f"Iteration {iteration+1}/{self.max_loops} for query: {current_query}")
            plan = self.planner.create_plan(current_query)
            execution_context: Dict[str, Any] = {}
            step_results: List[Dict[str, Any]] = []

            for step in plan:
                if cancellation_check and cancellation_check():
                    logger.info("Cancellation requested, aborting")
                    return {"success": False, "error": "cancelled"}

                tool = self.registry.get(step["tool"])
                if not tool:
                    logger.warning(f"No tool registered for {step['tool']}, skipping")
                    step_results.append({"step": step, "result": {"success": False, "error": "tool_missing"}})
                    continue

                step_input = step.get("input") or current_query
                payload = {"query": step_input, "context": execution_context.copy()}
                logger.debug(f"Executing tool {tool.name} with input: {str(step_input)[:200]}")
                result = tool.execute(payload)
                step_results.append({"step": step, "result": result})

                if result.get("success"):
                    execution_context[f"{tool.name}_output"] = result.get("data")
                    full_step_results.append({"tool": tool.name, "data": result.get("data")})

            # pick best result from step_results
            best = None
            best_score = 0.0
            for r in step_results:
                score = self.evaluator.score(r.get("result"))
                if score > best_score:
                    best_score = score
                    best = r.get("result")

            if best and self.evaluator.is_strong(best):
                logger.info(f"Found strong result with score {best_score}")
                final_result = best
                break

            logger.info(f"No strong result in iteration {iteration+1} (best_score={best_score}); refining query")
            current_query = self.improver.refine_query(current_query, step_results)

        if final_result is None:
            # merge accumulated results into a fallback
            merged = []
            for r in full_step_results:
                d = r.get("data")
                if d:
                    try:
                        merged.append(str(d)[:2000])
                    except Exception:
                        merged.append(repr(d)[:2000])
            final_text = "\n\n".join(merged) or current_query
            final_result = {"success": True, "data": final_text, "confidence": 0.3}

        try:
            # Persist summarized data and learn
            self.memory.set(query, final_result.get("data"))
            self.memory.learn(query, {"result": final_result, "iterations": iteration + 1, "timestamp": time.time()})
        except Exception:
            logger.exception("Failed to persist memory")

        elapsed = time.time() - start
        final_result["meta"] = {"iterations": iteration + 1, "time": elapsed}
        return final_result


__all__ = ["Memory", "Tool", "ToolRegistry", "Planner", "Evaluator", "SelfImprover", "AutonomousEngine"]
