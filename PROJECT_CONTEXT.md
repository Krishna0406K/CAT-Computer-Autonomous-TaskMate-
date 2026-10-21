# CAT Project Context

## Hardware & System Constraints
- **GPU:** RTX 3050 6GB VRAM (strictly ONE LLM resident on GPU at a time).
- **RAM & CPU:** 16GB System RAM, Intel i5-12450H.
- **Model Rules:** Ollama serving `qwen3:8b` via `http://localhost:11434/v1` (OpenAI-compatible). Use thinking mode for planning, `/no_think` for fast execution. CPU fallback for small tasks (`qwen3:1.7b`).

## Current Status & Completed Phases
- **Phase 1: COMPLETE** 
  - FastAPI gateway built (`services/gateway/main.py`).
  - Ollama client wrapper implemented (`services/gateway/models.py`).
  - CLI test script verified and working (`cli.py`).

- **Phase 2: COMPLETE**
  - LangGraph plan→act→observe→verify loop built (`services/harness/graph.py`, `state.py`, nodes).
  - 5 initial tools implemented (`tools/browser_tools.py`, `office_tools.py`, `file_tools.py`, `screen_tools.py`).
  - Harness successfully connected to Phase 1 gateway.

- **Phase 3: COMPLETE**
  - Permission engine built (`services/permission/policy.py` with `RISK_TABLE`, `approval_queue.py`).
  - LangGraph execution loop updated to verify tool risk levels.
  - HIGH/CRITICAL actions successfully intercepted with a terminal Allow/Deny prompt.

- **Phase 4: COMPLETE**
  - SQLite database logging implemented (`data/cat.db`) to record tasks and execution steps.
  - Deterministic evaluation scripts built (`services/evaluator/deterministic.py` for file existence, row counts, etc.).

- **Phase 5: COMPLETE**
  - Tauri + React desktop window built (`apps/desktop/`) replacing the CLI.
  - Command box, live-streamed execution trace, and interactive UI permission popups integrated with the backend.

- **Phase 6: COMPLETE**
  - Basic vision tool implemented (`tools/screen_tools.py`) combining `computer.screenshot` with `qwen2.5vl:3b`.
  - Gateway model manager configured to handle automatic Ollama swaps between text (`qwen3:8b`) and vision (`qwen2.5vl:3b`).

- **Phase 7: COMPLETE**
  - Tauri background service configured to start on login, sitting quietly in the system tray (`apps/desktop/src-tauri/`).

- **Phase 8: COMPLETE**
  - Voice functionality implemented (`services/voice/stt.py` using `faster-whisper` on CPU, `services/voice/tts.py` using `Piper` on CPU).

- **Phase 9: COMPLETE**
  - Observatory dashboard overview page built, querying SQLite logs (`data/cat.db`) for tasks today, success rates, and metrics.

- **Phase 10: COMPLETE**
  - Advanced workflows and multi-step macro execution built (`services/macros/`), allowing the LangGraph harness to chain and replay complex sequences.

- **Phase 11: COMPLETE**
  - Production hardening & final packaging configured (Tauri release build scripts, clean background teardowns, and error recovery wrappers).

## Upcoming Target
- **Phase 12:** [Add your next milestone or target here, e.g., cloud sync extension, advanced plugin architecture, or multi-agent delegation].