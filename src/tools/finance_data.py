"""
Financial Data Downloader Tool using yfinance
"""
from typing import Any, List, Dict, Optional
from src.tools.base import BaseTool
from src.mcp.protocol import ToolDefinition, ToolParameter
from pathlib import Path
import yfinance as yf
import pandas as pd
from datetime import datetime
from io import StringIO
import requests


class FinanceDataDownloaderTool(BaseTool):
    """Download financial market data"""
    
    def __init__(self, workspace_root: Path):
        super().__init__()
        self.name = "finance_data_downloader"
        self.workspace_root = workspace_root
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description="Downloads historical financial market data (OHLCV: Open, High, Low, Close, Volume) for a list of stock tickers over a specified date range. Saves data as CSV files.",
            parameters=[
                ToolParameter(
                    name="tickers",
                    type="array",
                    description="List of stock ticker symbols (e.g., ['AAPL', 'MSFT', 'SPY'])",
                    required=True
                ),
                ToolParameter(
                    name="start_date",
                    type="string",
                    description="Start date in YYYY-MM-DD format",
                    required=True
                ),
                ToolParameter(
                    name="end_date",
                    type="string",
                    description="End date in YYYY-MM-DD format",
                    required=True
                ),
                ToolParameter(
                    name="interval",
                    type="string",
                    description="Data interval: '1d' (daily), '1wk' (weekly), '1mo' (monthly)",
                    required=False,
                    default="1d",
                    enum=["1d", "1wk", "1mo", "1h", "5m"]
                )
            ],
            returns={
                "type": "object",
                "description": "File paths of downloaded CSV files and summary statistics"
            }
        )
    
    async def execute(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> Dict[str, Any]:
        """Download financial data"""
        try:
            downloaded_files: List[str] = []
            summary: Dict[str, Any] = {}
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

            for ticker in tickers:
                data_source = "yfinance"
                data = pd.DataFrame()
                yf_error: Optional[str] = None

                try:
                    data = yf.download(
                        ticker,
                        start=start_date,
                        end=end_date,
                        interval=interval,
                        progress=False
                    )
                except Exception as exc:
                    yf_error = str(exc)

                if data.empty:
                    # Attempt fallback to Stooq
                    data_source = "stooq"
                    try:
                        url = f"https://stooq.com/q/d/l/?s={ticker.lower()}.us&i=d"
                        response = requests.get(url, timeout=15)
                        response.raise_for_status()
                        stooq_df = pd.read_csv(StringIO(response.text))
                        stooq_df["Date"] = pd.to_datetime(stooq_df["Date"])
                        stooq_df = stooq_df.sort_values("Date")
                        mask = (stooq_df["Date"].dt.date >= start_dt) & (stooq_df["Date"].dt.date <= end_dt)
                        data = stooq_df.loc[mask].reset_index(drop=True)
                        data = data.rename(columns=str.title)
                        if "Close" not in data.columns:
                            raise ValueError("Stooq response missing expected columns")
                    except Exception as fallback_exc:
                        summary[ticker] = {
                            "status": "failed",
                            "error": yf_error or str(fallback_exc)
                        }
                        continue

                if data.empty:
                    summary[ticker] = {"status": "failed", "error": yf_error or "No data available"}
                    continue

                # Normalize to MarketData schema
                if not data.index.name:
                    data.index.name = "Date"
                data_reset = data.reset_index()
                timestamp_col = None
                for candidate in ("Date", "Datetime", data.index.name):
                    if candidate in data_reset.columns:
                        timestamp_col = candidate
                        break
                if timestamp_col is None:
                    timestamp_col = data_reset.columns[0]
                data_reset = data_reset.rename(columns={timestamp_col: "timestamp"})

                column_mapping = {
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Adj Close": "adj_close",
                    "Volume": "volume"
                }
                data_reset = data_reset.rename(columns={k: v for k, v in column_mapping.items() if k in data_reset.columns})
                data_reset["symbol"] = ticker
                base_columns = ["timestamp", "symbol", "open", "high", "low", "close", "volume"]
                missing_required = [col for col in base_columns if col not in data_reset.columns]
                if missing_required:
                    summary[ticker] = {
                        "status": "failed",
                        "error": f"Missing required columns after normalization: {missing_required}"
                    }
                    continue

                additional_cols = [col for col in data_reset.columns if col not in base_columns]
                data_reset = data_reset[base_columns + additional_cols]

                # Ensure timestamp column is normalized to naive UTC timestamps
                timestamps = pd.to_datetime(data_reset["timestamp"], utc=True, errors="coerce")
                data_reset["timestamp"] = timestamps.dt.tz_localize(None)
                if data_reset["timestamp"].isnull().any():
                    summary[ticker] = {
                        "status": "failed",
                        "error": "Unable to parse timestamps into MarketData schema"
                    }
                    continue

                filename = f"{ticker}_{interval}_{start_date}_to_{end_date}.csv"
                file_path = self.workspace_root / filename
                data_reset.to_csv(file_path, index=False)
                downloaded_files.append(str(file_path))

                first_date = data_reset["timestamp"].iloc[0]
                last_date = data_reset["timestamp"].iloc[-1]
                first_str = first_date.strftime("%Y-%m-%d")
                last_str = last_date.strftime("%Y-%m-%d")

                summary[ticker] = {
                    "status": "success",
                    "rows": len(data_reset),
                    "start_date": first_str,
                    "end_date": last_str,
                    "columns": list(data_reset.columns),
                    "data_source": data_source,
                    "file_path": str(file_path)
                }

            return {
                "result": {
                    "total_tickers": len(tickers),
                    "successful_downloads": len(downloaded_files),
                    "summary": summary
                },
                "artifacts": downloaded_files
            }
        except Exception as e:
            raise Exception(f"Failed to download financial data: {str(e)}")
