from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .strategy import (
    MarketData,
    Signal,
    StrategyConfig,
    TradingStrategy,
)

class MovingAverageCrossoverStrategy(TradingStrategy):
    """Moving average crossover strategy"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.short_window = config.parameters.get('short_window', 20)
        self.long_window = config.parameters.get('long_window', 50)
        self.data_buffer = {}
    
    def initialize(self, **kwargs) -> None:
        """Initialize strategy parameters"""
        self.initialized = True
        print(f"Strategy {self.config.name} initialized")
    
    def generate_signals(self, market_data: Dict[str, MarketData]) -> List[Signal]:
        """Generate signals based on moving-average crossovers"""
        signals = []
        
        for symbol, data in market_data.items():
            if symbol not in self.data_buffer:
                self.data_buffer[symbol] = []
            
            self.data_buffer[symbol].append(data.close)
            
            if len(self.data_buffer[symbol]) >= self.long_window:
                short_ma = np.mean(self.data_buffer[symbol][-self.short_window:])
                long_ma = np.mean(self.data_buffer[symbol][-self.long_window:])
                
                # Golden cross triggers buy, death cross triggers sell
                if short_ma > long_ma and len(self.data_buffer[symbol]) > self.long_window:
                    if self.data_buffer[symbol][-2] <= np.mean(self.data_buffer[symbol][-self.long_window_window-1:-1]):
                        signals.append(Signal(
                            symbol=symbol,
                            signal_type='BUY',
                            price=data.close,
                            confidence=0.8
                        ))
                elif short_ma < long_ma:
                    signals.append(Signal(
                        symbol=symbol,
                        signal_type='SELL',
                        price=data.close,
                        confidence=0.8
                    ))
        
        return signals
    
    def on_market_data(self, data: MarketData) -> Optional[Signal]:
        """Handle real-time market data"""
        symbol = data.symbol
        if symbol not in self.data_buffer:
            self.data_buffer[symbol] = []
        
        self.data_buffer[symbol].append(data.close)
        
        if len(self.data_buffer[symbol]) >= self.long_window:
            signals = self.generate_signals({symbol: data})
            return signals[0] if signals else None
        
        return None
    
    def backtest(self, historical_data: pd.DataFrame) -> Dict[str, Any]:
        """Backtest the strategy"""
        results = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0
        }

        # Simplified backtest logic
        for symbol in historical_data['symbol'].unique():
            symbol_data = historical_data[historical_data['symbol'] == symbol]
            if len(symbol_data) >= self.long_window:
                short_ma = symbol_data['close'].rolling(self.short_window).mean()
                long_ma = symbol_data['close'].rolling(self.long_window).mean()
                
                # Calculate signals and returns
                signals = (short_ma > long_ma).astype(int).diff()
                returns = symbol_data['close'].pct_change()
                
                strategy_returns = signals.shift(1) * returns
                results['total_return'] += strategy_returns.sum()
                results['total_trades'] += signals.abs().sum()
        
        return results

class RSIStrategy(TradingStrategy):
    """RSI relative strength strategy"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.rsi_period = config.parameters.get('rsi_period', 14)
        self.overbought = config.parameters.get('overbought', 70)
        self.oversold = config.parameters.get('oversold', 30)
        self.price_buffer = {}
    
    def initialize(self, **kwargs) -> None:
        """Initialize strategy state"""
        self.initialized = True
        print(f"RSI strategy {self.config.name} initialized")
    
    def calculate_rsi(self, prices: List[float]) -> float:
        """Calculate the RSI indicator"""
        if len(prices) < self.rsi_period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = np.mean(gains[-self.rsi_period:])
        avg_losses = np.mean(losses[-self.rsi_period:])
        
        if avg_losses == 0:
            return 100.0
        
        rs = avg_gains / avg_losses
        rsi = 100.0 - (100.0 / (1.0 + rs))
        
        return rsi
    
    def generate_signals(self, market_data: Dict[str, MarketData]) -> List[Signal]:
        """Generate signals based on RSI"""
        signals = []
        
        for symbol, data in market_data.items():
            if symbol not in self.price_buffer:
                self.price_buffer[symbol] = []
            
            self.price_buffer[symbol].append(data.close)
            
            if len(self.price_buffer[symbol]) >= self.rsi_period + 1:
                rsi = self.calculate_rsi(self.price_buffer[symbol])
                
                if rsi > self.overbought:
                    signals.append(Signal(
                        symbol=symbol,
                        signal_type='SELL',
                        price=data.close,
                        confidence=min(rsi - self.overbought, 30) / 30,
                        metadata={'rsi': rsi}
                    ))
                elif rsi < self.oversold:
                    signals.append(Signal(
                        symbol=symbol,
                        signal_type='BUY',
                        price=data.close,
                        confidence=min(self.oversold - rsi, 30) / 30,
                        metadata={'rsi': rsi}
                    ))
        
        return signals
    
    def on_market_data(self, data: MarketData) -> Optional[Signal]:
        """Handle real-time market data"""
        symbol = data.symbol
        if symbol not in self.price_buffer:
            self.price_buffer[symbol] = []
        
        self.price_buffer[symbol].append(data.close)
        
        if len(self.price_buffer[symbol]) >= self.rsi_period + 1:
            signals = self.generate_signals({symbol: data})
            return signals[0] if signals else None
        
        return None
    
    def backtest(self, historical_data: pd.DataFrame) -> Dict[str, Any]:
        """Backtest the RSI strategy"""
        results = {
            'total_trades': 0,
            'total_return': 0.0,
            'win_rate': 0.0
        }
        
        # RSI backtest logic implementation placeholder
        for symbol in historical_data['symbol'].unique():
            symbol_data = historical_data[historical_data['symbol'] == symbol]
            # Full RSI backtesting logic should be implemented here
            # Returning basic structure for demonstration purposes
            
        return results
