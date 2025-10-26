"""
Workflow Engine
Orchestrates the entire multi-agent workflow
"""
from typing import Dict, Any, Optional, List, Set
from pathlib import Path
from datetime import datetime
import json
import asyncio

from src.config import config
from src.mcp.protocol import MCPContext, WorkflowPlan
from src.llm_client import get_llm_client
from src.tools import ToolRegistry
from src.agents.orchestrator import OrchestratorAgent
from src.agents.planner import PlannerAgent
from src.agents.executor import ExecutorAgent
from src.agents.strategy_team import (
    StrategySynthesizerAgent,
    StrategyEvaluatorAgent,
    JudgerAgent
)
from src.agents.writer import WriterAgent


class WorkflowEngine:
    """Main workflow orchestration engine"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
    
    def _initialize_journal(self, workspace_path: Path, session_id: str, user_request: str):
        """Initialize the main journal file"""
        journal_path = workspace_path / "main_journal.md"
        
        with open(journal_path, 'w') as f:
            f.write(f"""# Workflow Execution Journal

**Session ID:** {session_id}
**User Request:** {user_request}
**Started:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

""")
        return journal_path
    
    def _log_step_to_journal(
        self,
        journal_path: Path,
        step_num: int,
        objective: str,
        result: Dict[str, Any],
        files_created: list
    ):
        """Log a completed step to the journal"""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(journal_path, 'a') as f:
            f.write(f"""## Step {step_num}: {objective}

**Timestamp:** {timestamp}
**Status:** {'✅ Success' if result.get('success') else '❌ Failed'}
**Iterations Used:** {result.get('iterations', 'N/A')}

### Input
```
{objective}
```

### Thoughts and Reasoning
""")
            
            # Log thoughts
            thoughts = result.get('thoughts', [])
            if thoughts:
                for i, thought in enumerate(thoughts, 1):
                    f.write(f"{i}. {thought}\n")
            else:
                f.write("No thoughts recorded.\n")
            
            f.write("\n### Actions Taken\n")
            
            # Log actions (tool calls)
            actions = result.get('actions', [])
            if actions:
                for action in actions:
                    # Handle both dict and ToolCall object
                    if hasattr(action, 'tool_name'):
                        tool_name = action.tool_name
                        arguments = action.arguments
                    else:
                        tool_name = action.get('tool_name', 'unknown')
                        arguments = action.get('arguments', {})
                    f.write(f"- **{tool_name}** with arguments: `{json.dumps(arguments)}`\n")
            else:
                f.write("No actions taken.\n")
            
            f.write("\n### Observations\n")
            
            # Log observations (tool results)
            observations = result.get('observations', [])
            if observations:
                for i, obs in enumerate(observations, 1):
                    # Truncate long observations
                    obs_preview = obs[:300] + "..." if len(obs) > 300 else obs
                    f.write(f"{i}. {obs_preview}\n")
            else:
                f.write("No observations recorded.\n")
            
            f.write("\n### Files Created\n")
            if files_created:
                for file in files_created:
                    f.write(f"- `{file}`\n")
            else:
                f.write("No new files created.\n")
            
            f.write("\n### Final Result\n")
            f.write(f"```\n{result.get('result', 'No result')}\n```\n")
            
            f.write("\n---\n\n")
    
    def _format_plan_progress(
        self,
        plan: Optional[WorkflowPlan],
        plan_step_status: Dict[int, Dict[str, Any]]
    ) -> str:
        """Create a human-readable summary of plan progress"""
        if not plan:
            return "No plan yet. Request Planner to generate a comprehensive plan."
        lines: List[str] = []
        for step in plan.steps:
            step_num = step.get("step_number")
            objective = step.get("objective", "(missing objective)")
            status_info = plan_step_status.get(step_num)
            if status_info:
                status = status_info.get("status", "unknown").lower()
                summary = status_info.get("summary", "")
                if status == "success":
                    badge = "✅"
                    detail = f"SUCCESS - {summary}" if summary else "SUCCESS"
                elif status == "failed":
                    badge = "⚠️"
                    detail = f"FAILED - {summary}" if summary else "FAILED"
                else:
                    badge = "ℹ️"
                    detail = summary or "IN PROGRESS"
            else:
                badge = "⬜"
                detail = "PENDING"
            lines.append(f"{badge} Step {step_num}: {objective}")
            lines.append(f"   ↳ {detail}")
        return "\n".join(lines)

    def _build_state_summary(
        self,
        current_status: str,
        plan_total_steps: int,
        plan_steps_completed: int,
        strategy_iterations_completed: int,
        final_report_created: bool,
        decisions_made: int
    ) -> str:
        """Summarize workflow state for the orchestrator"""
        lines = [
            f"Workflow status: {current_status}",
            f"Decisions made so far: {decisions_made}",
            f"Plan steps completed: {plan_steps_completed}/{plan_total_steps}",
            f"Strategy refinement iterations completed: {strategy_iterations_completed}",
            f"Final report created: {'Yes' if final_report_created else 'No'}"
        ]
        return "\n".join(lines)

    def _append_existing_files(self, task_description: str, existing_files: Set[str]) -> str:
        """Append existing workspace files context to a task description"""
        if not existing_files:
            return task_description
        files_list = "\n".join(f"- {name}" for name in sorted(existing_files))
        return (
            f"{task_description}\n\n"
            "NOTE: The following files already exist in the workspace:\n"
            f"{files_list}\n"
            "Reuse existing artifacts when possible and avoid duplicate downloads or creations."
        )

    def _summarize_result(self, result: Dict[str, Any]) -> str:
        """Create a concise summary string from an agent result"""
        if not result:
            return "No result returned."
        success = result.get("success")
        if success is False:
            base = result.get("error") or result.get("result") or "Task reported failure."
        else:
            base = result.get("result") or "Task completed."
        if not isinstance(base, str):
            base = str(base)
        line = base.strip().splitlines()[0] if base else ""
        if len(line) > 160:
            line = f"{line[:157]}..."
        prefix = "SUCCESS" if success else "STATUS"
        return f"{prefix}: {line or 'No further details provided.'}"

    async def execute_workflow(
        self,
        user_request: str,
        session_id: Optional[str] = None
    ) -> MCPContext:
        """
        Execute complete workflow for a user request
        """
        
        # Create session
        if not session_id:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            # Create safe filename from request
            safe_name = "".join(c if c.isalnum() else "_" for c in user_request[:30])
            session_id = f"{timestamp}_{safe_name}"
        
        # Create workspace
        workspace_path = config.WORKSPACE_ROOT / session_id
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize journal
        journal_path = self._initialize_journal(workspace_path, session_id, user_request)
        print(f"[{session_id}] Initialized journal: {journal_path}")
        
        # Initialize context
        context = MCPContext(
            session_id=session_id,
            workspace_path=str(workspace_path),
            user_request=user_request,
            status="initializing"
        )
        
        # Initialize tool registry
        tool_registry = ToolRegistry(workspace_path)
        
        # Initialize agents
        orchestrator = OrchestratorAgent(
            agent_id="orchestrator",
            agent_type="orchestrator",
            workspace_path=str(workspace_path),
            tool_registry=tool_registry,
            llm_client=self.llm_client
        )
        
        planner = PlannerAgent(
            agent_id="planner",
            agent_type="planner",
            workspace_path=str(workspace_path),
            tool_registry=tool_registry,
            llm_client=self.llm_client
        )
        
        executor = ExecutorAgent(
            agent_id="executor",
            agent_type="executor",
            workspace_path=str(workspace_path),
            tool_registry=tool_registry,
            llm_client=self.llm_client
        )
        
        writer = WriterAgent(
            agent_id="writer",
            agent_type="writer",
            workspace_path=str(workspace_path),
            tool_registry=tool_registry,
            llm_client=self.llm_client
        )
        
        scanner_tool = tool_registry.get_tool("file_system_scanner")
        
        plan: Optional[WorkflowPlan] = None
        plan_step_status: Dict[int, Dict[str, Any]] = {}
        last_action_summary = "Workflow initialized."
        strategy_iterations_completed = 0
        final_report_created = False
        journal_step_counter = 0
        max_decisions = 40
        finished = False
        
        try:
            for decision_index in range(max_decisions):
                files_result = await scanner_tool.execute()
                plan_progress = self._format_plan_progress(plan, plan_step_status)
                plan_total_steps = len(plan.steps) if plan else 0
                plan_steps_completed = sum(
                    1 for info in plan_step_status.values() if info.get("status") == "success"
                )
                state_summary = self._build_state_summary(
                    current_status=context.status,
                    plan_total_steps=plan_total_steps,
                    plan_steps_completed=plan_steps_completed,
                    strategy_iterations_completed=strategy_iterations_completed,
                    final_report_created=final_report_created,
                    decisions_made=decision_index
                )
                decision = await orchestrator.decide_next_step(
                    user_request=user_request,
                    plan=plan,
                    current_files=files_result,
                    plan_progress=plan_progress,
                    state_summary=state_summary,
                    recent_action=last_action_summary
                )
                next_agent = (decision.get("next_agent") or "").lower()
                task_description = decision.get("task")
                plan_step = decision.get("plan_step")
                reasoning = decision.get("reasoning", "")
                
                print(f"[{session_id}] Orchestrator decision -> agent={next_agent}, plan_step={plan_step}")
                if reasoning:
                    preview = reasoning.strip()
                    if len(preview) > 400:
                        preview = preview[:397] + "..."
                    print(f"[{session_id}] Decision rationale:\n{preview}")
                
                if not next_agent:
                    raise ValueError("Orchestrator did not provide NEXT_AGENT.")
                if next_agent not in {"planner", "executor", "strategy_refinement", "writer", "finish"}:
                    raise ValueError(f"Orchestrator selected unknown agent '{next_agent}'.")
                if next_agent not in {"finish", "planner"} and not task_description:
                    raise ValueError("Orchestrator did not provide TASK description for delegated agent.")
                
                if isinstance(plan_step, str):
                    try:
                        plan_step = int(plan_step)
                    except ValueError:
                        plan_step = None if plan_step.upper() == "NONE" else plan_step
                
                if next_agent == "finish":
                    context.status = "completed"
                    last_action_summary = "Workflow marked complete by orchestrator."
                    finished = True
                    break
                
                if next_agent == "planner":
                    context.status = "planning"
                    print(f"[{session_id}] Planner selected to create or update plan...")
                    plan = await planner.create_plan(user_request)
                    context.plan = plan
                    plan_step_status = {}
                    plan_file = workspace_path / "plan.json"
                    with open(plan_file, 'w') as f:
                        json.dump(plan.dict(), f, indent=2, default=str)
                    print(f"[{session_id}] Plan created with {len(plan.steps)} steps")
                    with open(journal_path, 'a') as f:
                        f.write(f"""## Planning Phase

**Planner Agent** created a {len(plan.steps)}-step plan:

""")
                        for step in plan.steps:
                            f.write(f"{step.get('step_number')}. {step.get('objective')}\n")
                        f.write(f"\n**Plan saved to:** `plan.json`\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n")
                    last_action_summary = f"Planner produced plan with {len(plan.steps)} steps."
                    context.status = "executing"
                    continue
                
                if next_agent == "executor":
                    context.status = "executing"
                    objective = task_description or "(No objective provided)"
                    print(f"[{session_id}] Delegating to Executor: {objective[:120]}...")
                    files_before = set(f.name for f in workspace_path.iterdir() if f.is_file())
                    enhanced_task = self._append_existing_files(objective, files_before)
                    result = await executor.execute_task(enhanced_task)
                    print(f"[{session_id}] Executor success: {result.get('success')}")
                    files_after = set(f.name for f in workspace_path.iterdir() if f.is_file())
                    files_created = list(files_after - files_before)
                    journal_step_counter += 1
                    log_step_number = plan_step if isinstance(plan_step, int) else journal_step_counter
                    self._log_step_to_journal(journal_path, log_step_number, objective, result, files_created)
                    summary = self._summarize_result(result)
                    if isinstance(plan_step, int):
                        status_flag = "success" if result.get("success") else "failed"
                        plan_step_status[plan_step] = {"status": status_flag, "summary": summary}
                    last_action_summary = summary
                    continue
                
                if next_agent == "strategy_refinement":
                    context.status = "refining"
                    print(f"[{session_id}] Initiating strategy refinement loop...")
                    files_before = set(f.name for f in workspace_path.iterdir() if f.is_file())
                    await self._execute_strategy_refinement(
                        workspace_path,
                        tool_registry,
                        user_request,
                        journal_path
                    )
                    strategy_iterations_completed = config.MAX_REFINEMENT_ITERATIONS
                    files_after = set(f.name for f in workspace_path.iterdir() if f.is_file())
                    files_created = list(files_after - files_before)
                    journal_step_counter += 1
                    log_step_number = plan_step if isinstance(plan_step, int) else journal_step_counter
                    refinement_summary = (
                        f"Strategy refinement loop completed ({config.MAX_REFINEMENT_ITERATIONS} iterations)."
                    )
                    refinement_result = {
                        "success": True,
                        "result": refinement_summary,
                        "iterations": config.MAX_REFINEMENT_ITERATIONS,
                        "thoughts": [],
                        "actions": [],
                        "observations": []
                    }
                    self._log_step_to_journal(
                        journal_path,
                        log_step_number,
                        "Execute strategy refinement loop",
                        refinement_result,
                        files_created
                    )
                    if isinstance(plan_step, int):
                        plan_step_status[plan_step] = {"status": "success", "summary": refinement_summary}
                    last_action_summary = refinement_summary
                    context.status = "executing"
                    continue
                
                if next_agent == "writer":
                    context.status = "reporting"
                    print(f"[{session_id}] Delegating to Writer for final report...")
                    files_before = set(f.name for f in workspace_path.iterdir() if f.is_file())
                    with open(journal_path, 'r') as f:
                        journal_content = f.read()
                    all_files = [f['name'] for f in files_result]
                    writer_output = await writer.generate_report(
                        user_request=user_request,
                        all_files=all_files,
                        journal_content=journal_content
                    )
                    report_path = workspace_path / "final_report.md"
                    report_exists = report_path.exists()
                    files_after = set(f.name for f in workspace_path.iterdir() if f.is_file())
                    files_created = list(files_after - files_before)
                    journal_step_counter += 1
                    log_step_number = plan_step if isinstance(plan_step, int) else journal_step_counter
                    writer_result = {
                        "success": report_exists,
                        "result": writer_output,
                        "thoughts": [],
                        "actions": [],
                        "observations": []
                    }
                    self._log_step_to_journal(
                        journal_path,
                        log_step_number,
                        task_description or "Generate final report",
                        writer_result,
                        files_created
                    )
                    if report_exists:
                        final_report_created = True
                        print(f"[{session_id}] ✓ Final report created: {report_path}")
                        with open(journal_path, 'a') as f:
                            f.write(f"""## Final Report Generation

**Writer Agent** completed the final report.

**Report saved to:** `final_report.md`
**Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

""")
                        writer_summary = f"Final report created at {report_path.name}."
                    else:
                        print(f"[{session_id}] ⚠️  Warning: final_report.md was not created")
                        writer_summary = "Writer completed task but final_report.md not found."
                    if isinstance(plan_step, int):
                        plan_step_status[plan_step] = {
                            "status": "success" if report_exists else "failed",
                            "summary": writer_summary
                        }
                    last_action_summary = writer_summary
                    context.status = "executing"
                    continue
            else:
                if not finished:
                    context.status = "failed"
                    warning = (
                        "Maximum orchestration decisions reached before workflow completion. "
                        "Review plan and orchestrator instructions."
                    )
                    print(f"[{session_id}] ⚠️ {warning}")
                    with open(journal_path, 'a') as f:
                        f.write(f"""## ⚠️ Workflow Incomplete

**Reason:** {warning}
**Decisions Made:** {max_decisions}
**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

""")

            if context.status == "completed":
                print(f"[{session_id}] Workflow completed successfully!")
            elif context.status == "failed":
                print(f"[{session_id}] Workflow ended in FAILED state.")
            print(f"[{session_id}] Journal saved to: {journal_path}")
            
            if context.status == "completed" and not final_report_created:
                print(f"[{session_id}] ⚠️ Completed state reached without final report. Verify requirements.")
            
            return context
        except Exception as e:
            context.status = "failed"
            print(f"[{session_id}] Workflow failed: {str(e)}")
            with open(journal_path, 'a') as f:
                f.write(f"""## ❌ Workflow Failed

**Error:** {str(e)}
**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

""")
            raise
    
    async def _execute_strategy_refinement(
        self,
        workspace_path: Path,
        tool_registry: ToolRegistry,
        user_request: str,
        journal_path: Path
    ):
        """Execute 3-iteration strategy refinement loop"""
        
        # Log strategy refinement start to journal
        with open(journal_path, 'a') as f:
            f.write(f"""## Strategy Refinement Loop (3 Iterations)

**Started:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

""")
        
        synthesizer = StrategySynthesizerAgent(
            agent_id="synthesizer",
            agent_type="strategy_synthesizer",
            workspace_path=str(workspace_path),
            tool_registry=tool_registry,
            llm_client=self.llm_client
        )
        
        evaluator = StrategyEvaluatorAgent(
            agent_id="evaluator",
            agent_type="strategy_evaluator",
            workspace_path=str(workspace_path),
            tool_registry=tool_registry,
            llm_client=self.llm_client
        )
        
        judger = JudgerAgent(
            agent_id="judger",
            agent_type="judger",
            workspace_path=str(workspace_path),
            tool_registry=tool_registry,
            llm_client=self.llm_client
        )
        
        feedback = None
        
        for iteration in range(1, config.MAX_REFINEMENT_ITERATIONS + 1):
            print(f"  Strategy Iteration {iteration}/3...")
            
            # Log iteration start to journal
            with open(journal_path, 'a') as f:
                f.write(f"""### Iteration {iteration}

""")
            
            # 1. Synthesize strategy
            print(f"    - Generating strategy code...")
            synth_result = await synthesizer.generate_strategy(
                user_request=user_request,
                iteration=iteration,
                feedback=feedback
            )
            
            with open(journal_path, 'a') as f:
                f.write(f"""**Strategy Synthesizer:**
- Generated: `strategy_v{iteration}.py`
- Feedback incorporated: {'Yes' if feedback else 'No (first iteration)'}

""")
            
            # 2. Evaluate strategy
            print(f"    - Running backtest and evaluation...")
            eval_task = f"""Execute the strategy in strategy_v{iteration}.py and evaluate its performance.

REQUIRED TASKS:
1. Run the strategy code using python_execution
2. Calculate metrics using regression_based_strategy_evaluation
3. Save metrics to results_v{iteration}.json
4. **CRITICAL: Generate and save a comprehensive evaluation report to evaluation_v{iteration}.md**

The evaluation report (evaluation_v{iteration}.md) MUST include:
- Performance metrics summary (Total Return, Sharpe Ratio, Max Drawdown, Alpha, Beta, etc.)
- Risk analysis (Volatility, VaR, Downside Risk)
- Trading statistics (Win Rate, Profit Factor, Number of Trades)
- Strategy strengths and weaknesses based on the metrics
- Comparison with benchmark (buy-and-hold)
- Specific recommendations for improvement in next iteration

Use file_saver to save the evaluation report as 'evaluation_v{iteration}.md'.

This is iteration {iteration} of 3. Be thorough and analytical."""
            
            eval_result = await evaluator.execute_task(eval_task)
            
            # Check if evaluation report was created
            eval_report_file = workspace_path / f"evaluation_v{iteration}.md"
            eval_report_created = eval_report_file.exists()
            
            with open(journal_path, 'a') as f:
                f.write(f"""**Strategy Evaluator:**
- Backtest completed: {eval_result.get('success')}
- Results saved to: `results_v{iteration}.json`
- Evaluation report: {'✅ `evaluation_v' + str(iteration) + '.md`' if eval_report_created else '⚠️ Not generated'}

""")
            
            # 3. Judge and provide feedback
            print(f"    - Generating feedback...")
            judge_result = await judger.evaluate_strategy(iteration)
            
            # Load feedback for next iteration
            feedback_file = workspace_path / f"feedback_v{iteration}.txt"
            if feedback_file.exists():
                with open(feedback_file, 'r') as f:
                    feedback = f.read()
                
                with open(journal_path, 'a') as f_journal:
                    f_journal.write(f"""**Judger:**
- Feedback saved to: `feedback_v{iteration}.txt`
- Key suggestions: {feedback[:200]}...

""")
        
        # Log completion to journal
        with open(journal_path, 'a') as f:
            f.write(f"""**Strategy Refinement Complete**
- Total iterations: 3
- Final strategy: `strategy_v3.py`
- Completed: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

""")
        
        print(f"  Strategy refinement complete (3 iterations)")
