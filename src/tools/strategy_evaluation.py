"""
Regression-based Strategy Evaluation Tool
"""
from typing import Any, Dict
from src.tools.base import BaseTool
from src.mcp.protocol import ToolDefinition, ToolParameter
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats


class RegressionBasedStrategyEvaluationTool(BaseTool):
    """Evaluate trading strategy performance using regression analysis"""
    
    def __init__(self, workspace_root: Path):
        super().__init__()
        self.name = "regression_based_strategy_evaluation"
        self.workspace_root = workspace_root
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description="Evaluates a trading strategy's performance relative to a benchmark using regression analysis. Calculates alpha, beta, Sharpe ratio, maximum drawdown, and other key metrics.",
            parameters=[
                ToolParameter(
                    name="strategy_returns_file",
                    type="string",
                    description="Path to CSV file containing strategy returns (must have 'date' and 'returns' columns)",
                    required=True
                ),
                ToolParameter(
                    name="benchmark_returns_file",
                    type="string",
                    description="Path to CSV file containing benchmark returns (must have 'date' and 'returns' columns)",
                    required=True
                ),
                ToolParameter(
                    name="risk_free_rate",
                    type="number",
                    description="Annual risk-free rate (default: 0.02 for 2%)",
                    required=False,
                    default=0.02
                )
            ],
            returns={
                "type": "object",
                "description": "Performance metrics including alpha, beta, Sharpe ratio, drawdown, etc."
            }
        )
    
    async def execute(
        self,
        strategy_returns_file: str,
        benchmark_returns_file: str,
        risk_free_rate: float = 0.02
    ) -> Dict[str, Any]:
        """Evaluate strategy performance"""
        try:
            # Load data
            strategy_path = self.workspace_root / strategy_returns_file
            benchmark_path = self.workspace_root / benchmark_returns_file
            
            strategy_df = pd.read_csv(strategy_path, parse_dates=['date'])
            benchmark_df = pd.read_csv(benchmark_path, parse_dates=['date'])
            
            strategy_returns = strategy_df['returns'].values
            benchmark_returns = benchmark_df['returns'].values
            
            # Ensure same length
            min_len = min(len(strategy_returns), len(benchmark_returns))
            strategy_returns = strategy_returns[:min_len]
            benchmark_returns = benchmark_returns[:min_len]
            
            # Calculate regression: strategy = alpha + beta * benchmark + error
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                benchmark_returns, strategy_returns
            )
            
            beta = slope
            alpha = intercept * 252  # Annualized alpha (assuming daily returns)
            
            # Calculate performance metrics
            metrics = {
                # Regression metrics
                "alpha": float(alpha),
                "beta": float(beta),
                "r_squared": float(r_value ** 2),
                "p_value": float(p_value),
                
                # Return metrics
                "total_return": float(np.prod(1 + strategy_returns) - 1),
                "annualized_return": float(np.mean(strategy_returns) * 252),
                "volatility": float(np.std(strategy_returns) * np.sqrt(252)),
                
                # Risk-adjusted metrics
                "sharpe_ratio": self._calculate_sharpe_ratio(
                    strategy_returns, risk_free_rate
                ),
                "sortino_ratio": self._calculate_sortino_ratio(
                    strategy_returns, risk_free_rate
                ),
                "information_ratio": self._calculate_information_ratio(
                    strategy_returns, benchmark_returns
                ),
                
                # Drawdown metrics
                "max_drawdown": self._calculate_max_drawdown(strategy_returns),
                "max_drawdown_duration": self._calculate_max_drawdown_duration(
                    strategy_returns
                ),
                
                # Win/Loss metrics
                "win_rate": float(np.sum(strategy_returns > 0) / len(strategy_returns)),
                "avg_win": float(np.mean(strategy_returns[strategy_returns > 0]) 
                               if np.any(strategy_returns > 0) else 0),
                "avg_loss": float(np.mean(strategy_returns[strategy_returns < 0])
                                if np.any(strategy_returns < 0) else 0),
                
                # Benchmark comparison
                "excess_return": float(np.mean(strategy_returns - benchmark_returns) * 252),
                "tracking_error": float(np.std(strategy_returns - benchmark_returns) * np.sqrt(252)),
                
                # Additional stats
                "skewness": float(stats.skew(strategy_returns)),
                "kurtosis": float(stats.kurtosis(strategy_returns)),
                "var_95": float(np.percentile(strategy_returns, 5)),
                "cvar_95": float(np.mean(strategy_returns[strategy_returns <= np.percentile(strategy_returns, 5)])),
            }
            
            return metrics
            
        except Exception as e:
            raise Exception(f"Strategy evaluation failed: {str(e)}")
    
    def _calculate_sharpe_ratio(
        self,
        returns: np.ndarray,
        risk_free_rate: float
    ) -> float:
        """Calculate Sharpe ratio"""
        excess_returns = returns - (risk_free_rate / 252)
        if np.std(excess_returns) == 0:
            return 0.0
        return float(np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252))
    
    def _calculate_sortino_ratio(
        self,
        returns: np.ndarray,
        risk_free_rate: float
    ) -> float:
        """Calculate Sortino ratio (downside deviation)"""
        excess_returns = returns - (risk_free_rate / 252)
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) == 0 or np.std(downside_returns) == 0:
            return 0.0
        return float(np.mean(excess_returns) / np.std(downside_returns) * np.sqrt(252))
    
    def _calculate_information_ratio(
        self,
        strategy_returns: np.ndarray,
        benchmark_returns: np.ndarray
    ) -> float:
        """Calculate information ratio"""
        excess_returns = strategy_returns - benchmark_returns
        tracking_error = np.std(excess_returns)
        if tracking_error == 0:
            return 0.0
        return float(np.mean(excess_returns) / tracking_error * np.sqrt(252))
    
    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return float(np.min(drawdown))
    
    def _calculate_max_drawdown_duration(self, returns: np.ndarray) -> int:
        """Calculate maximum drawdown duration in days"""
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        
        in_drawdown = cumulative < running_max
        durations = []
        current_duration = 0
        
        for is_dd in in_drawdown:
            if is_dd:
                current_duration += 1
            else:
                if current_duration > 0:
                    durations.append(current_duration)
                current_duration = 0
        
        if current_duration > 0:
            durations.append(current_duration)
        
        return int(max(durations)) if durations else 0
