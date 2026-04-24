## TODO

- Decide whether `Core/voice.py` should remain a test-safe simulator or be replaced with a single production TTS implementation (currently, production TTS lives in `Core/main.py`).
- Reduce legacy configuration surface area:
  - `.env.example` contains many legacy variables; prune to the ones actually used.
  - Keep `config.yaml` as the main non-secret config, `.env` for secrets only.
- Clean up tool/worktree artifacts if present:
  - `.claude/` (worktrees, caches) should not ship with the project.
- Consider adding a `pyproject.toml` and using a single dependency workflow (pip/uv/poetry).

