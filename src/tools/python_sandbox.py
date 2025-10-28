"""
Python Execution Sandbox Tool
Secure execution environment for untrusted Python code
"""
from typing import Any, Dict, Optional, List
from src.tools.base import BaseTool
from src.mcp.protocol import ToolDefinition, ToolParameter
from src.llm_client import get_llm_client
from src.config import config
from pathlib import Path
from datetime import datetime
import asyncio
import tempfile
import json
import uuid
import logging
import re

logger = logging.getLogger(__name__)


class PythonExecutionTool(BaseTool):
    """Execute Python code in a secure sandbox"""
    
    def __init__(self, workspace_root: Path, timeout: int = 300, max_attempts: int = 10):
        super().__init__()
        self.name = "python_execution"
        self.workspace_root = workspace_root
        self.timeout = timeout
        self.sessions = {}  # session_id -> state
        self.code_llm_client = get_llm_client(
            provider=config.CODE_LLM_PROVIDER,
            model=config.CODE_LLM_MODEL
        )
        self.max_attempts = max_attempts

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description="""Executes Python analysis tasks end-to-end in a secure, stateful sandbox. Provide a natural-language task description; the tool will generate Python code with an internal LLM and run it automatically. Ideal for data analysis, simulations, backtesting, and visualization workflows. The sandbox has access to pandas, numpy, matplotlib, scipy, scikit-learn, and other data science libraries.

SUCCESSFUL EXECUTIONS AUTOMATICALLY SAVE THE GENERATED PYTHON SOURCE
- When a run completes successfully, the generated script is persisted in the workspace root using the configured filename pattern (see parameters).

CASCADE MODE WORKFLOW:
1. Supply a detailed `task_description` that is self-contained and context independent
2. The tool generates compliant Python code internally and executes it in the sandbox
3. Outputs, stdout/stderr, and created files are returned to the caller

EFFECTIVE TASK DESCRIPTIONS SHOULD:
- Mention required input files (with expected paths or filenames)
- Describe the analytical steps (transformations, indicators, models, metrics)
- Specify any plots or tables to produce and desired filenames
- Note success criteria or checks that should appear in the logs

The working directory is the workspace folder. All saved files will be available for review and use in subsequent steps.""",
            parameters=[
                ToolParameter(
                    name="task_description",
                    type="string",
                    description="Self-contained natural-language description of the Python analysis to perform. Specify required data sources, processing steps, file names, metrics, and plots so the generated code can execute without extra context.",
                    required=True
                ),
                ToolParameter(
                    name="session_id",
                    type="string",
                    description="Session ID to maintain state across executions. Use same ID to persist variables.",
                    required=False
                ),
                ToolParameter(
                    name="preferred_source_name",
                    type="string",
                    description="Optional base name for saving the generated Python source when execution succeeds. Final filename will be '<preferred_source_name>_<timestamp>.py'.",
                    required=False
                )
            ],
            returns={
                "type": "object",
                "description": "Execution results including stdout, stderr, generated files, and any returned values"
            }
        )
    
    async def execute(
        self,
        task_description: str,
        session_id: Optional[str] = None,
        preferred_source_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute Python task in sandbox via cascade code generation with retries
        
        For production, this should use Docker + Jupyter kernel + gVisor
        For development/demo, we use a simplified local execution with restrictions
        """
        try:
            if not task_description or not task_description.strip():
                raise ValueError("task_description is required and cannot be empty")

            if not session_id:
                session_id = str(uuid.uuid4())

            messages = self._build_initial_messages(task_description, session_id)
            attempt_summaries: List[Dict[str, Any]] = []
            last_execution: Optional[Dict[str, Any]] = None

            # Iterate generation/execution in a ReAct-style loop.
            for attempt_idx in range(1, self.max_attempts + 1):
                logger.info(
                    "🧠 Attempt %d/%d for session %s",
                    attempt_idx,
                    self.max_attempts,
                    session_id[:8]
                )

                generation = await self._generate_code(messages, session_id)
                code = generation["code"]
                messages.append({"role": "assistant", "content": generation["raw_response"]})

                execution = await self._execute_generated_code(code, session_id)
                execution["generated_code"] = code
                execution["code_generation_response"] = generation["raw_response"]
                execution["attempt"] = attempt_idx

                attempt_summaries.append({
                    "attempt": attempt_idx,
                    "return_code": execution.get("return_code"),
                    "success": execution.get("success"),
                    "stdout": self._truncate_text(execution.get("stdout")),
                    "stderr": self._truncate_text(execution.get("stderr")),
                    "error_report": self._truncate_text(execution.get("error_report")),
                    "files_created": execution.get("files_created", []),
                    "execution_time_ms": execution.get("execution_time_ms"),
                    "generated_code": code,
                    "code_generation_response": generation["raw_response"]
                })

                last_execution = execution

                if execution.get("success"):
                    break

                feedback_message = self._build_feedback_message(execution)
                messages.append({"role": "user", "content": feedback_message})
            else:
                logger.error(
                    "All %d attempts failed for session %s",
                    self.max_attempts,
                    session_id[:8]
                )

            if not last_execution:
                raise RuntimeError("Execution loop completed without running any attempts")

            if last_execution.get("success") and last_execution.get("generated_code"):
                artifact_path = self._persist_generated_code(
                    code=last_execution["generated_code"],
                    task_description=task_description,
                    execution_time_ms=last_execution.get("execution_time_ms"),
                    preferred_source_name=preferred_source_name
                )
                if artifact_path:
                    last_execution.setdefault("artifacts", []).append(artifact_path)

            last_execution["task_description"] = task_description
            last_execution["session_id"] = session_id
            last_execution["attempts"] = attempt_summaries
            last_execution["total_attempts"] = len(attempt_summaries)
            last_execution["max_attempts"] = self.max_attempts

            return last_execution
        except asyncio.TimeoutError:
            logger.error(f"❌ Execution timeout after {self.timeout} seconds")
            raise Exception(f"Execution timeout after {self.timeout} seconds")
        except Exception as e:
            logger.error(f"❌ Execution failed: {str(e)}")
            raise Exception(f"Execution failed: {str(e)}")

    def _build_initial_messages(self, task_description: str, session_id: str) -> List[Dict[str, str]]:
        """Initialize conversation messages for the code generation dialog"""
        system_prompt = self._get_system_prompt()
        user_content = (
            "You are preparing code for session "
            f"{session_id[:8]} inside the AgenticQuant sandbox.\n"
            "Task description:\n"
            f"{task_description.strip()}\n\n"
            "Return only the Python code block."
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

    def _get_system_prompt(self) -> str:
        """Return the base system prompt for code generation"""
        return """You are a senior quantitative developer working inside a restricted Python sandbox. Generate a complete Python script that fulfills the user's task description inside a single code block. Follow these rules strictly:

MANDATORY PRACTICES FOR DATA ANALYSIS:
1. Always print() intermediate steps and results (data loading confirmations, calculation steps, key statistics, final metrics).
2. ALWAYS save analysis results to files:
    a) Try your best to analyze data with data exploration and visualizations.
    b) Data exploration results → CSV files (e.g., df.describe().to_csv('summary_stats.csv')).
    c) Visualizations → PNG files saved with plt.savefig('plot.png', dpi=100, bbox_inches='tight') and plt.close().
    d) Choose filenames that clearly communicate content (e.g., 'processed_data.csv', 'strategy_performance.png').
3. Use print() to confirm file creation, e.g., print('✓ Saved: processed_data.csv').
4. Try your best to make quantitative conclusions. Whenever you try to make a *quantitative* conclusion, please perform data exploration and visualization.

ADDITIONAL REQUIREMENTS:
- Print progress updates and key results with clear, human-readable messages.
- Assume the current working directory is the session workspace; reference local files with relative paths.
- Respond with exactly one Python code block and no surrounding prose.
- Ensure the code is restartable and self-contained; import any required libraries.
- Avoid deprecated pandas usage (e.g., DataFrame.ix); use modern APIs.
- Use defensive programming: check for file existence when appropriate and raise informative errors.
- Write and save files strictly within the current working directory; do not create new folders or subdirectories.

**DON'T** generate any *assertion* or *test cases* inside the code, even though the task description might mention the success criteria.
"""

    def _build_feedback_message(self, execution: Dict[str, Any]) -> str:
        """Build feedback prompt for correcting a failed attempt"""
        stdout = self._truncate_text(execution.get("stdout"), limit=2000)
        stderr = self._truncate_text(execution.get("stderr"), limit=2000)
        error_report = execution.get("error_report") or ""
        error_report = self._truncate_text(error_report, limit=2000)
        generated_code = execution.get("generated_code") or ""
        code_excerpt = self._truncate_text(generated_code, limit=6000)

        stdout_block = stdout or "<empty>"
        stderr_block = stderr or "<empty>"
        error_block = f"\n\nAdditional context:\n{error_report}" if error_report else ""
        files_created = execution.get("files_created") or []
        files_section = ", ".join(files_created) if files_created else "none"

        return (
            "The previous code attempt (attempt "
            f"{execution.get('attempt')} of {self.max_attempts}) exited with return_code "
            f"{execution.get('return_code')} and did not complete successfully.\n"
            f"Files created: {files_section}.\n"
            "Please analyze the diagnostics below, incorporate any useful progress (e.g., existing files), "
            "revise the previous code rather than starting from scratch, and respond with a corrected, self-contained Python code block that follows all sandbox rules.\n\n"
            "Previous attempt code:\n"
            f"```python\n{code_excerpt}\n```\n\n"
            f"STDOUT:\n```text\n{stdout_block}\n```\n\n"
            f"STDERR:\n```text\n{stderr_block}\n```{error_block}"
        )

    def _truncate_text(self, value: Optional[str], limit: int = 2000) -> str:
        """Safely truncate long text blocks for logging/prompts"""
        if not value:
            return ""
        value = value.strip()
        if len(value) <= limit:
            return value
        return value[: max(limit - 3, 0)] + "..."

    async def _generate_code(self, messages: List[Dict[str, str]], session_id: str) -> Dict[str, str]:
        """Generate Python code for the task using the internal LLM"""

        response = await self.code_llm_client.chat_completion(
            messages=messages,
            tools=None,
            temperature=0.2,
            max_tokens=config.LLM_CODE_MAX_TOKENS
        )

        content = (response.get("content") or "").strip()
        if not content:
            raise ValueError("Code generation returned empty content")

        code = self._extract_python_code(content)
        if not code:
            raise ValueError("Could not extract Python code block from generation response")

        suffix = '...' if len(code) > 400 else ''
        logger.info(
            "Generated code for session %s...\n%s%s",
            session_id[:8],
            code,
            suffix
        )

        return {"code": code, "raw_response": content}

    def _extract_python_code(self, content: str) -> Optional[str]:
        """Extract python code block from LLM response"""
        python_block_pattern = re.compile(r"```python\s*(.*?)```", re.IGNORECASE | re.DOTALL)
        match = python_block_pattern.search(content)
        if not match:
            generic_pattern = re.compile(r"```\s*(.*?)```", re.DOTALL)
            match = generic_pattern.search(content)
        if not match:
            return None
        code = match.group(1).strip()
        return code

    async def _execute_generated_code(self, code: str, session_id: str) -> Dict[str, Any]:
        """Execute generated Python code using the existing sandbox pipeline"""
        logger.info(f"{'='*70}")
        logger.info(f"🐍 Executing Generated Python Code (session: {session_id[:8]}...)")
        logger.info(f"{'='*70}")
        logger.info(f"Working directory: {Path(self.workspace_root).resolve()}")

        execution_script = self._create_execution_script(code, session_id)
        result = await self._execute_in_subprocess(execution_script)

        logger.info(f"{'='*70}")
        logger.info(f"📊 Execution Results")
        logger.info(f"{'='*70}")
        success = result['return_code'] == 0
        status_msg = '✅ SUCCESS' if success else '❌ FAILED'
        logger.info(f"Status: {status_msg}")
        logger.info(f"Execution time: {result['execution_time_ms']:.0f}ms")

        if result.get("stdout"):
            logger.info(f"--- STDOUT ---")
            logger.info(result["stdout"])

        if result.get("stderr"):
            log_fn = logger.warning if not success else logger.info
            log_fn(f"--- STDERR ---")
            log_fn(result["stderr"])

        if result.get("files_created"):
            logger.info(f"--- FILES CREATED ---")
            for f in result["files_created"]:
                file_path = self.workspace_root / f
                if file_path.exists():
                    size = file_path.stat().st_size
                    size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                    logger.info(f"  ✓ {f} ({size_str})")
                else:
                    logger.info(f"  • {f}")

        logger.info(f"{'='*70}")

        error_report = None
        if not success:
            error_report = (
                "Python code:\n\n"
                f"{code}\n\n"
                "Execution Status:\n\nfailed\n\n"
                f"STDOUT:\n{result.get('stdout', '')}\n\n"
                f"STDERR:\n{result.get('stderr', '')}"
            )

        return {
            "session_id": session_id,
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "return_code": result["return_code"],
            "execution_time_ms": result["execution_time_ms"],
            "files_created": result.get("files_created", []),
            "success": success,
            "error_report": error_report
        }
    
    def _create_execution_script(self, code: str, session_id: str) -> str:
        """Create wrapped execution script with safety measures"""
        
        # Ensure we have absolute path
        workspace_abs = Path(self.workspace_root).resolve()
        
        # Encode user code to avoid quote escaping issues
        import base64
        code_bytes = code.encode('utf-8')
        code_b64 = base64.b64encode(code_bytes).decode('ascii')
        
        # Wrapper script that limits capabilities
        wrapper = f"""
import sys
import os
import io
from contextlib import redirect_stdout, redirect_stderr
import json
import base64

# Change working directory to workspace (using absolute path)
os.chdir('{workspace_abs}')

# Track files before execution
files_before = set(os.listdir('.'))

# Capture stdout and stderr
stdout_buffer = io.StringIO()
stderr_buffer = io.StringIO()

# Decode user code from base64 (avoids quote escaping issues)
user_code = base64.b64decode('{code_b64}').decode('utf-8')

# Execute user code
try:
    with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
        exec(user_code, {{}})
    
    # Track new files
    files_after = set(os.listdir('.'))
    new_files = list(files_after - files_before)
    
    # Output results
    result = {{
        "stdout": stdout_buffer.getvalue(),
        "stderr": stderr_buffer.getvalue(),
        "files_created": new_files,
        "return_code": 0
    }}
    print(json.dumps(result))
    
except Exception as e:
    # Build error message outside dictionary to avoid backslash in f-string
    stderr_text = stderr_buffer.getvalue()
    error_text = str(e)
    newline = chr(10)  # newline character without backslash
    
    # Combine error message parts
    if stderr_text and not stderr_text.endswith(newline):
        stderr_text += newline
    stderr_text += 'Error: ' + error_text
    
    result = {{
        "stdout": stdout_buffer.getvalue(),
        "stderr": stderr_text,
        "files_created": [],
        "return_code": 1
    }}
    print(json.dumps(result))
    sys.exit(1)
"""
        return wrapper
    
    async def _execute_in_subprocess(self, script: str) -> Dict[str, Any]:
        """Execute script in subprocess"""
        import time
        start_time = time.time()
        
        # Create temporary script file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script)
            script_path = f.name
        
        try:
            python_exec = config.SANDBOX_PYTHON_EXECUTABLE
            # Execute with timeout using configured interpreter (defaults to current venv)
            process = await asyncio.create_subprocess_exec(
                python_exec, script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace_root)
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            # Parse output
            try:
                output_str = stdout.decode('utf-8').strip()
                # Get last line which should be JSON result
                last_line = output_str.split('\n')[-1]
                result = json.loads(last_line)
                result["execution_time_ms"] = execution_time
                return result
            except:
                return {
                    "stdout": stdout.decode('utf-8'),
                    "stderr": stderr.decode('utf-8'),
                    "return_code": process.returncode,
                    "execution_time_ms": execution_time,
                    "files_created": []
                }
        finally:
            # Clean up temp file
            Path(script_path).unlink(missing_ok=True)

    def _persist_generated_code(
        self,
        code: str,
        task_description: str,
        execution_time_ms: Optional[float],
        preferred_source_name: Optional[str]
    ) -> Optional[str]:
        """Save executed code for reproducibility."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        if preferred_source_name:
            base = preferred_source_name.strip()
        else:
            base = task_description.lower()
            base = re.sub(r"[^a-z0-9]+", "_", base).strip("_")
        if not base:
            base = "python_task"
        base = base[:80]
        filename = f"{base}_{timestamp}.py"
        code_dir = self.workspace_root
        code_dir.mkdir(parents=True, exist_ok=True)
        target_path = code_dir / filename
        counter = 1
        while target_path.exists():
            target_path = code_dir / f"{base}_{timestamp}_{counter}.py"
            counter += 1
        target_path.write_text(code, encoding="utf-8")
        return str(target_path.relative_to(self.workspace_root))