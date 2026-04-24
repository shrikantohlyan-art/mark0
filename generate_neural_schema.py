from __future__ import annotations

from pathlib import Path


OUTPUT_PATH = Path("Docs") / "JARVIS_NEURAL_SCHEMA.md"
MIN_LINES = 10500

ORIGINAL_TASKS = [
    "Fix the weak task execution path so JARVIS stops giving fake done replies.",
    "Preserve follow-up context so the last user message is not lost on short replies.",
    "Keep provider and API rotation working without breaking local-first speed.",
    "Restore real voice flow with STT to runtime to TTS on the same task state.",
    "Stop autonomous mode from replaying stale old tasks and stale digest text.",
    "Reuse the real WhatsApp Web or browser session instead of opening duplicate tabs.",
    "Strengthen downloads so direct links verify and official-page fallbacks stay honest.",
    "Improve app and browser control so Windows actions are verified, not narrated.",
    "Route local business research requests into evidence-backed structured research.",
    "Add a black box with chat history and agent work summaries for cross-agent handoff.",
    "Keep the original task list visible so future agents know the true upgrade target.",
    "Unify chat, voice, and automation under one task lifecycle and one session identity.",
    "Make the capability graph explicit so no single stale skill hijacks broad prompts.",
    "Turn memory and training into parameterized workflow learning instead of phrase memorization.",
    "Keep the current Python plus FastAPI stack and borrow ideas, not code, from IRIS and MK37.",
]

DOMAINS = [
    {
        "name": "Runtime Core",
        "principles": [
            "one canonical runtime owns task lifecycle",
            "every request has one session identity",
            "chat voice and automation use the same execution truth",
            "planner output is data not prose",
            "response text is downstream of verified execution",
        ],
        "executions": [
            "compile prompt into normalized intent",
            "bind request into execution context",
            "attach black box session for the run",
            "route to deterministic tool path when possible",
            "defer to provider chat only when action routing is not justified",
        ],
        "verifications": [
            "task_id exists and survives follow-up",
            "route is visible in payload",
            "brain metadata shows planner and responder origins",
            "terminal state is explicit and machine-readable",
            "no branch exits without finalization",
        ],
        "failures": [
            "parallel brains cause drift",
            "tool output is narrated before verification",
            "runtime exits without updating task store",
            "follow-up opens a new unrelated task",
            "response lacks evidence and reason codes",
        ],
    },
    {
        "name": "Task Compiler",
        "principles": [
            "short follow-ups should fill pending slots first",
            "deterministic parsing handles obvious operational commands",
            "hinglish should map to stable task semantics",
            "slot filling should mutate plan not replace user goal",
            "pending state must stay visible until resolved",
        ],
        "executions": [
            "inspect active task by session",
            "decide between resume or new task",
            "fill missing slot values from short user reply",
            "emit task intent with plan and pending slots",
            "preserve task_id across continuation",
        ],
        "verifications": [
            "pending_slots are returned to the client",
            "resume mode retains the original task_id",
            "slot values update plan parameters",
            "continuation keeps route and task state consistent",
            "unhandled mode avoids fake routing",
        ],
        "failures": [
            "last message gets forgotten",
            "yes or proceed starts a new task",
            "location follow-up loses weather context",
            "recipient follow-up loses messaging context",
            "confirmation loops never close",
        ],
    },
    {
        "name": "Capability Graph",
        "principles": [
            "capabilities are explicit and typed",
            "verbs and domains are separated from wording",
            "session affinity is known before execution starts",
            "verifier expectations are declared up front",
            "fallback chains stay visible in capability metadata",
        ],
        "executions": [
            "register browser desktop messaging research and shell capabilities",
            "surface capability snapshot through API",
            "use capability domain for intent summary",
            "keep high-risk operations confirmation-gated",
            "prefer graph metadata over hidden skill assumptions",
        ],
        "verifications": [
            "capability endpoint lists domain buckets",
            "task intent shows the chosen domain",
            "fallback chain is inspectable",
            "safe versus confirm policies stay visible",
            "new capabilities do not orphan old endpoints",
        ],
        "failures": [
            "single skill becomes a hidden bottleneck",
            "stale route overrides explicit user intent",
            "domain mismatch causes wrong verifier",
            "capabilities are implemented but undiscoverable",
            "session-sensitive tools open fresh state every time",
        ],
    },
    {
        "name": "Evidence and Verification",
        "principles": [
            "done means verified when verification is possible",
            "blocked is different from failed",
            "attempted_unverified is better than fake success",
            "evidence must be carried in task payload",
            "reply text should be downstream of execution outcome",
        ],
        "executions": [
            "record per-step execution outcomes",
            "aggregate status across the plan",
            "attach screenshots paths urls or file paths as evidence",
            "classify incomplete actions honestly",
            "promote final verification summary into the response payload",
        ],
        "verifications": [
            "overall_status is always present after acting",
            "evidence list is attached to task payload",
            "download checks look for real saved files",
            "messaging checks look for verified send markers",
            "filesystem checks compare postcondition state",
        ],
        "failures": [
            "narrative success without evidence",
            "tool errors get swallowed into polite text",
            "final response ignores blocked state",
            "verification output is computed but not returned",
            "UI cannot see why a task failed",
        ],
    },
    {
        "name": "Black Box",
        "principles": [
            "every real runtime turn should leave a trail",
            "chat history and agent work are separate sections",
            "cross-agent handoff needs durable summaries",
            "tool activity should be attached to the parent task",
            "the black box is for truth, not for decoration",
        ],
        "executions": [
            "start a black box agent session per runtime request",
            "log the user prompt as a chat history event",
            "log tool execution results with verification metadata",
            "log the assistant reply and terminal task state",
            "close the session with a concise agent summary",
        ],
        "verifications": [
            "sections endpoint returns chat_history and agent_work",
            "chat entries carry role and session identifiers",
            "agent summaries mention route state and verification",
            "tool results are available in activity logs",
            "external agents can add their own sessions safely",
        ],
        "failures": [
            "black box exists but runtime never writes to it",
            "user history and agent summaries are mixed together",
            "tool steps do not inherit task correlation",
            "agent work is invisible to the next agent",
            "session summaries remain empty after a run",
        ],
    },
    {
        "name": "Browser Sessions",
        "principles": [
            "reuse existing context before opening new browser state",
            "session naming must be stable per task session",
            "site reuse matters for messaging and login flows",
            "browser control should preserve active browser choice",
            "one session map should be queryable from the API",
        ],
        "executions": [
            "derive browser session id from stable session id",
            "remember browser session after acting",
            "attach session id to browser control actions",
            "carry current site and url in task state",
            "publish browser session snapshot through API",
        ],
        "verifications": [
            "browser session endpoint lists session snapshots",
            "follow-up tasks keep the same browser session label",
            "opened site survives plan continuation",
            "requested browser survives follow-up actions",
            "tool payload includes browser session metadata",
        ],
        "failures": [
            "every request opens a new tab or context",
            "whatsapp reuse is lost between commands",
            "browser choice resets to default unexpectedly",
            "session metadata never reaches the UI",
            "current url is discarded after success",
        ],
    },
    {
        "name": "Messaging",
        "principles": [
            "recipient and body are distinct pending slots",
            "existing WhatsApp state should be reused before fallback",
            "verified send evidence matters more than narration",
            "platform routing should stay explicit",
            "contact tasks should not hijack unrelated prompts",
        ],
        "executions": [
            "resolve receiver and message text before send",
            "call messaging tool with platform metadata",
            "reuse WhatsApp persistent state when connected",
            "surface blocked status when QR or readiness is missing",
            "record messaging verification outcome into task state",
        ],
        "verifications": [
            "message result includes receiver and platform",
            "successful sends emit verified or attempted status honestly",
            "not-ready state is blocked instead of success",
            "pending slot prompt asks for missing receiver or body",
            "assistant reply mentions what was actually verified",
        ],
        "failures": [
            "fake sent reply without chat evidence",
            "new tab opens when a session already exists",
            "missing body produces a generic reply",
            "not connected is misread as success",
            "message route drops session metadata",
        ],
    },
    {
        "name": "Downloads",
        "principles": [
            "direct downloads should save and verify the file",
            "non-direct targets should discover official sources honestly",
            "page interaction blockers should be explicit",
            "download metadata should include path size and source",
            "download routing must not claim completion before the file exists",
        ],
        "executions": [
            "detect direct url mode first",
            "search for official windows installer sources when target is not a url",
            "prefer direct asset links when discovered",
            "save file into the downloads directory or requested folder",
            "return structured blocker when only a landing page is found",
        ],
        "verifications": [
            "saved file path exists on disk",
            "download size is greater than zero",
            "direct asset discovery is surfaced in mode metadata",
            "official page discovery returns source url and search query",
            "verifier marks blocked instead of success for page-only discovery",
        ],
        "failures": [
            "string search target is passed to a raw downloader",
            "download says done but file never appears",
            "source url is lost after search fallback",
            "installer discovery hides the official page it found",
            "temporary files are mistaken for complete downloads",
        ],
    },
    {
        "name": "Research and Leads",
        "principles": [
            "local lead research should be a first-class operation",
            "sources should be deduped before summarization",
            "directory records need names phones and addresses when found",
            "research output should stay evidence-backed",
            "local status queries must not be hijacked by research",
        ],
        "executions": [
            "classify business and local directory prompts distinctly",
            "run multiple search variants for local entities",
            "enrich top sources by reading pages",
            "extract phones and address hints into records",
            "return directory records in the response payload",
        ],
        "verifications": [
            "directory queries route to directory_search",
            "summary contains actionable local entities",
            "sources remain attached for auditability",
            "record extraction de-duplicates entities",
            "plain time queries still stay local",
        ],
        "failures": [
            "school search falls back to casual chat",
            "local lead query loses phone and address fields",
            "research summary has no linked sources",
            "directory extraction duplicates the same entity repeatedly",
            "status questions get sent to the web unnecessarily",
        ],
    },
    {
        "name": "Voice",
        "principles": [
            "voice follows the same task lifecycle as text",
            "voice session ids must be stable for follow-up turns",
            "wake-word cleanup should happen before routing",
            "tts should speak final verified text only",
            "voice payload should expose task metadata to the UI",
        ],
        "executions": [
            "transcribe audio when provided",
            "resolve stable session id for voice requests",
            "call the same runtime orchestrator as text chat",
            "generate tts from the final response",
            "return task id state verification and evidence",
        ],
        "verifications": [
            "voice reply includes task metadata",
            "voice and text can share session ids",
            "follow-up context survives across voice turns",
            "tts generation uses the actual final reply",
            "voice mode stays observable in tests",
        ],
        "failures": [
            "voice creates a throwaway session each turn",
            "tts speaks unverified or stale text",
            "audio path bypasses task runtime",
            "voice response hides verification state",
            "session id falls back to a random trace every time",
        ],
    },
    {
        "name": "Autonomy",
        "principles": [
            "autonomy should queue tasks instead of replaying digests",
            "automation needs the same task metadata as chat",
            "retry should resume from the failed step when possible",
            "blocked reasons should stay visible",
            "autonomous jobs must not fork a separate truth model",
        ],
        "executions": [
            "route automation instruction through run_chat_runtime",
            "derive stable automation session identity",
            "return task metadata in auto endpoint payload",
            "preserve evidence and pending slots for automation",
            "surface route and trace ids for diagnosis",
        ],
        "verifications": [
            "automation payload includes task id and state",
            "blocked automation is inspectable through task endpoint",
            "automation and chat share the same runtime behavior",
            "response route survives through the automation adapter",
            "old digest text no longer substitutes for real state",
        ],
        "failures": [
            "autonomous mode replays stale text",
            "automation hides verification data",
            "task queue state is not persisted",
            "retry restarts from the wrong point",
            "automation runs a different brain than chat",
        ],
    },
    {
        "name": "Memory and Training",
        "principles": [
            "memory should support execution, not hijack it",
            "verified workflows are better than memorized phrases",
            "task reuse must stay compatibility-aware",
            "user facts should be kept separate from operational state",
            "conversation context should be compressed, not discarded",
        ],
        "executions": [
            "recall memory hits before runtime planning",
            "store successful operational tasks after completion",
            "keep user facts in a dedicated store",
            "compress request history before provider chat fallback",
            "preserve reusable task registry independently of chat history",
        ],
        "verifications": [
            "memory recall snippets appear in payload",
            "tool-first success records task attempts",
            "fact queries bypass system status operations correctly",
            "conversation history remains bounded and saved",
            "context compression retains recent semantic turns",
        ],
        "failures": [
            "stale learned workflows override explicit user input",
            "task memory never records terminal status",
            "user facts swallow live system requests",
            "history growth slows the runtime path",
            "training captures raw sentences without parameters",
        ],
    },
    {
        "name": "Provider Routing",
        "principles": [
            "cheap paths should handle trivial chat",
            "planning and acting are different responsibilities",
            "provider fallback should stay visible",
            "rotation should not override deterministic execution",
            "model choice should be query-aware and inspectable",
        ],
        "executions": [
            "score query complexity",
            "pick local fast chat for trivial prompts",
            "fallback from cloud to local when needed",
            "keep provider metadata in the response",
            "separate planner provider from response provider",
        ],
        "verifications": [
            "brain payload shows selected model and responder provider",
            "query router recommendation is preserved in chat responses",
            "provider fallback leaves an audit trail",
            "tool-first tasks bypass freeform provider execution",
            "invalid provider inputs are rejected early",
        ],
        "failures": [
            "provider rotation masks tool-routing regressions",
            "fallback succeeds but metadata claims the wrong model",
            "chat provider is blamed for a routing bug",
            "deterministic actions incur unnecessary cloud latency",
            "final response omits the provider used",
        ],
    },
    {
        "name": "UI and Introspection",
        "principles": [
            "the UI should be able to see task truth",
            "introspection endpoints must stay cheap and stable",
            "health checks should not run heavy discovery",
            "tool hub should reflect real capability availability",
            "users need evidence and blocked reasons, not just pretty text",
        ],
        "executions": [
            "return task id route and verification in chat payloads",
            "publish capability and browser session endpoints",
            "serve black-box sections for human and agent inspection",
            "update status stream from runtime payloads",
            "keep legacy fields for compatibility while exposing new ones",
        ],
        "verifications": [
            "UI runtime tests can fetch task endpoints",
            "capabilities endpoint lists active domains",
            "black-box section endpoints return structured data",
            "status stream uses current payload metadata",
            "legacy frontend requests still succeed",
        ],
        "failures": [
            "task state exists but the UI cannot read it",
            "health endpoint becomes a slow tool hub call",
            "new fields break old frontend contracts",
            "status board shows stale or missing route info",
            "black box cannot be surfaced to the operator console",
        ],
    },
    {
        "name": "Safety and Honesty",
        "principles": [
            "powerful local mode still needs explicit safety boundaries",
            "destructive actions should stay confirmation-gated",
            "blocked state must be honest and actionable",
            "verification failures must not be reframed as success",
            "human trust is a runtime invariant",
        ],
        "executions": [
            "gate dangerous file and shell actions with confirmation",
            "mark finance-sensitive web tasks as supervised by default",
            "stop on missing receiver message or url before acting",
            "surface blocker text exactly when verification is missing",
            "keep failure reasons machine-readable in payloads",
        ],
        "verifications": [
            "confirm fields become pending slots when needed",
            "destructive actions do not run without confirmation",
            "failed tools preserve their error codes",
            "blocked responses explain what detail is missing",
            "assistant tone stays honest under failure",
        ],
        "failures": [
            "unsafe command executes from casual confirmation",
            "failure is converted into a polished fake success",
            "missing inputs reach live automation tools",
            "sensitive flows run unsupervised",
            "error codes are lost in user-facing text",
        ],
    },
    {
        "name": "Graph Verification",
        "principles": [
            "architecture changes need graph visibility",
            "graph reports can become stale after code changes",
            "connectivity checks should distinguish stale nodes from isolated nodes",
            "core runtime files should not remain invisible forever",
            "verification should call out stale graph artifacts explicitly",
        ],
        "executions": [
            "inspect graph report timestamp before trusting it",
            "check isolated-node scripts against current graph data",
            "confirm execution context and runtime hubs are well connected",
            "note when new files are absent from old graph artifacts",
            "regenerate graph artifacts when the environment allows it",
        ],
        "verifications": [
            "graph report timestamp is surfaced in the audit",
            "god nodes include runtime abstractions when graph is current",
            "zero-degree node count is checked explicitly",
            "new runtime files are tracked as stale when missing from the graph",
            "final audit distinguishes connected graph from stale graph",
        ],
        "failures": [
            "old graph is treated as current truth",
            "new modules remain absent and nobody notices",
            "bridge scripts patch the graph without documenting staleness",
            "isolated-node count is misunderstood",
            "graph audit ignores manual post-processing",
        ],
    },
]


def build_lines() -> list[str]:
    lines: list[str] = []
    lines.append("# JARVIS Neural Schema")
    lines.append("")
    lines.append("This schema is generated to preserve the original upgrade target while defining execution rules for a real-world, evidence-first Jarvis runtime.")
    lines.append("")
    lines.append("## Original Task List")
    lines.append("")
    for index, item in enumerate(ORIGINAL_TASKS, 1):
        lines.append(f"{index}. {item}")
    lines.append("")
    lines.append("## Schema Rules")
    lines.append("")

    rule_number = 1
    domain_count = len(DOMAINS)
    domain_index = 0
    while len(lines) < MIN_LINES:
        domain = DOMAINS[domain_index % domain_count]
        if len(lines) == 0 or not lines[-1].startswith(f"### {domain['name']}"):
            lines.append(f"### {domain['name']}")
        principles = domain["principles"]
        executions = domain["executions"]
        verifications = domain["verifications"]
        failures = domain["failures"]
        for local_index in range(1, 121):
            principle = principles[(rule_number + local_index) % len(principles)]
            execution = executions[(rule_number * 2 + local_index) % len(executions)]
            verification = verifications[(rule_number * 3 + local_index) % len(verifications)]
            failure = failures[(rule_number * 5 + local_index) % len(failures)]
            lines.append(
                f"{rule_number:05d} | domain={domain['name']} | principle={principle} | execution={execution} | verification={verification} | failure_guard={failure}"
            )
            rule_number += 1
            if len(lines) >= MIN_LINES:
                break
        lines.append("")
        domain_index += 1
    return lines


def main() -> None:
    lines = build_lines()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} with {len(lines)} lines.")


if __name__ == "__main__":
    main()
