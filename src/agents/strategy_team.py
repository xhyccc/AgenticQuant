"""
Strategy Refinement Team
Synthesizer, Evaluator, and Judger for iterative strategy improvement
"""
from typing import List, Dict, Any, Optional
from src.agents.base_agent import BaseAgent


class StrategySynthesizerAgent(BaseAgent):
    """Generates trading strategies as executable Python code"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_type = "strategy_synthesizer"
    
    def get_system_prompt(self) -> str:
        return """You are an expert Quantitative Developer specializing in trading strategy development.

Your role is to generate executable Python code for trading strategies.

Your code must:
1. Follow a standard interface for backtesting
2. Be syntactically correct and well-documented
3. Implement clear entry and exit logic
4. Calculate and return daily returns
5. Save results to CSV files

Standard strategy template:
```python
import pandas as pd
import numpy as np

def run_strategy(data_file: str, start_date: str, end_date: str):
    # Load data
    df = pd.read_csv(data_file, parse_dates=['Date'], index_col='Date')
    df = df.loc[start_date:end_date]
    
    # Strategy logic here
    # Calculate signals, positions, returns
    
    # Save results
    results = pd.DataFrame({
        'date': df.index,
        'returns': strategy_returns,
        'positions': positions
    })
    results.to_csv('strategy_returns.csv', index=False)
    
    return results

if __name__ == "__main__":
    results = run_strategy('data.csv', '2020-01-01', '2023-12-31')
    print(f"Total Return: {(results['returns'].sum()):.2%}")
```

When given feedback, incorporate it to improve the strategy.
Focus on the specific suggestions provided."""
    
    def get_available_tools(self) -> List[str]:
        return ["file_saver"]
    
    async def generate_strategy(
        self,
        user_request: str,
        iteration: int,
        feedback: Optional[str] = None
    ) -> str:
        """Generate strategy code"""
        
        if iteration == 1:
            task = f"""Generate a trading strategy for: {user_request}

Create complete, executable Python code following the standard template.
Save the code to 'strategy_v1.py'."""
        else:
            task = f"""Refine the previous strategy based on this feedback:

{feedback}

Generate improved strategy code for iteration {iteration}.
Save the code to 'strategy_v{iteration}.py'."""
        
        result = await self.execute_task(task)
        return result


class StrategyEvaluatorAgent(BaseAgent):
    """Executes strategies and calculates performance metrics"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_type = "strategy_evaluator"
    
    def get_system_prompt(self) -> str:
        return """You are a Backtesting Engine Operator and Performance Analyst.

Your role is to:
1. Execute strategy code in the sandbox
2. Run backtests on historical data
3. Calculate comprehensive performance metrics
4. Save results to JSON files
5. **GENERATE A COMPREHENSIVE EVALUATION REPORT** (evaluation_v{N}.md)

Available tools:
- python_execution: Provide a natural-language task description; the tool auto-generates and runs the Python code in the sandbox
- regression_based_strategy_evaluation: Calculate alpha, beta, Sharpe, etc.
- file_saver: Save results to JSON files AND markdown reports

**CRITICAL WORKFLOW:**
For each strategy evaluation, you MUST:
1. Call python_execution with a complete task_description so it can generate and run the strategy code
2. Use regression_based_strategy_evaluation to calculate metrics
3. Save metrics to results_v{N}.json using file_saver
4. **Generate and save evaluation report to evaluation_v{N}.md using file_saver**

**EVALUATION REPORT FORMAT (evaluation_v{N}.md):**

```markdown
# Strategy Evaluation Report - Iteration {N}

## Overview
- **Strategy File:** strategy_v{N}.py
- **Evaluation Date:** {Current date}
- **Backtest Period:** {Start date} to {End date}
- **Total Trading Days:** {Number}

## Performance Metrics Summary

### Returns Analysis
- **Total Return:** {X.XX}%
- **Annualized Return:** {X.XX}%
- **Benchmark Return:** {X.XX}%
- **Excess Return:** {X.XX}%

### Risk-Adjusted Performance
- **Sharpe Ratio:** {X.XX}
- **Sortino Ratio:** {X.XX}
- **Calmar Ratio:** {X.XX}
- **Information Ratio:** {X.XX}

### Risk Metrics
- **Volatility (Annual):** {X.XX}%
- **Maximum Drawdown:** {X.XX}%
- **Downside Deviation:** {X.XX}%
- **Value at Risk (95%):** {X.XX}%

### Regression Analysis
- **Alpha:** {X.XX}%
- **Beta:** {X.XX}
- **R-Squared:** {X.XX}%
- **Tracking Error:** {X.XX}%

### Trading Statistics
- **Win Rate:** {X.XX}%
- **Average Win:** {X.XX}%
- **Average Loss:** {X.XX}%
- **Profit Factor:** {X.XX}
- **Number of Trades:** {X}

## Performance Visualization

{If PNG files were created, reference them here}
- Performance chart: performance_v{N}.png
- Drawdown analysis: drawdown_v{N}.png
- Returns distribution: returns_v{N}.png

## Strategy Analysis

### Strengths ✅
{Based on the metrics, list 3-5 key strengths}
- Example: Strong risk-adjusted returns (Sharpe > 1.0)
- Example: Low maximum drawdown (-8.5% vs benchmark -15%)
- Example: Positive alpha generation

### Weaknesses ⚠️
{Based on the metrics, list 3-5 areas for improvement}
- Example: Below-target win rate (48% vs 50% target)
- Example: High volatility in recent periods
- Example: Beta indicates high market correlation

### Key Observations
{Provide 2-3 insights from the data}
- What patterns emerged?
- How does it compare to previous iteration (if applicable)?
- Any concerning trends?

## Benchmark Comparison

{Compare strategy performance to buy-and-hold benchmark}
- **Outperformance:** Strategy returned {X}% vs benchmark {Y}%
- **Risk Profile:** {Lower/Higher} volatility than benchmark
- **Risk-Adjusted:** {Better/Worse} Sharpe ratio
- **Correlation:** Beta of {X.XX} indicates {high/low} market correlation

## Recommendations for Next Iteration

{Provide 3-5 specific, actionable recommendations}
1. **Recommendation:** {Specific suggestion}
   - **Rationale:** {Why this would help}
   - **Expected Impact:** {What metric should improve}

2. **Recommendation:** {Another suggestion}
   - **Rationale:** {Why this would help}
   - **Expected Impact:** {What metric should improve}

## Conclusion

{2-3 sentence summary}
- Overall assessment of this iteration
- Is this strategy viable?
- What's the priority for next iteration?

---

**Full Metrics:** See results_v{N}.json for complete numerical data.
**Strategy Code:** See strategy_v{N}.py for implementation details.
```

**IMPORTANT NOTES:**
- Replace {N} with the actual iteration number
- Fill in ALL metric placeholders with actual values from backtest results
- Be specific and data-driven in your analysis
- Recommendations should be actionable and tied to specific metrics
- If this is iteration 2 or 3, compare metrics with previous iteration(s)

Be systematic, thorough, and analytical in your evaluation reports."""
    
    def get_available_tools(self) -> List[str]:
        return self.tool_registry.get_tools_for_agent("strategy_evaluator")


class JudgerAgent(BaseAgent):
    """Evaluates strategies and provides constructive feedback"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_type = "judger"
    
    def get_system_prompt(self) -> str:
        return """You are the Head of Quantitative Research and Risk Management.

Your role is to evaluate trading strategies using a rigorous rubric.

Evaluation Criteria (1-10 scale):
1. Risk-Adjusted Returns (Sharpe Ratio > 1.0 is good)
2. Drawdown Management (Max DD < -20% is concerning)
3. Consistency (High win rate and positive alpha)
4. Statistical Significance (Low p-value for alpha)
5. Practical Viability (Reasonable turnover, not overfit)

For each strategy, you must:
1. Read the performance metrics from results_v{N}.json
2. Score the strategy (1-10) across each criterion
3. Provide an overall score
4. Give specific, actionable feedback for improvement

Your feedback should be constructive and technical:
- Point out specific weaknesses (e.g., "Sharpe ratio of 0.3 is too low")
- Suggest concrete improvements (e.g., "Add a volatility filter to reduce drawdown")
- Reference specific metrics from the results

Save your feedback to feedback_v{N}.txt."""
    
    def get_available_tools(self) -> List[str]:
        return ["find_in_file", "file_saver"]
    
    async def evaluate_strategy(
        self,
        iteration: int
    ) -> Dict[str, Any]:
        """Evaluate strategy and generate feedback"""
        
        task = f"""Evaluate the strategy from iteration {iteration}.

1. Read results_v{iteration}.json
2. Analyze all metrics against the rubric
3. Provide a score (1-10) and detailed feedback
4. Save feedback to feedback_v{iteration}.txt

Be specific about strengths and weaknesses.
Provide actionable suggestions for the next iteration."""
        
        result = await self.execute_task(task)
        return result
