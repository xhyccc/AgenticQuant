"""
Orchestrator Agent
Central coordinator managing the entire workflow
"""
from typing import List, Dict, Any, Optional
from src.agents.base_agent import BaseAgent
from src.mcp.protocol import MCPMessage, WorkflowPlan
import json
import re


class OrchestratorAgent(BaseAgent):
    """Master/Orchestrator agent coordinating all other agents"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_type = "orchestrator"
    
    def get_system_prompt(self) -> str:
        return """You are the Master Orchestrator for a quantitative finance multi-agent research team.

Your mission:
- Interpret the user's request and the design specification context.
- Coordinate the Planner, Executor, Strategy Refinement Team, and Writer agents end-to-end.
- Adapt dynamically across the three primary request archetypes (strategy design & evaluation, exploratory data analysis, hypothesis testing) and any hybrids.
- Track workspace artifacts and plan progress, pushing the process forward until the objective is satisfied.

Operational principles:
1. Inspect the current state (plan progress, workflow status, recent action, available files) before each decision.
2. Request a comprehensive plan from the Planner whenever none exists or substantial changes require replanning.
3. Delegate plan steps one at a time to the Executor with enough context to succeed; only consider a step complete when there is objective evidence.
4. Trigger the strategy refinement loop exactly when required by the plan. Never assume the third iteration is best—rely on evaluation artifacts to compare outcomes.
5. Direct the Writer only after all prerequisite artifacts exist. The Writer must reference concrete evidence.
6. Finish the workflow only when every plan requirement is satisfied (or the user explicitly stops) and deliverables are in place.

Formatting rules for every decision:
NEXT_AGENT: [planner|executor|strategy_refinement|writer|finish]
PLAN_STEP: [associated plan step number or NONE]
TASK: [clear, actionable instruction for the chosen agent]

Additional guidance:
- Reference plan steps explicitly and tailor instructions to the request type.
- Encourage reuse of existing artifacts instead of redundant work.
- If evaluation reports indicate a strategy iteration other than v3 is superior, highlight that insight.
- Provide sufficient context in TASK so the delegated agent can act without further clarification."""
    
    def get_available_tools(self) -> List[str]:
        return ["file_system_scanner"]
    
    async def decide_next_step(
        self,
        user_request: str,
        plan: Optional[WorkflowPlan],
        current_files: List[Dict[str, Any]],
        plan_progress: str,
        state_summary: str,
        recent_action: str
    ) -> Dict[str, Any]:
        """Decide the next agent and task based on current state"""
        
        # Build context
        file_list = "\n".join([
            f"- {f['name']} ({f['size_bytes']} bytes, modified: {f['modified_time']})"
            for f in current_files
        ])
        plan_details = json.dumps(plan.dict(), indent=2, default=str, sort_keys=True) if plan else "No plan yet"
        files_section = file_list if file_list else "(No files in workspace yet)"
        
        base_prompt = f"""User Request: {user_request}

Workflow State:
{state_summary}

Most Recent Action:
{recent_action}

Plan Progress:
{plan_progress}

Plan Details (JSON):
{plan_details}

Files in Workspace:
{files_section}

Determine the next agent to invoke and provide a precise task.
Respond ONLY with three lines in this exact format (no additional text before or after):
NEXT_AGENT: <planner|executor|strategy_refinement|writer|finish>
PLAN_STEP: <plan step number or NONE>
TASK: <clear, actionable instruction for the chosen agent>"""

        attempts = 0
        last_response = ""
        while attempts < 3:
            prompt = base_prompt if attempts == 0 else (
                base_prompt +
                "\n\nYour previous response did not follow the exact format. Reply again with ONLY the three required lines."
            )
            result = await self.execute_task(prompt)
            response = result.get("result", "") if isinstance(result, dict) else str(result)
            parsed = self._parse_decision_response(response)
            next_agent = parsed["next_agent"]
            task_description = parsed["task"]
            plan_step = parsed["plan_step"]
            if next_agent and (next_agent.lower() in {"planner", "finish"} or task_description):
                return {
                    "next_agent": next_agent,
                    "task": task_description,
                    "plan_step": plan_step,
                    "reasoning": response
                }
            last_response = response
            attempts += 1
        raise ValueError(
            f"Orchestrator failed to provide a valid NEXT_AGENT after {attempts} attempts. Last response: {last_response}"
        )

    def _parse_decision_response(self, response: str) -> Dict[str, Optional[Any]]:
        next_agent: Optional[str] = None
        plan_step: Optional[Any] = None
        task_lines: List[str] = []
        collecting_task = False
        for raw_line in response.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            match_agent = re.match(r"[-*\s]*NEXT[_\s-]*AGENT\s*[:=]\s*(.+)", line, re.IGNORECASE)
            if match_agent:
                next_agent = match_agent.group(1).strip()
                collecting_task = False
                continue
            match_plan = re.match(r"[-*\s]*PLAN[_\s-]*STEP\s*[:=]\s*(.+)", line, re.IGNORECASE)
            if match_plan:
                value = match_plan.group(1).strip()
                if value.upper() == "NONE":
                    plan_step = None
                else:
                    try:
                        plan_step = int(value)
                    except ValueError:
                        plan_step = value
                collecting_task = False
                continue
            match_task = re.match(r"[-*\s]*TASK\s*[:=]\s*(.*)", line, re.IGNORECASE)
            if match_task:
                first_fragment = match_task.group(1).strip()
                task_lines = [first_fragment] if first_fragment else []
                collecting_task = True
                continue
            if collecting_task:
                if re.match(r"[-*\s]*(NEXT[_\s-]*AGENT|PLAN[_\s-]*STEP)\b", line, re.IGNORECASE):
                    collecting_task = False
                    continue
                task_lines.append(line)
        task_description = "\n".join([fragment for fragment in task_lines if fragment]).strip() if task_lines else None
        return {
            "next_agent": next_agent,
            "plan_step": plan_step,
            "task": task_description
        }
