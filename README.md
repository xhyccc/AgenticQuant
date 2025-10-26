# AgenticQuant

AgenticQuant is a multi-agent quantitative research stack that automates market research, data preparation, strategy design, backtesting, iterative evaluation, and reporting. A React-style (ReAct) reasoning loop coordinates specialist agents and MCP tools to deliver auditable, versioned analysis packages for each request.

## Key Features
- **Workflow Engine** orchestrates Planner, Executor, Strategy Team, Writer, and evaluation agents with a shared state store.
- **Seven MCP Tools** cover web research, finance data access, offline Python execution, file operations, strategy evaluation, and more.
- **Iterative Strategy Refinement** runs three feedback loops (Evaluator + Judger) and persists every iteration (`strategy_v#.py`, `results_v#.json`, feedback notes).
- **File-Based Audit Trail** captures plans, intermediate artifacts, metrics, and final reports per workspace session under `workspaces/<timestamp>_*`.
- **Modern Web Experience** provides session management, live status updates via WebSockets, artifact downloads, and a gradient UI.
- **Configurable LLM Layer** (OpenAI or Anthropic) with prompt templates per agent.

## Architecture at a Glance
```
User → Web UI / CLI → Workflow Engine
                        ↓
            Orchestrator → Planner → Executor → Strategy Team
                               ↓
                        Synthesizer / Evaluator / Judger (3x loop)
                               ↓
                         MCP Tools + Workspace Files
                               ↓
                          final_report.md & artifacts
```
- Prompts live in `src/agents/*.py`.
- Tool implementations live in `src/tools/` and follow the MCP protocol defined in `src/mcp/protocol.py`.
- `src/workflow_engine.py` drives the agent/task lifecycle.

## Quick Start
```bash
# 1) Setup environment and install dependencies
./setup.sh

# 2) Configure environment variables
cp .env.example .env
# edit .env with your OpenAI / Anthropic credentials and optional settings

# 3) Launch the application (virtualenv is activated by setup.sh)
python main.py
```
Open <http://localhost:8000> and submit a strategy brief (see "Example Request" below). Progress updates stream in real time; artifacts land in a new `workspaces/<timestamp>_<slug>/` folder.

## Example Request
```
Develop a momentum trading strategy for AAPL using:
- 20-day and 50-day moving average crossovers
- RSI indicator for entry/exit timing
- Backtest from 2020 to 2023
- Compare against SPY benchmark
```
Expect the full run (planning → reporting) to finish in roughly 10–15 minutes depending on model latency.

## Repository Layout
```
├── cli.py                    # CLI entry point
├── main.py                   # Web server bootstrap
├── src/
│   ├── agents/               # Planner, Executor, Writer, etc.
│   ├── tools/                # MCP tool implementations
│   ├── mcp/protocol.py       # MCP message schemas
│   ├── workflow_engine.py    # Agent orchestration logic
│   └── config.py             # Core configuration values
├── workspaces/               # Generated analysis artifacts (gitignored)
├── logs/                     # Execution logs (gitignored)
├── requirements.txt          # Python dependencies
├── setup.sh                  # Bootstrap script (venv + deps)
├── DEVELOPMENT.md            # Contributor & roadmap notes
└── GETTING_STARTED.md        # Extended onboarding guide
```

## Configuration
Environment variables are read from `.env`:
- `DEFAULT_LLM_PROVIDER` (`openai` or `anthropic`)
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`
- `DEFAULT_MODEL` and model-specific parameters
- Networking/tuning flags (see `.env.example`)

The number of refinement loops, default cost assumptions, and other controls live in `src/config.py`.

## Usage Modes
- **Web UI** (`python main.py`): interactive dashboard with session management, artifact downloads, and live run log.
- **CLI / Programmatic** (`python cli.py` or `example_usage.py`): launch analyses from scripts or terminal.
- **Generated Workspace**: inspect `plan.json`, `research_notes.md`, `strategy_v*.py`, `results_v*.json`, `evaluation_v*.md`, and `final_report.md` for each run.

## Development & Testing
```bash
# Activate env (if not already)
source venv/bin/activate

# Run linters/tests (extend as needed)
pytest -v
```
See `DEVELOPMENT.md` for adding agents or tools, prompt editing, and extension ideas.

## Contributing
1. Fork the repository and clone your fork.
2. Create a feature branch: `git checkout -b feature/awesome-improvement`.
3. Commit with clear messages and include tests/docs where relevant.
4. Push and open a pull request against `main` in <https://github.com/xhyccc/AgenticQuant>.

## Roadmap Highlights
- Dockerized execution sandbox
- Expanded data connectors (Bloomberg, news APIs)
- Portfolio optimization workflows
- Walk-forward / regime-aware evaluation
- Authentication and multi-user collaboration

## License
Specify the project license here (add LICENSE file if applicable).

---
Questions or ideas? Open an issue or discussion in the GitHub repo. Happy quanting! 🚀
