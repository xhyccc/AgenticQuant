from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np

@dataclass
class MarketData:
    """Market data structure"""
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    additional_data: Optional[Dict[str, Any]] = None

@dataclass
class Signal:
    """Trading signal"""
    symbol: str
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    quantity: Optional[float] = None
    price: Optional[float] = None
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class StrategyConfig:
    """Strategy configuration"""
    name: str
    parameters: Dict[str, Any]
    symbols: List[str]
    risk_limits: Dict[str, float]
    execution_params: Dict[str, Any]

class TradingStrategy(ABC):
    """Abstract trading strategy interface"""
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.initialized = False
        self.performance_metrics = {}
    
    @abstractmethod
    def initialize(self, **kwargs) -> None:
        """Initialize the strategy"""
        pass
    
    @abstractmethod
    def generate_signals(self, market_data: Dict[str, MarketData]) -> List[Signal]:
        """Generate trading signals"""
        pass
    
    @abstractmethod
    def on_market_data(self, data: MarketData) -> Optional[Signal]:
        """Handle real-time market data"""
        pass
    
    @abstractmethod
    def backtest(self, historical_data: pd.DataFrame) -> Dict[str, Any]:
        """Backtest the strategy"""
        pass
    
    def update_parameters(self, parameters: Dict[str, Any]) -> None:
        """Dynamically update strategy parameters"""
        self.config.parameters.update(parameters)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Retrieve strategy performance metrics"""
        return self.performance_metrics
    
    def validate_config(self) -> bool:
        """Validate strategy configuration"""
        required_fields = ['name', 'symbols']
        return all(field in self.config.__dict__ for field in required_fields)