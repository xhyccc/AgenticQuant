"""
Planner Agent
Creates detailed, executable plans from user requests
"""
from typing import List, Dict, Any
from src.agents.base_agent import BaseAgent
from src.mcp.protocol import WorkflowPlan
import json
from datetime import datetime, timedelta, date
import re


class PlannerAgent(BaseAgent):
    """Strategic planner that decomposes user requests into actionable plans"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_type = "planner"
    
    def get_system_prompt(self) -> str:
        available_tools = self.tool_registry.get_tools_for_agent("executor")
        tools_desc = "\n".join([
            f"- {tool}: {self.tool_registry.get_tool(tool).get_definition().description}"
            for tool in available_tools
        ])
        
        return f"""You are an expert Quantitative Strategist and Project Planner.

Your role is to create detailed, step-by-step plans to address quantitative finance research requests.

Available tools for execution:
{tools_desc}

CRITICAL REQUIREMENTS FOR PLAN QUALITY:

1. **RESEARCH-FIRST WORKFLOW**: The plan MUST begin with a comprehensive online **web search** and **save** research results to a research note
    - Require use of `web_search` and `file_saver`  before any data manipulation
    - decompose the research target into multiple queries (each query subject one hypothesis to test) and do iterative search if needed
    - Capture macroeconomic backdrop, sector drivers, market sentiment, regulatory considerations, and real-time developments for the target instruments
    - When search finished, please think of the `vibe` of trading, and save findings (information for trading, analysis, and understanding) into a research note namely `research_notes.md`
    - Ground subsequent steps with the findings (saved in a file namely 'research_note.md' and cite saved research notes files)

2. **COMPREHENSIVE OBJECTIVES**: Each step's objective must be self-contained and specific
    - Include WHAT will be done (action)
    - Include WHY it's being done (purpose)
    - Leverage research findings to justify the action
    - Include concrete parameters (e.g., "20-day moving average", "2-year lookback", "daily intervals")
    - Example: ❌ "Download data" → ✅ "Assess historical macro context for AAPL by reviewing FOMC statements and sector outlook from credible sources to inform momentum strategy assumptions"

3. **SPECIFIC INPUTS**: Clearly state what each step requires
    - List exact file names if known (e.g., "AAPL_1d_2023-01-01_to_2025-01-01.csv")
    - Specify data formats (e.g., "CSV with columns: Date, Open, High, Low, Close, Volume")
    - Include parameters needed (e.g., "Trading cost: 5 bps per transaction", "Settlement convention: T+1")
    - Explicitly note when Python execution tasks must rely on existing workspace data only (no live APIs)

4. **DETAILED OUTPUTS**: Specify exactly what each step produces
    - Exact file names (e.g., "strategy_v1.py", "performance_metrics.json", "final_report.md")
    - File formats, contents, and required metrics (e.g., "Sharpe Ratio, Max Drawdown, Total Return, Win Rate, turnover-adjusted PnL")
    - Required visualizations (e.g., "PNG chart showing equity curve vs benchmark") and how they appear in downstream markdown reports
    - Use versioned filenames within the same session (e.g., results_v1.json, results_v2.json) to preserve prior outputs

5. **SELF-CONTAINED STEPS**: Each step must stand alone without ambiguous references
    - Reference specific data sources (e.g., "processed_SPY_data.csv" instead of "the dataset")
    - Reference explicit strategy artifacts (e.g., "strategy_v2.py" instead of "the strategy")
    - Carry forward critical assumptions such as trading costs and T+0/T+1 execution handling

6. **Visualization and analysis results**: Each step with `python_execution` must specify its visualization and analysis requirements
    - Include specific plots, charts, or tables to be generated
    - Specify how these visualizations will be used to interpret the results
    - Include any relevant statistical analysis or metrics to be calculated
    - Document any assumptions or limitations related to the visualizations and analyses

7. **BACKTEST CONSTRAINTS**: All backtesting and analytics must respect execution frictions
    - Trading cost assumptions (e.g., 5 bps per leg or user-specified) must be stated in objectives, inputs, and outputs
    - Explicitly define whether fills occur T+0 (same-day close) or T+1 (next-day open) and reflect that in performance calculations
    - Python execution tasks must emphasize: "Use only existing downloaded datasets within the workspace; do NOT call yfinance or any live market APIs."

8. **DELIVERABLE FORMAT**: Final reporting must be markdown-based
    - Final synthesis step produces `final_report.md`
    - The markdown should embed narrative text, display generated images, and link to supporting data artifacts stored in the workspace

9. **ADAPTIVE STRUCTURE**: Tailor plan length to the request
    - Typical modules: research discovery (1~3 steps), data understanding/prep (2-4 steps), strategy design & backtest (1-3 steps), evaluation & comparison (1-2 steps), reporting (1 step)
    - Adjust the exact number of steps per module based on problem complexity; avoid rigid templates

10. **FILE STRUCTURE INSPECTION**: Before transforming or modeling with existing files
    - Require an inspection step using `python_execution` (lightweight schema audit) or `find_in_file` to confirm headers, column data types, metadata notes, missing values, and other structural assumptions
    - Capture the inspection output (e.g., `data_structure_notes_v1.md`) and reference it explicitly in downstream steps so tasks rely on verified structure

Output your plan as a JSON array with this structure:
[
  {{
     "step_number": 1,
     "objective": "Comprehensive, self-contained objective with specific details and parameters",
     "required_tools": ["tool1", "tool2"],
     "inputs": "Detailed list of what this step needs (files, parameters, assumptions)",
     "outputs": "Specific list of what this step produces (exact file names, formats, contents, metrics)",
     "success_criteria": "Clear indicators that this step completed successfully"
  }},
  ...
]

When strategy refinement cycles are needed, include a dedicated evaluation step that compares all generated versions (e.g., strategy_v1.py vs strategy_v2.py vs strategy_v3.py) and documents which version currently performs best based on explicit metrics after accounting for trading costs and settlement assumptions.

Think step-by-step using Chain-of-Thought reasoning before finalizing the plan. Make each step comprehensive and self-contained."""
    
    def get_available_tools(self) -> List[str]:
        return []  # Planner uses pure reasoning, no tools
    
    async def create_plan(self, user_request: str) -> WorkflowPlan:
        """Create a detailed plan from user request"""
        
        task = f"""Create a detailed, comprehensive plan for the following request:

{user_request}

MINDSET: Keep a growing mindset and be curious to the external information:
- Make sure *web_search* and *file_saver* are used in the first step for discovery.
- After complete each step, immediately save findings into a workspace artifact (e.g., `step1_findings.md`).

CRITICAL: Each step must be SELF-CONTAINED and COMPREHENSIVE:
- Objective: Include specific parameters, ticker symbols, time periods, strategy details, and explicitly note trading cost + settlement assumptions (T+0 or T+1)
- Inputs: List exact files, data formats, columns, parameters needed, and emphasize that Python execution must use only existing downloaded datasets (no yfinance or live APIs)
- Outputs: Specify exact file names, formats, contents, metrics, visualizations, and how artifacts feed into downstream markdown reporting
- Outputs: Incorporate versioned filenames (e.g., *_v1, *_v2) when multiple iterations are expected within the same session so earlier artifacts remain available
- Success Criteria: Define clear completion indicators tied to measurable checks (file existence, metric ranges, research coverage)
- Adapt the number of steps to the request's scope while respecting module expectations (research discovery, data understanding, strategy design/backtest, evaluation, reporting)

ADDITIONAL DIRECTIVES:
- The plan MUST start with an in-depth online/document research step that leverages `web_search` (and other discovery tools if relevant) to capture background, real-time sentiment, macroeconomic context, and regulatory factors related to the trading target. Require saving findings into a workspace artifact (e.g., `research_notes.md`).
- For every backtesting or analytics step, specify trading cost assumptions (e.g., 5 bps per trade) and settlement timing (clarify if orders execute same-day close [T+0] or next-day open [T+1]) and ensure outputs include cost-adjusted metrics.
- When instructing Python execution, explicitly state in the inputs: "Use only the existing downloaded dataset(s) in the workspace; external market data APIs are prohibited."
- Final deliverable must be `final_report.md` that embeds narrative text, displays generated charts via `<img>` tags, and links to supporting CSV/JSON artifacts.
- Strategy refinement cycles should be consolidated into a single step that references all iterations and compares versions after accounting for costs and settlement assumptions.
- Ensure an inspection task (using `python_execution` or `find_in_file`) captures file structure, schema, column types, missing value handling, and relevant metadata (e.g., `data_structure_notes_v1.md`) before any transformations begin; cite this artifact in later steps.

MODULE GUIDANCE (flexible, do not rigidly template):
- Research discovery and note: typically 2-3 step using web_search and file_saver tools.
- Data understanding & preparation: usually 1-2 steps depending on complexity and number of datasets.
- Strategy design & implementation or analytical modeling: 1-2 steps capturing code creation and configuration details.
- Backtesting & evaluation: 1-2 steps covering execution, metric computation, cost adjustments, and benchmark comparisons.
- Reporting & handoff: 1 step producing the markdown deliverable with embedded visuals and data links.

Ensure the resulting JSON array follows the specified schema and that each step is fully self-contained."""
        
        result = await self.execute_task(task)
        
        # Parse plan from result
        try:
            # Extract JSON from response
            response = result.get("result", "")
            print(f"LLM-RESPONSE plan: {response}")
            # Find JSON array in response
            start = response.find("[")
            end = response.rfind("]") + 1
            
            if start != -1 and end > start:
                plan_json = response[start:end]
                steps = json.loads(plan_json)
            else:
                # Fallback: create basic plan structure
                steps = self._create_default_plan(user_request)
            
            plan = WorkflowPlan(
                plan_id=f"plan_{datetime.utcnow().timestamp()}",
                user_request=user_request,
                steps=steps,
                estimated_duration_minutes=len(steps) * 5
            )
            
            return plan
            
        except Exception as e:
            # Fallback to default plan
            steps = self._create_default_plan(user_request)
            return WorkflowPlan(
                plan_id=f"plan_{datetime.utcnow().timestamp()}",
                user_request=user_request,
                steps=steps
            )
    
    def _create_default_plan(self, user_request: str) -> List[Dict[str, Any]]:
        """Create a comprehensive default plan when LLM output is unusable."""
        request_type = self._determine_request_type(user_request)
        ticker = self._extract_ticker(user_request)
        strategy_descriptor = self._extract_strategy_descriptor(user_request)
        indicator = self._extract_indicator(user_request)
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=730)
        trading_days_estimate = 502
        interval = "1d"

        if request_type == "eda":
            return self._build_eda_plan(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                trading_days_estimate=trading_days_estimate,
                indicator=indicator
            )
        if request_type == "hypothesis":
            return self._build_hypothesis_plan(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                trading_days_estimate=trading_days_estimate,
                strategy_descriptor=strategy_descriptor
            )

        return self._build_strategy_plan(
            ticker=ticker,
            strategy_descriptor=strategy_descriptor,
            indicator=indicator,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            trading_days_estimate=trading_days_estimate
        )

    def _build_strategy_plan(
        self,
        ticker: str,
        strategy_descriptor: str,
        indicator: str,
        start_date: date,
        end_date: date,
        interval: str,
        trading_days_estimate: int
    ) -> List[Dict[str, Any]]:
        research_notes_filename = "research_notes.md"
        data_inventory_filename = f"{ticker}_data_inventory.json"
        processed_filename = f"processed_{ticker}_data.csv"
        stats_filename = "summary_statistics.csv"
        quality_report_filename = "data_quality_report.txt"
        strategy_results_filename = "strategy_backtest_results.csv"
        equity_curve_filename = "strategy_performance.png"
        metrics_filename = "performance_metrics.json"
        comparison_filename = "strategy_comparison.json"
        markdown_report_filename = "final_report.md"

        return [
            {
                "step_number": 1,
                "objective": f"Conduct deep-dive online research capturing macroeconomic backdrop, sector catalysts, market sentiment, and regulatory considerations relevant to {ticker} {strategy_descriptor} strategy design, saving grounded findings for later reference",
                "required_tools": ["web_search", "file_saver"],
                "inputs": "Minimum 5 up-to-date sources (within last 12 months where possible) covering macro trends, sector performance, institutional sentiment, and policy news impacting the target tickers; include search variations for market outlook, analyst commentary, and risk factors",
                "outputs": f"{research_notes_filename} summarizing key insights with citations, bullet list of market drivers, sentiment snapshot, macro themes, and regulatory notes; appended source URL list",
                "success_criteria": f"{research_notes_filename} exists with sections for Macroeconomics, Market Sentiment, Sector Drivers, Risks, Opportunities; cites ≥5 distinct credible sources with access dates"
            },
            {
                "step_number": 2,
                "objective": f"Inventory and validate existing workspace datasets covering {ticker} from {start_date} to {end_date} at {interval} intervals, then engineer {indicator} features while documenting data quality findings",
                "required_tools": ["python_execution", "file_saver"],
                "inputs": "Use only CSV files already present in workspace (e.g., workspaces/.../*.csv); task description must state 'Use only existing downloaded dataset(s); do NOT call yfinance or other live APIs'; indicator window=20 days; trading days target={trading_days_estimate}",
                "outputs": f"{data_inventory_filename} listing located datasets with date ranges/columns, {processed_filename} containing cleaned OHLCV data plus {indicator} column, {stats_filename} with descriptive stats, {quality_report_filename} recording missing data handling and assumptions",
                "success_criteria": f"{processed_filename} retains ≥{trading_days_estimate - 80} rows, {indicator} populated without NaNs, {quality_report_filename} confirms no live API calls and documents any imputations"
            },
            {
                "step_number": 3,
                "objective": f"Implement initial {strategy_descriptor} strategy logic leveraging {indicator} signals and configurable trading frictions (trading cost = 5 bps per transaction, settlement assumption = T+1), packaging executable code for reuse",
                "required_tools": ["python_execution", "file_saver"],
                "inputs": f"Dataset: {processed_filename}; Strategy parameters: indicator window=20, entry/exit rules tied to {indicator}, position sizing=100% notional, trading_cost_bps=5, settlement_convention='T+1'; task description must reiterate offline data constraint",
                "outputs": "strategy_v1.py implementing data loading, signal generation honor settlement lag, cost-adjusted PnL, and modular configuration block",
                "success_criteria": "strategy_v1.py stored in workspace, functions documented with cost and settlement parameters, dry-run executes without external data downloads"
            },
            {
                "step_number": 4,
                "objective": f"Backtest strategy_v1.py on {processed_filename} producing cost-adjusted performance metrics and visuals comparing T+1 base case versus alternative T+0 sensitivity",
                "required_tools": ["python_execution", "regression_based_strategy_evaluation", "file_saver"],
                "inputs": "Execution instructions must state to reuse existing dataset only; run two scenarios (T+1 base with 5 bps costs, T+0 sensitivity with same costs); include benchmark = buy-and-hold from processed data",
                "outputs": f"{strategy_results_filename} with scenario-labelled returns, {metrics_filename} summarizing CAGR, Sharpe, Sortino, Max Drawdown, Win Rate, turnover-adjusted PnL for each settlement assumption, {equity_curve_filename} overlaying equity curves vs benchmark",
                "success_criteria": f"{metrics_filename} reports both T+1 and T+0 rows with cost-adjusted metrics, {equity_curve_filename} displays both strategy variants and benchmark, backtest log confirms no live API usage"
            },
            {
                "step_number": 5,
                "objective": f"Synthesize evaluator and judger feedback to iterate on the {strategy_descriptor} logic (strategy_v1 → strategy_v2 → strategy_v3 if needed), ensuring each revision quantifies improvements net of trading costs and settlement effects",
                "required_tools": ["python_execution", "file_saver", "regression_based_strategy_evaluation", "find_in_file"],
                "inputs": f"Artifacts: strategy_v1.py, {processed_filename}, feedback files, cost assumptions (5 bps), settlement options (T+1 base, T+0 sensitivity); reiterate offline data constraint in execution instructions",
                "outputs": "strategy_v1.py/results_v1.json/evaluation_v1.md/feedback_v1.txt, strategy_v2.py/results_v2.json/evaluation_v2.md/feedback_v2.txt, strategy_v3.py/results_v3.json/evaluation_v3.md/feedback_v3.txt as produced, {comparison_filename} compiling key metrics across versions and settlement scenarios",
                "success_criteria": f"Each iteration records cost-adjusted metrics, {comparison_filename} highlights best-performing version with settlement context, feedback files confirm addressed comments"
            },
            {
                "step_number": 6,
                "objective": "Generate markdown deliverable summarizing research context, data preparation, strategy iterations, and performance comparisons with embedded visuals and links to supporting artifacts",
                "required_tools": ["find_in_file", "file_saver"],
                "inputs": f"Inputs: {research_notes_filename}, {processed_filename}, {metrics_filename}, {equity_curve_filename}, {comparison_filename}, evaluation and feedback docs; ensure markdown references local images and links to CSV/JSON files",
                "outputs": f"{markdown_report_filename} containing narrative sections (Executive Summary, Market Context, Data Preparation, Strategy Results, Risk Considerations, Next Steps), embedded image for {equity_curve_filename}, hyperlinks to datasets and metrics files",
                "success_criteria": f"{markdown_report_filename} exists, renders embedded chart and working hyperlinks, explicitly states recommended strategy version and settlement assumption based on cost-adjusted metrics"
            }
        ]

    def _build_eda_plan(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        interval: str,
        trading_days_estimate: int,
        indicator: str
    ) -> List[Dict[str, Any]]:
        research_notes_filename = "research_notes.md"
        cleaned_filename = f"cleaned_{ticker}_data.csv"
        stats_filename = "summary_statistics.csv"
        quality_report_filename = "data_quality_report.txt"
        eda_metrics_filename = "eda_metrics.json"
        metrics_summary_filename = "eda_metrics_summary.txt"
        visualization_prefix = f"{ticker}_eda"
        markdown_report_filename = "eda_report.md"

        return [
            {
                "step_number": 1,
                "objective": f"Compile comprehensive background research for {ticker} covering macro environment, sector performance, sentiment, and recent news to contextualize exploratory data analysis",
                "required_tools": ["web_search", "file_saver"],
                "inputs": "At least 5 reputable, recent sources spanning macro trends, sector commentary, analyst views, and risk factors; include varied queries targeting sentiment and regulatory considerations",
                "outputs": f"{research_notes_filename} summarizing macro factors, sentiment indicators, sector drivers, and risks/opportunities with cited URLs",
                "success_criteria": f"{research_notes_filename} contains dedicated sections for Macro, Sector, Sentiment, Risks, cites ≥5 sources, and notes data relevance timeframe"
            },
            {
                "step_number": 2,
                "objective": f"Identify and cleanse existing workspace datasets for {ticker} ({start_date} to {end_date}, interval {interval}), recording data quality decisions while engineering {indicator}",
                "required_tools": ["python_execution", "file_saver"],
                "inputs": "Use only pre-downloaded CSVs within workspace (e.g., workspaces/.../*.csv); task description must forbid live API usage; cleaning rules: forward-fill gaps ≤3 days, drop rows missing Close; indicator window=20",
                "outputs": f"{cleaned_filename} with OHLCV plus {indicator}, {stats_filename} capturing descriptive statistics, {quality_report_filename} documenting located files, coverage, missing data handling, and confirmation of no external downloads",
                "success_criteria": f"{cleaned_filename} retains ≥{trading_days_estimate - 100} observations, {indicator} contains no NaNs, {quality_report_filename} explicitly confirms offline-only data usage"
            },
            {
                "step_number": 3,
                "objective": f"Compute exploratory analytics (returns distribution, rolling volatility, volume dynamics, correlations) on {cleaned_filename} to uncover structural patterns",
                "required_tools": ["python_execution", "file_saver"],
                "inputs": f"Dataset: {cleaned_filename}; metrics: daily returns, rolling 20-day volatility, autocorrelation lags (1,5,20), volume z-scores, correlation matrix between price changes, volume, {indicator}; execution instructions must restate offline data constraint",
                "outputs": f"{eda_metrics_filename} containing computed metrics and correlation matrices, {metrics_summary_filename} describing notable patterns and anomalies",
                "success_criteria": f"All computed metrics stored without NaNs, {metrics_summary_filename} highlights ≥3 insights referencing quantitative evidence"
            },
            {
                "step_number": 4,
                "objective": f"Produce visualization set showcasing price vs {indicator}, returns distribution, rolling volatility, and volume behavior to support qualitative assessment",
                "required_tools": ["python_execution", "file_saver"],
                "inputs": f"Source data: {cleaned_filename}; charts: price+{indicator} line, returns histogram, rolling volatility line, volume bar with z-score overlay; reiterate offline data constraint in task description",
                "outputs": f"PNG files {visualization_prefix}_trend.png, {visualization_prefix}_returns_hist.png, {visualization_prefix}_volatility.png, {visualization_prefix}_volume.png with labeled axes and legends",
                "success_criteria": "All PNGs generated successfully, visually clear with titles, stored paths logged"
            },
            {
                "step_number": 5,
                "objective": "Assemble markdown summary communicating research context, data quality decisions, key EDA findings, and visual evidence with linked artifacts for follow-up investigations",
                "required_tools": ["find_in_file", "file_saver"],
                "inputs": f"Inputs: {research_notes_filename}, {stats_filename}, {quality_report_filename}, {eda_metrics_filename}, {metrics_summary_filename}, visualization PNGs; ensure Markdown embeds images via ![image](<img>) and links to CSV/JSON resources",
                "outputs": f"{markdown_report_filename} containing sections (Context, Data Audit, Exploratory Metrics, Visual Insights, Recommendations) with embedded charts and hyperlinks to supporting files",
                "success_criteria": f"{markdown_report_filename} exists, renders embedded images, links resolve to workspace files, includes actionable recommendations aligned with findings"
            }
        ]

    def _build_hypothesis_plan(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        interval: str,
        trading_days_estimate: int,
        strategy_descriptor: str
    ) -> List[Dict[str, Any]]:
        research_notes_filename = "research_notes.md"
        prepared_filename = f"prepared_{ticker}_dataset.csv"
        hypothesis_doc = "hypothesis_design.md"
        test_results_filename = "hypothesis_test_results.json"
        visualization_filename = f"{ticker}_hypothesis_diagnostics.png"
        conclusion_filename = "hypothesis_conclusions.md"
        quality_report_filename = "data_quality_report.md"

        return [
            {
                "step_number": 1,
                "objective": f"Gather comprehensive background research for {ticker} focusing on macro trends, sector dynamics, sentiment, and regulatory factors that could influence {strategy_descriptor} hypotheses",
                "required_tools": ["web_search", "file_saver"],
                "inputs": "Use ≥5 recent authoritative sources covering macro, sentiment, industry outlook, and risk considerations; include varied queries encompassing hypothesis topic",
                "outputs": f"{research_notes_filename} detailing contextual insights with citations supporting hypothesis framing",
                "success_criteria": f"{research_notes_filename} includes sections for Macro Context, Sentiment, Sector Drivers, Regulatory/Risk Notes, with ≥5 cited sources"
            },
            {
                "step_number": 2,
                "objective": f"Assemble feature-ready dataset for hypothesis testing using only existing workspace CSVs spanning {start_date} to {end_date} at {interval} intervals, documenting data quality decisions",
                "required_tools": ["python_execution", "file_saver"],
                "inputs": "Task description must state: 'Use only downloaded dataset(s); no live API access permitted'; engineering requirements: daily returns, 20-day and 50-day moving averages, rolling 20-day volatility, volume z-scores",
                "outputs": f"{prepared_filename} with engineered features, {quality_report_filename} summarizing source files, coverage, missing data handling, and confirmation of offline-only approach",
                "success_criteria": f"{prepared_filename} retains ≥{trading_days_estimate - 100} rows with no missing feature values, {quality_report_filename} records data lineage and quality checks"
            },
            {
                "step_number": 3,
                "objective": "Formulate statistical hypotheses, select appropriate tests, and document methodology including treatment of trading frictions where relevant",
                "required_tools": ["find_in_file", "file_saver"],
                "inputs": f"Context from {research_notes_filename}, dataset summary from {quality_report_filename}, significance level α=0.05, note any trading cost or settlement assumptions influencing expected effects",
                "outputs": f"{hypothesis_doc} outlining null/alternative hypotheses, test selection (e.g., t-test, Mann-Whitney, variance ratio), assumptions, and evaluation criteria",
                "success_criteria": f"{hypothesis_doc} includes hypothesis statements, statistical test plan, assumptions validation checklist, and links back to contextual research"
            },
            {
                "step_number": 4,
                "objective": "Execute planned statistical tests, compute effect sizes, and visualize diagnostics while ensuring reproducibility under offline data constraints",
                "required_tools": ["python_execution", "file_saver"],
                "inputs": f"Dataset: {prepared_filename}, Plan: {hypothesis_doc}; tests to include mean return t-test, volatility comparison, distribution shift analysis; reiterate offline-only data rule in task description",
                "outputs": f"{test_results_filename} capturing statistics, p-values, confidence intervals, effect sizes; {visualization_filename} summarizing diagnostic plots (QQ plots, rolling stats)",
                "success_criteria": f"{test_results_filename} lists all tests with interpretation fields populated, {visualization_filename} generated without errors, execution logs confirm no live data calls"
            },
            {
                "step_number": 5,
                "objective": "Synthesize conclusions in interactive markdown summarizing hypothesis outcomes, practical implications, limitations, and recommended next experiments",
                "required_tools": ["find_in_file", "file_saver"],
                "inputs": f"Inputs: {research_notes_filename}, {hypothesis_doc}, {test_results_filename}, {visualization_filename}; Markdown must embed diagnostics via ![image](<img>) and link to dataset/features/notes",
                "outputs": f"{conclusion_filename} with sections (Context, Hypotheses, Results, Practical Interpretation, Limitations, Next Steps) including embedded diagnostics and hyperlinks",
                "success_criteria": f"{conclusion_filename} exists, renders embedded visualization, references key statistics, and clearly states accept/reject decisions for each hypothesis"
            }
        ]

    def _determine_request_type(self, user_request: str) -> str:
        lowered = user_request.lower()
        hypothesis_keywords = ["hypothesis", "test", "significance", "statistical", "p-value"]
        eda_keywords = ["explore", "eda", "visual", "dashboard", "pattern", "insight", "analysis"]
        strategy_keywords = ["strategy", "trading", "momentum", "mean reversion", "alpha", "portfolio", "backtest"]

        if any(keyword in lowered for keyword in hypothesis_keywords):
            return "hypothesis"
        if any(keyword in lowered for keyword in eda_keywords):
            return "eda"
        if any(keyword in lowered for keyword in strategy_keywords):
            return "strategy"
        return "strategy"

    def _extract_ticker(self, user_request: str) -> str:
        match = re.findall(r"\b[A-Z]{2,5}\b", user_request)
        return match[0] if match else "SYMBOL"

    def _extract_indicator(self, user_request: str) -> str:
        indicator_match = re.search(r"(\d+[- ]?(day|period)[- ]?(MA|EMA|SMA))", user_request, re.IGNORECASE)
        if indicator_match:
            return indicator_match.group(1).replace(" ", "-")
        return "20-day moving average"

    def _extract_strategy_descriptor(self, user_request: str) -> str:
        keywords = [
            ("momentum", "momentum"),
            ("mean reversion", "mean reversion"),
            ("pairs", "pairs trading"),
            ("volatility", "volatility-based"),
            ("trend", "trend-following")
        ]
        lowered = user_request.lower()
        for phrase, descriptor in keywords:
            if phrase in lowered:
                return descriptor
        return "quantitative"
