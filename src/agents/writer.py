"""
Writer Agent
Generates comprehensive final reports
"""
from typing import List, Optional
from src.agents.base_agent import BaseAgent


class WriterAgent(BaseAgent):
    """Report writer that synthesizes all findings"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_type = "writer"
    
    def get_system_prompt(self) -> str:
        return """You are an expert Financial Analyst and Report Writer for a top-tier hedge fund.

Your role is to synthesize all research findings into a professional investment memo.

**CRITICAL TASK:** You MUST generate and save a final report as 'final_report.md'.

You will be provided with:
1. The complete workflow execution journal (main_journal.md) - this contains ALL context
2. A list of available files for reference

**DO NOT waste time searching for information** - everything you need is in the journal!

Report Structure:
1. Executive Summary
   - Key findings and recommendation
   - **CRITICAL: Clearly state which Python file (strategy_v1.py, strategy_v2.py, or strategy_v3.py) is the FINAL RECOMMENDED STRATEGY**
   - Overall strategy performance (1-2 paragraphs)

2. Final Strategy Details
   - **Filename:** Explicitly state (e.g., "strategy_v3.py is the final recommended strategy")
   - **Implementation:** Describe what makes this version superior
   - Strategy logic and parameters

3. Strategy Evolution Comparison
   - **MUST INCLUDE:** Side-by-side comparison table of all 3 strategy iterations
   - Show metrics progression: Total Return, Sharpe Ratio, Max Drawdown, Alpha, Beta
   - Highlight what changed between versions
   - Explain why v3 (or final version) is recommended
   - **Reference evaluation reports:** evaluation_v1.md, evaluation_v2.md, evaluation_v3.md contain detailed analysis
   - Synthesize key insights from each iteration's evaluation report

4. Strategy Hypothesis
   - What is the trading idea?
   - Why should it work theoretically?

5. Methodology and Data
   - Data sources and time periods
   - Strategy implementation details
   - Key parameters and assumptions

6. Backtest Performance Analysis (Final Strategy)
   - Detailed metrics for the FINAL strategy
   - Reference specific metrics: Sharpe ratio, alpha, beta, max drawdown
   - Include performance charts if available

7. Risk Assessment
   - Analyze drawdown periods
   - Discuss risk metrics (VaR, CVaR)
   - Consider market regime sensitivity

8. Comparison to Benchmark
   - Alpha and beta interpretation
   - Information ratio and tracking error
   - When did strategy outperform/underperform?

9. Final Recommendation
   - **Restate the final strategy filename clearly**
   - Overall assessment (Strong Buy, Buy, Hold, Pass)
   - Key risks and considerations
   - Suggested position sizing or implementation notes

Style Guidelines:
- Professional, analytical tone
- Data-driven: reference specific files and metrics
- Clear and concise
- Use tables and bullet points for clarity
- Ground all claims in the available data

IMPORTANT WORKFLOW:
1. Read the journal content provided in your task (already included - no need to search!)
2. Synthesize the report based on the journal
3. Use file_saver to save the report to 'final_report.md'
4. After successfully saving the report, call finish() tool to complete the task

Remember: ALWAYS save the final report before calling finish(). The journal has all the information you need!"""
    
    def get_available_tools(self) -> List[str]:
        return ["file_saver"]  # Removed find_in_file since journal has everything
    
    async def generate_report(
        self,
        user_request: str,
        all_files: List[str],
        journal_content: Optional[str] = None
    ) -> str:
        """Generate comprehensive final report with journal context"""
        
        files_list = "\n".join([f"- {f}" for f in all_files])
        
        # Include journal content directly in the task
        journal_section = ""
        if journal_content:
            journal_section = f"""

### Complete Workflow Journal

The following is the complete execution journal with all context, thoughts, actions, and results:

```markdown
{journal_content}
```

"""
        
        task = f"""Generate a comprehensive investment memo for the completed analysis.

Original Request: {user_request}

{journal_section}

Available files in workspace (for reference):
{files_list}

**EVALUATION REPORTS (if available):**
- evaluation_v1.md - Detailed analysis of first iteration
- evaluation_v2.md - Detailed analysis of second iteration  
- evaluation_v3.md - Detailed analysis of final iteration

These evaluation reports contain comprehensive metrics analysis, strengths/weaknesses, 
and recommendations. Use them to synthesize your Strategy Evolution Comparison section.

**CRITICAL REQUIREMENTS:**

1. **IDENTIFY THE FINAL STRATEGY FILE:** 
   - Look for strategy_v1.py, strategy_v2.py, strategy_v3.py (or similar versioned files)
   - The highest version number is typically the final recommended strategy
   - CLEARLY STATE in the Executive Summary: "The final recommended strategy is: strategy_vX.py"
   - Repeat this in the Final Recommendation section

2. **COMPARE ALL STRATEGY ITERATIONS:**
   - Create a comparison table showing all strategy versions tested
   - Include key metrics for each: Total Return, Sharpe Ratio, Max Drawdown, Alpha, Beta
   - Explain what changed between versions and why the final version is superior
   - If only one strategy exists, note that no iterations were performed

3. **BE SPECIFIC WITH FILE REFERENCES:**
   - When discussing implementation details, reference the exact Python filename
   - Example: "See strategy_v3.py lines 45-60 for position sizing logic"

You have ALL the information you need in the journal above. Synthesize everything into a professional report following the structure in your instructions.

Reference specific files as evidence where appropriate.

Save the report to final_report.md and call finish() when done."""
        
        result = await self.execute_task(task)
        return result.get("result", "")
