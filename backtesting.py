"""
Backtesting Module for Trading Strategies
Supports all strategies with comprehensive performance metrics
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from strategy import Strategy, MovingAverageStrategy, RSIMomentumStrategy, BollingerBandsStrategy, EMAStrategy, EMARibbonStrategy, EMA200Strategy
try:
    from chart_patterns import ChartPatternStrategy
    CHART_PATTERNS_AVAILABLE = True
except ImportError:
    CHART_PATTERNS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Lazy import for advanced strategies to avoid dependency issues
def _import_advanced_strategies():
    """Lazy import for advanced strategies"""
    try:
        from advanced_strategies import NewsMomentumStrategy, MeanReversionStrategy, CryptoOnChainStrategy, MLBasedStrategy
        return NewsMomentumStrategy, MeanReversionStrategy, CryptoOnChainStrategy, MLBasedStrategy
    except ImportError as e:
        logger.warning(f"Advanced strategies not available: {e}")
        return None, None, None, None


class BacktestResult:
    """Backtest results container"""
    
    def __init__(self):
        self.trades = []
        self.equity_curve = []
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        self.max_drawdown = 0.0
        self.max_drawdown_percent = 0.0
        self.sharpe_ratio = 0.0
        self.win_rate = 0.0
        self.profit_factor = 0.0
        self.avg_win = 0.0
        self.avg_loss = 0.0
        self.largest_win = 0.0
        self.largest_loss = 0.0
        
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'total_pnl': self.total_pnl,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_percent': self.max_drawdown_percent,
            'sharpe_ratio': self.sharpe_ratio,
            'profit_factor': self.profit_factor,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'largest_win': self.largest_win,
            'largest_loss': self.largest_loss,
            'trades': self.trades,
            'equity_curve': self.equity_curve
        }


class Backtester:
    """Backtesting engine for trading strategies"""
    
    def __init__(self, initial_capital: float = 100000.0, commission: float = 0.001):
        """
        Initialize backtester
        
        Args:
            initial_capital: Starting capital
            commission: Commission rate per trade (0.001 = 0.1%)
        """
        self.initial_capital = initial_capital
        self.commission = commission
        
        # Import advanced strategies lazily
        NewsMomentumStrategy, MeanReversionStrategy, CryptoOnChainStrategy, MLBasedStrategy = _import_advanced_strategies()
        
        self.strategies = {
            'Moving Average': MovingAverageStrategy,
            'RSI Momentum': RSIMomentumStrategy,
            'Bollinger Bands': BollingerBandsStrategy,
            'EMA Crossover': EMAStrategy,
            'EMA Ribbon': EMARibbonStrategy,
            'EMA 200 Dynamic S/R': EMA200Strategy,
        }
        
        # Add chart patterns if available
        if CHART_PATTERNS_AVAILABLE:
            self.strategies['Chart Patterns'] = ChartPatternStrategy
        
        # Add advanced strategies if available
        if NewsMomentumStrategy is not None:
            self.strategies['News Momentum'] = NewsMomentumStrategy
        if MeanReversionStrategy is not None:
            self.strategies['Mean Reversion'] = MeanReversionStrategy
        if CryptoOnChainStrategy is not None:
            self.strategies['Crypto On-Chain'] = CryptoOnChainStrategy
        if MLBasedStrategy is not None:
            self.strategies['ML-Based'] = MLBasedStrategy
    
    def normalize_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Normalize data format for backtesting"""
        df = data.copy()
        
        # Ensure required columns exist
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            # Try to convert from list format
            if len(df.columns) >= 6:
                df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume'] + list(df.columns[6:])
        
        # Ensure timestamp is datetime
        if 'timestamp' in df.columns:
            if df['timestamp'].dtype != 'datetime64[ns]':
                if isinstance(df['timestamp'].iloc[0], (int, float)):
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', errors='coerce')
                else:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        else:
            # Create index-based timestamp
            df['timestamp'] = pd.date_range(start='2024-01-01', periods=len(df), freq='1H')
        
        # Ensure numeric columns
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    def run_backtest(self, strategy: Strategy, data: pd.DataFrame, 
                    initial_capital: float = None, 
                    position_size_pct: float = 0.1) -> BacktestResult:
        """
        Run backtest on a strategy
        
        Args:
            strategy: Strategy instance
            data: Historical price data
            initial_capital: Starting capital (uses instance default if None)
            position_size_pct: Position size as percentage of capital (0.1 = 10%)
        
        Returns:
            BacktestResult object
        """
        if initial_capital is None:
            initial_capital = self.initial_capital
        
        # Normalize data
        df = self.normalize_data(data)
        
        if len(df) < 50:
            logger.warning("Insufficient data for backtesting")
            return BacktestResult()
        
        result = BacktestResult()
        capital = initial_capital
        equity_curve = [capital]
        positions = []  # List of open positions
        trades = []
        
        # Minimum period needed for strategy
        min_period = 50
        if hasattr(strategy, 'slow_period'):
            min_period = max(min_period, strategy.slow_period + 10)
        if hasattr(strategy, 'rsi_period'):
            min_period = max(min_period, strategy.rsi_period + 10)
        if hasattr(strategy, 'period'):
            min_period = max(min_period, strategy.period + 10)
        
        # Run backtest
        for i in range(min_period, len(df)):
            current_data = df.iloc[:i+1].copy()
            current_price = float(current_data['close'].iloc[-1])
            current_time = current_data['timestamp'].iloc[-1]
            
            # Check exit conditions for open positions
            positions_to_close = []
            for pos_idx, position in enumerate(positions):
                entry_price = position['entry_price']
                side = position['side']
                stop_loss = position.get('stop_loss', 0)
                take_profit = position.get('take_profit', 0)
                
                # Check stop loss
                if stop_loss > 0:
                    if side == 'BUY' and current_price <= stop_loss:
                        positions_to_close.append((pos_idx, 'stop_loss', current_price))
                        continue
                    elif side == 'SELL' and current_price >= stop_loss:
                        positions_to_close.append((pos_idx, 'stop_loss', current_price))
                        continue
                
                # Check take profit
                if take_profit > 0:
                    if side == 'BUY' and current_price >= take_profit:
                        positions_to_close.append((pos_idx, 'take_profit', current_price))
                        continue
                    elif side == 'SELL' and current_price <= take_profit:
                        positions_to_close.append((pos_idx, 'take_profit', current_price))
                        continue
                
                # Check strategy exit
                if strategy.should_exit(position, current_price):
                    positions_to_close.append((pos_idx, 'strategy_exit', current_price))
            
            # Close positions
            for pos_idx, exit_reason, exit_price in reversed(positions_to_close):
                position = positions.pop(pos_idx)
                
                # Calculate P&L
                entry_price = position['entry_price']
                quantity = position['quantity']
                side = position['side']
                
                if side == 'BUY':
                    pnl = (exit_price - entry_price) * quantity
                else:
                    pnl = (entry_price - exit_price) * quantity
                
                # Apply commission
                commission_cost = (entry_price + exit_price) * quantity * self.commission
                pnl -= commission_cost
                
                # Update capital
                capital += pnl
                
                # Record trade
                trade = {
                    'entry_time': position['entry_time'],
                    'exit_time': current_time,
                    'symbol': position.get('symbol', 'UNKNOWN'),
                    'side': side,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'quantity': quantity,
                    'pnl': pnl,
                    'pnl_percent': (pnl / (entry_price * quantity)) * 100,
                    'exit_reason': exit_reason,
                    'strategy': strategy.name
                }
                trades.append(trade)
                result.trades.append(trade)
                
                if pnl > 0:
                    result.winning_trades += 1
                else:
                    result.losing_trades += 1
            
            # Generate new signal
            try:
                signal = strategy.generate_signal(current_data)
            except Exception as e:
                logger.error(f"Error generating signal: {e}")
                signal = {'action': 'HOLD', 'confidence': 0.0, 'price': current_price}
            
            # Open new position if signal and no existing position
            if signal.get('action') in ['BUY', 'SELL'] and len(positions) == 0:
                side = signal['action']
                entry_price = signal.get('price', current_price)
                
                # Calculate position size
                position_value = capital * position_size_pct
                quantity = position_value / entry_price
                
                # Create position
                position = {
                    'entry_time': current_time,
                    'entry_price': entry_price,
                    'quantity': quantity,
                    'side': side,
                    'symbol': current_data.get('symbol', 'UNKNOWN').iloc[0] if 'symbol' in current_data.columns else 'UNKNOWN',
                    'stop_loss': signal.get('stop_loss', 0),
                    'take_profit': signal.get('take_profit', 0),
                    'confidence': signal.get('confidence', 0.0)
                }
                positions.append(position)
            
            # Update equity curve
            # Calculate unrealized P&L
            unrealized_pnl = 0
            for position in positions:
                entry_price = position['entry_price']
                quantity = position['quantity']
                side = position['side']
                
                if side == 'BUY':
                    unrealized_pnl += (current_price - entry_price) * quantity
                else:
                    unrealized_pnl += (entry_price - current_price) * quantity
            
            equity_curve.append(capital + unrealized_pnl)
        
        # Close any remaining positions
        if len(positions) > 0 and len(df) > 0:
            final_price = float(df['close'].iloc[-1])
            final_time = df['timestamp'].iloc[-1]
            
            for position in positions:
                entry_price = position['entry_price']
                quantity = position['quantity']
                side = position['side']
                
                if side == 'BUY':
                    pnl = (final_price - entry_price) * quantity
                else:
                    pnl = (entry_price - final_price) * quantity
                
                commission_cost = (entry_price + final_price) * quantity * self.commission
                pnl -= commission_cost
                capital += pnl
                
                trade = {
                    'entry_time': position['entry_time'],
                    'exit_time': final_time,
                    'symbol': position.get('symbol', 'UNKNOWN'),
                    'side': side,
                    'entry_price': entry_price,
                    'exit_price': final_price,
                    'quantity': quantity,
                    'pnl': pnl,
                    'pnl_percent': (pnl / (entry_price * quantity)) * 100,
                    'exit_reason': 'end_of_data',
                    'strategy': strategy.name
                }
                trades.append(trade)
                result.trades.append(trade)
                
                if pnl > 0:
                    result.winning_trades += 1
                else:
                    result.losing_trades += 1
        
        # Calculate metrics
        result.total_trades = len(trades)
        result.equity_curve = equity_curve
        
        if len(trades) > 0:
            result.total_pnl = sum(t['pnl'] for t in trades)
            result.win_rate = (result.winning_trades / result.total_trades) * 100 if result.total_trades > 0 else 0
            
            winning_pnls = [t['pnl'] for t in trades if t['pnl'] > 0]
            losing_pnls = [t['pnl'] for t in trades if t['pnl'] < 0]
            
            if winning_pnls:
                result.avg_win = np.mean(winning_pnls)
                result.largest_win = max(winning_pnls)
            else:
                result.avg_win = 0
                result.largest_win = 0
            
            if losing_pnls:
                result.avg_loss = np.mean(losing_pnls)
                result.largest_loss = min(losing_pnls)
            else:
                result.avg_loss = 0
                result.largest_loss = 0
            
            # Profit factor
            total_wins = sum(winning_pnls) if winning_pnls else 0
            total_losses = abs(sum(losing_pnls)) if losing_pnls else 0
            result.profit_factor = total_wins / total_losses if total_losses > 0 else float('inf') if total_wins > 0 else 0
            
            # Max drawdown
            equity_array = np.array(equity_curve)
            running_max = np.maximum.accumulate(equity_array)
            drawdown = equity_array - running_max
            result.max_drawdown = abs(np.min(drawdown))
            result.max_drawdown_percent = (result.max_drawdown / initial_capital) * 100 if initial_capital > 0 else 0
            
            # Sharpe ratio (simplified)
            if len(equity_curve) > 1:
                returns = np.diff(equity_curve) / equity_curve[:-1]
                if len(returns) > 0 and np.std(returns) > 0:
                    result.sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)  # Annualized
                else:
                    result.sharpe_ratio = 0
            else:
                result.sharpe_ratio = 0
        
        return result
    
    def backtest_strategy(self, strategy_name: str, data: pd.DataFrame, 
                         strategy_params: Dict = None,
                         initial_capital: float = None,
                         position_size_pct: float = 0.1) -> BacktestResult:
        """
        Backtest a strategy by name
        
        Args:
            strategy_name: Name of strategy
            data: Historical price data
            strategy_params: Parameters for strategy initialization
            initial_capital: Starting capital
            position_size_pct: Position size percentage
        
        Returns:
            BacktestResult object
        """
        if strategy_name not in self.strategies:
            raise ValueError(f"Strategy '{strategy_name}' not found")
        
        StrategyClass = self.strategies[strategy_name]
        
        # Initialize strategy with parameters
        if strategy_params:
            strategy = StrategyClass(**strategy_params)
        else:
            # Default parameters for EMA strategies
            if strategy_name == "EMA Crossover":
                strategy = StrategyClass(fast_period=9, slow_period=21)
            elif strategy_name == "EMA Ribbon":
                strategy = StrategyClass(periods=[8, 13, 21, 34, 55, 89])
            elif strategy_name == "EMA 200 Dynamic S/R":
                strategy = StrategyClass(pullback_ema=21)
            elif strategy_name == "Chart Patterns" and CHART_PATTERNS_AVAILABLE:
                strategy = StrategyClass(pattern_types=['all'])
            else:
                strategy = StrategyClass()
        
        return self.run_backtest(strategy, data, initial_capital, position_size_pct)


def compare_strategies(data: pd.DataFrame, strategies: List[str], 
                      strategy_params: Dict = None,
                      initial_capital: float = 100000.0) -> Dict:
    """
    Compare multiple strategies
    
    Args:
        data: Historical price data
        strategies: List of strategy names
        strategy_params: Dict of strategy params per strategy
        initial_capital: Starting capital
    
    Returns:
        Dictionary with comparison results
    """
    backtester = Backtester(initial_capital=initial_capital)
    results = {}
    
    for strategy_name in strategies:
        try:
            params = strategy_params.get(strategy_name, {}) if strategy_params else {}
            result = backtester.backtest_strategy(strategy_name, data, params, initial_capital)
            results[strategy_name] = result.to_dict()
        except Exception as e:
            logger.error(f"Error backtesting {strategy_name}: {e}")
            results[strategy_name] = {'error': str(e)}
    
    return results

