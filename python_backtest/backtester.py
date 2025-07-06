import pandas as pd
import numpy as np
from typing import Dict, Any, List
from strategies.base import Strategy
import logging

class Backtester:
    """
    Portfolio Backtesting Engine
    
    Simulates trading strategies with realistic portfolio management including
    position sizing, stop-loss protection, and daily profit reinvestment.
    Supports both single strategy and multi-strategy comparison modes.
    
    Parameters:
        initial_capital (float): Starting portfolio value (default: 100.0)
            - Higher values = larger position sizes, more significant profits/losses
            - Lower values = smaller trades, easier to test with small amounts
            - Typical range: $100-$10,000 for testing
            
        position_size (float): Fraction of available capital per trade (default: 0.8)
            - Lower values = more conservative, better risk management
            - Higher values = more aggressive, higher potential returns/risk
            - Range: 0.1-1.0 (10%-100% of capital per trade)
            - 0.8 = 80% of available capital used per trade
            
        stop_loss (float): Maximum loss percentage before exit (default: 0.02)
            - Lower values = tighter risk control, more frequent exits
            - Higher values = more room for recovery, fewer stop-outs
            - Range: 0.01-0.05 (1%-5% loss tolerance)
            - 0.02 = 2% stop loss
    """
    
    def __init__(self, initial_capital: float = 100.0, position_size: float = 0.8, stop_loss: float = 0.02):
        self.initial_capital = initial_capital
        self.position_size = position_size  # Use 80% of available capital per trade
        self.stop_loss = stop_loss
        self.reinvest_profits = True  # Reinvest profits daily
        
    def run(self, data: pd.DataFrame, strategy: Strategy) -> Dict[str, Any]:
        """
        Execute backtest simulation with the given strategy and data.
        
        Args:
            data (pd.DataFrame): Price data with datetime index and 'Close' column
            strategy (Strategy): Trading strategy object implementing generate_signals()
            
        Returns:
            Dict[str, Any]: Backtest results containing:
                - portfolio: DataFrame with all portfolio metrics over time
                - total_return: Overall percentage return
                - annualized_return: Return adjusted for time period
                - sharpe_ratio: Risk-adjusted return measure
                - max_drawdown: Largest peak-to-trough decline
                - volatility: Annualized price volatility
                - num_trades: Total number of trades executed
                - win_rate: Percentage of profitable trades
                - profit_factor: Ratio of gross profit to gross loss
                
        Simulation Logic:
            1. Generate trading signals from strategy
            2. Track portfolio value, cash, and positions
            3. Execute trades based on signals and risk management
            4. Apply stop-loss protection
            5. Reinvest profits daily
            6. Calculate performance metrics
        """
        signals = strategy.generate_signals(data)
        
        # Initialize portfolio tracking
        portfolio = pd.DataFrame(index=data.index)
        portfolio['price'] = data['Close']
        portfolio['signal'] = signals
        portfolio['position'] = 0.0
        portfolio['cash'] = self.initial_capital
        portfolio['holdings'] = 0.0
        portfolio['total_value'] = self.initial_capital
        portfolio['daily_pnl'] = 0.0
        portfolio['entry_price'] = 0.0  # Track entry price for short positions
        
        # Log initial portfolio state
        logging.info(f"Initial capital: ${self.initial_capital:.2f}")
        logging.info(f"Position size: {self.position_size:.1%}")
        logging.info(f"Stop loss: {self.stop_loss:.1%}")
        
        position = 0  # 0: no position, 1: long, -1: short
        entry_price = 0
        entry_time = None
        daily_start_value = self.initial_capital
        
        total_rows = len(data)
        print(f"Processing {total_rows:,} rows...")
        
        for i in range(total_rows):
            if i % 10000 == 0:  # Progress indicator every 10k rows
                print(f"Progress: {i:,}/{total_rows:,} ({i/total_rows*100:.1f}%)")
                
            current_price = data['Close'].iloc[i]
            current_time = data.index[i]
            signal = signals.iloc[i]
            
            # Get current position from previous iteration
            if i > 0:
                prev_position = portfolio['position'].iloc[i-1]
                position = 1 if prev_position > 0 else (-1 if prev_position < 0 else 0)
            else:
                position = 0  # Start with no position
            
            # Check if it's a new day for profit reinvestment
            if i > 0:
                prev_time = data.index[i-1]
                if current_time.date() != prev_time.date():
                    # New day - reinvest profits if enabled
                    logging.debug(f"New day detected at {current_time}. Previous cash: {portfolio['cash'].iloc[i-1]:.2f}")
                    if self.reinvest_profits and portfolio['total_value'].iloc[i-1] > daily_start_value:
                        profit = portfolio['total_value'].iloc[i-1] - daily_start_value
                        portfolio.loc[current_time, 'cash'] = portfolio['cash'].iloc[i-1] + profit
                        daily_start_value = portfolio['total_value'].iloc[i-1]
                        logging.debug(f"  Reinvested profit: ${profit:.2f}, New cash: ${portfolio.loc[current_time, 'cash']:.2f}")
                    else:
                        portfolio.loc[current_time, 'cash'] = portfolio['cash'].iloc[i-1]
                        daily_start_value = portfolio['total_value'].iloc[i-1]
                        logging.debug(f"  No profit reinvestment. Carried forward cash: ${portfolio.loc[current_time, 'cash']:.2f}")
                else:
                    # Same day - carry forward cash from previous iteration
                    portfolio.loc[current_time, 'cash'] = portfolio['cash'].iloc[i-1]
                    logging.debug(f"Same day at {current_time}. Carried forward cash: ${portfolio.loc[current_time, 'cash']:.2f}")
            else:
                portfolio.loc[current_time, 'cash'] = self.initial_capital
                logging.debug(f"First iteration at {current_time}. Set initial cash: ${portfolio.loc[current_time, 'cash']:.2f}")
            
            # Check stop loss if in position
            if position != 0:
                if position == 1:  # Long position
                    loss_pct = (entry_price - current_price) / entry_price
                    if loss_pct >= self.stop_loss:
                        # Stop loss triggered
                        logging.info(f"Stop-loss triggered at {current_time}: Entry {entry_price:.2f}, Exit {current_price:.2f}, Loss {loss_pct:.1%}")
                        portfolio.loc[current_time, 'signal'] = -1
                        signal = -1
                else:  # Short position
                    loss_pct = (current_price - entry_price) / entry_price
                    if loss_pct >= self.stop_loss:
                        # Stop loss triggered
                        logging.info(f"Stop-loss triggered at {current_time}: Entry {entry_price:.2f}, Exit {current_price:.2f}, Loss {loss_pct:.1%}")
                        portfolio.loc[current_time, 'signal'] = 1
                        signal = 1
            
            # Execute trades
            if signal == 1 and position == 0:  # Buy signal
                logging.debug(f"BUY signal at {current_time}. Cash before trade: ${portfolio['cash'].iloc[i]:.2f}")
                position = 1
                entry_price = current_price
                entry_time = current_time
                trade_value = min(portfolio['cash'].iloc[i], portfolio['cash'].iloc[i] * self.position_size)  # Never trade more than available cash
                shares = trade_value / current_price
                portfolio.loc[current_time, 'position'] = shares
                portfolio.loc[current_time, 'cash'] = portfolio['cash'].iloc[i] - trade_value
                logging.debug(f"  Trade executed: ${trade_value:.2f} for {shares:.6f} shares. Cash after: ${portfolio.loc[current_time, 'cash']:.2f}")
                
                # Safety check: ensure cash doesn't go negative
                if portfolio.loc[current_time, 'cash'] < 0:
                    logging.warning(f"Trade would result in negative cash. Adjusting position size.")
                    portfolio.loc[current_time, 'cash'] = 0
                    portfolio.loc[current_time, 'position'] = portfolio['cash'].iloc[i] / current_price
            
            elif signal == -1 and position == 0:  # Sell signal (short)
                logging.debug(f"SELL signal at {current_time}. Cash before trade: ${portfolio['cash'].iloc[i]:.2f}")
                position = -1
                entry_price = current_price
                entry_time = current_time
                trade_value = min(portfolio['cash'].iloc[i], portfolio['cash'].iloc[i] * self.position_size)  # Never trade more than available cash
                shares = trade_value / current_price
                portfolio.loc[current_time, 'position'] = -shares
                # DO NOT add trade_value to cash for short selling; cash remains unchanged
                portfolio.loc[current_time, 'cash'] = portfolio['cash'].iloc[i]
                # Store entry price for short position tracking
                portfolio.loc[current_time, 'entry_price'] = entry_price
                logging.debug(f"  Short trade executed: ${trade_value:.2f} for {shares:.6f} shares. Cash after: ${portfolio.loc[current_time, 'cash']:.2f}")
                
                # Safety check: ensure cash doesn't go negative (shouldn't happen with short selling)
                if portfolio.loc[current_time, 'cash'] < 0:
                    logging.warning(f"Short trade would result in negative cash. This shouldn't happen.")
                    portfolio.loc[current_time, 'cash'] = 0
                    portfolio.loc[current_time, 'position'] = -portfolio['cash'].iloc[i] / current_price
            
            elif signal == -1 and position == 1:  # Close long position
                shares = portfolio['position'].iloc[i-1] if i > 0 else portfolio['position'].iloc[i]
                trade_value = shares * current_price
                portfolio.loc[current_time, 'position'] = 0
                portfolio.loc[current_time, 'cash'] = portfolio['cash'].iloc[i] + trade_value
                position = 0
                
                # Debug: Log position closing
                logging.info(f"Closed long position at {current_time}: {shares:.6f} shares @ ${current_price:.2f} = ${trade_value:.2f}")
                logging.info(f"  Cash before: ${portfolio['cash'].iloc[i]:.2f}, Cash after: ${portfolio.loc[current_time, 'cash']:.2f}")
                logging.debug(f"  Position reset to 0, entry_price reset to 0")
                
            elif signal == 1 and position == -1:  # Close short position
                shares = abs(portfolio['position'].iloc[i-1] if i > 0 else portfolio['position'].iloc[i])
                trade_value = shares * current_price
                portfolio.loc[current_time, 'position'] = 0
                portfolio.loc[current_time, 'cash'] = portfolio['cash'].iloc[i] + trade_value
                position = 0
                
                # Debug: Log position closing
                logging.info(f"Closed short position at {current_time}: {shares:.6f} shares @ ${current_price:.2f} = ${trade_value:.2f}")
                logging.info(f"  Cash before: ${portfolio['cash'].iloc[i]:.2f}, Cash after: ${portfolio.loc[current_time, 'cash']:.2f}")
                logging.debug(f"  Position reset to 0, entry_price reset to 0")
                
            else:  # No signal, maintain current position
                if i > 0:
                    portfolio.loc[current_time, 'position'] = portfolio['position'].iloc[i-1]
                    portfolio.loc[current_time, 'cash'] = portfolio['cash'].iloc[i-1]
                    portfolio.loc[current_time, 'holdings'] = portfolio['holdings'].iloc[i-1]
                    portfolio.loc[current_time, 'entry_price'] = portfolio['entry_price'].iloc[i-1]
                    logging.debug(f"No signal at {current_time}. Carried forward - Position: {portfolio['position'].iloc[i-1]:.6f}, Cash: ${portfolio['cash'].iloc[i-1]:.2f}, Holdings: ${portfolio['holdings'].iloc[i-1]:.2f}")
                else:
                    portfolio.loc[current_time, 'position'] = 0
                    portfolio.loc[current_time, 'cash'] = self.initial_capital
                    portfolio.loc[current_time, 'holdings'] = 0
                    portfolio.loc[current_time, 'entry_price'] = 0.0
                    logging.debug(f"First iteration no signal at {current_time}. Set defaults - Position: 0, Cash: ${self.initial_capital:.2f}, Holdings: 0")
            
            # Calculate current holdings value
            current_position = portfolio['position'].iloc[i]
            if current_position > 0:  # Long position
                portfolio.loc[current_time, 'holdings'] = current_position * current_price
            elif current_position < 0:  # Short position
                if position == -1:  # We're actually in a short position
                    short_shares = abs(current_position)
                    short_entry_price = portfolio['entry_price'].iloc[i] if portfolio['entry_price'].iloc[i] > 0 else entry_price
                    short_pnl = (short_entry_price - current_price) * short_shares
                    portfolio.loc[current_time, 'holdings'] = short_pnl
                else:
                    # Position was closed, holdings should be zero
                    portfolio.loc[current_time, 'holdings'] = 0
            else:  # No position
                portfolio.loc[current_time, 'holdings'] = 0
            
            # Calculate total portfolio value
            total_value = portfolio['cash'].iloc[i] + portfolio['holdings'].iloc[i]
            portfolio.loc[current_time, 'total_value'] = total_value

            # Debug: Track significant portfolio value drops
            if i > 0:
                prev_value = portfolio['total_value'].iloc[i-1]
                if prev_value > 0:
                    drop_pct = (total_value - prev_value) / prev_value
                    if drop_pct < -0.1:  # Log drops greater than 10%
                        logging.warning(f"Significant portfolio drop at {current_time}: {prev_value:.2f} -> {total_value:.2f} ({drop_pct:.1%})")
                        logging.warning(f"  Cash: {portfolio['cash'].iloc[i]:.2f}, Holdings: {portfolio['holdings'].iloc[i]:.2f}")
                        logging.warning(f"  Position: {portfolio['position'].iloc[i]:.6f}, Price: {current_price:.2f}")
                    
                    # CRITICAL: Stop simulation if portfolio drops by more than 50% in one step
                    if drop_pct < -0.5:
                        logging.error(f"CRITICAL: Portfolio dropped by {drop_pct:.1%} at {current_time}. This is unrealistic. Stopping simulation.")
                        print(f"❌ CRITICAL ERROR: Portfolio dropped by {drop_pct:.1%} at {current_time}. Stopping simulation.")
                        # Fill remaining rows with the last valid values
                        for j in range(i + 1, total_rows):
                            remaining_time = data.index[j]
                            portfolio.loc[remaining_time, 'position'] = portfolio['position'].iloc[i-1]
                            portfolio.loc[remaining_time, 'cash'] = portfolio['cash'].iloc[i-1]
                            portfolio.loc[remaining_time, 'holdings'] = portfolio['holdings'].iloc[i-1]
                            portfolio.loc[remaining_time, 'total_value'] = portfolio['total_value'].iloc[i-1]
                            portfolio.loc[remaining_time, 'daily_pnl'] = 0
                            portfolio.loc[remaining_time, 'entry_price'] = portfolio['entry_price'].iloc[i-1]
                        break

            # After all portfolio updates, add detailed debug logging
            logging.debug(f"{current_time}: Position={portfolio['position'].iloc[i]}, Cash={portfolio['cash'].iloc[i]:.2f}, Holdings={portfolio['holdings'].iloc[i]:.2f}, Total={portfolio['total_value'].iloc[i]:.2f}, Signal={signal}")

            # Forced liquidation if portfolio value drops below $1
            if total_value < 1:
                logging.warning(f"Portfolio value dropped below $1 at {current_time}. FORCED LIQUIDATION.")
                print(f"⚠️  FORCED LIQUIDATION: Portfolio value dropped below $1 at {current_time}")
                # Close all positions, set everything to zero
                portfolio.loc[current_time, 'position'] = 0
                portfolio.loc[current_time, 'cash'] = 0
                portfolio.loc[current_time, 'holdings'] = 0
                portfolio.loc[current_time, 'total_value'] = 0
                portfolio.loc[current_time, 'daily_pnl'] = 0
                portfolio.loc[current_time, 'entry_price'] = 0
                # Fill remaining rows with zeros
                for j in range(i + 1, total_rows):
                    remaining_time = data.index[j]
                    portfolio.loc[remaining_time, 'position'] = 0
                    portfolio.loc[remaining_time, 'cash'] = 0
                    portfolio.loc[remaining_time, 'holdings'] = 0
                    portfolio.loc[remaining_time, 'total_value'] = 0
                    portfolio.loc[remaining_time, 'daily_pnl'] = 0
                    portfolio.loc[remaining_time, 'entry_price'] = 0
                break

            # Debug: Log when portfolio goes negative (but continue for now)
            if total_value < 0:
                logging.error(f"Portfolio went negative: ${total_value:.2f} at {current_time}")
                print(f"❌ Portfolio went negative: ${total_value:.2f} at {current_time}")
                if current_position < 0 and position == -1:
                    short_shares = abs(current_position)
                    short_entry_price = portfolio['entry_price'].iloc[i] if portfolio['entry_price'].iloc[i] > 0 else entry_price
                    short_pnl = (short_entry_price - current_price) * short_shares
                    logging.error(f"Short position details at {current_time}:")
                    logging.error(f"  Entry price: ${short_entry_price:.2f}")
                    logging.error(f"  Current price: ${current_price:.2f}")
                    logging.error(f"  Short shares: {short_shares:.6f}")
                    logging.error(f"  Short P&L: ${short_pnl:.2f}")
                    logging.error(f"  Cash: ${portfolio['cash'].iloc[i]:.2f}")
                    logging.error(f"  Total value: ${total_value:.2f}")

            # Calculate daily P&L
            if i > 0:
                portfolio.loc[current_time, 'daily_pnl'] = (
                    portfolio['total_value'].iloc[i] - portfolio['total_value'].iloc[i-1]
                )
        
        # Calculate performance metrics
        returns = portfolio['total_value'].pct_change().dropna()
        
        # Log final portfolio state
        final_value = portfolio['total_value'].iloc[-1]
        total_return = (final_value - self.initial_capital) / self.initial_capital
        logging.info(f"Final portfolio value: ${final_value:.2f}")
        logging.info(f"Total return: {total_return:.2%}")
        logging.info(f"Total profit: ${final_value - self.initial_capital:.2f}")
        
        results = {
            'portfolio': portfolio,
            'total_return': total_return,
            'annualized_return': self._calculate_annualized_return(portfolio['total_value']),
            'sharpe_ratio': self._calculate_sharpe_ratio(returns),
            'max_drawdown': self._calculate_max_drawdown(portfolio['total_value']),
            'volatility': returns.std() * np.sqrt(252 * 24 * 60),  # Annualized volatility
            'num_trades': len(portfolio[portfolio['signal'] != 0]),
            'win_rate': self._calculate_win_rate(portfolio),
            'profit_factor': self._calculate_profit_factor(portfolio)
        }
        
        return results
    
    def run_multiple_strategies(self, data: pd.DataFrame, strategies: Dict[str, Strategy]) -> Dict[str, Any]:
        """
        Run backtest simulation with multiple strategies and compare their performance.
        
        Args:
            data (pd.DataFrame): Price data with datetime index and 'Close' column
            strategies (Dict[str, Strategy]): Dictionary of strategy names and strategy objects
            
        Returns:
            Dict[str, Any]: Comparison results containing:
                - results: Dictionary of results for each strategy
                - comparison_table: Summary comparison of all strategies
                - best_strategy: Name of the best performing strategy
                
        This method allows you to compare multiple strategies side-by-side
        and identify which one performs best for the given market conditions.
        """
        results = {}
        
        for strategy_name, strategy in strategies.items():
            logging.info(f"\nRunning {strategy_name} strategy...")
            print(f"\nRunning {strategy_name} strategy...")
            
            # Debug: Check signal generation
            signals = strategy.generate_signals(data)
            signal_count = len(signals[signals != 0])
            logging.info(f"Generated {signal_count} signals for {strategy_name}")
            print(f"Generated {signal_count} signals for {strategy_name}")
            
            strategy_results = self.run(data, strategy)
            results[strategy_name] = strategy_results
            
            # Log and print summary for this strategy
            logging.info(f"{strategy_name} - Total trades: {strategy_results['num_trades']}")
            logging.info(f"{strategy_name} - Total return: {strategy_results['total_return']:.2%}")
            logging.info(f"{strategy_name} - Sharpe ratio: {strategy_results['sharpe_ratio']:.2f}")
            logging.info(f"{strategy_name} - Max drawdown: {strategy_results['max_drawdown']:.2%}")
            
            print(f"{strategy_name} - Total trades: {strategy_results['num_trades']}")
            print(f"{strategy_name} - Total return: {strategy_results['total_return']:.2%}")
            print(f"{strategy_name} - Sharpe ratio: {strategy_results['sharpe_ratio']:.2f}")
            print(f"{strategy_name} - Max drawdown: {strategy_results['max_drawdown']:.2%}")
        
        # Create comparison table
        comparison_data = []
        for strategy_name, strategy_results in results.items():
            comparison_data.append({
                'Strategy': strategy_name,
                'Total Return (%)': f"{strategy_results['total_return']:.2%}",
                'Annualized Return (%)': f"{strategy_results['annualized_return']:.2%}",
                'Sharpe Ratio': f"{strategy_results['sharpe_ratio']:.2f}",
                'Max Drawdown (%)': f"{strategy_results['max_drawdown']:.2%}",
                'Volatility (%)': f"{strategy_results['volatility']:.2%}",
                'Number of Trades': strategy_results['num_trades'],
                'Win Rate (%)': f"{strategy_results['win_rate']:.1%}",
                'Profit Factor': f"{strategy_results['profit_factor']:.2f}"
            })
        
        comparison_table = pd.DataFrame(comparison_data)
        
        # Find best strategy (by Sharpe ratio, then by total return)
        best_strategy = max(results.keys(), 
                           key=lambda x: (results[x]['sharpe_ratio'], results[x]['total_return']))
        
        return {
            'results': results,
            'comparison_table': comparison_table,
            'best_strategy': best_strategy
        }
    
    def _calculate_annualized_return(self, equity_curve: pd.Series) -> float:
        """
        Calculate annualized return from equity curve.
        
        Args:
            equity_curve (pd.Series): Portfolio value over time
            
        Returns:
            float: Annualized return percentage
            
        Formula: (1 + total_return)^(365/days) - 1
        """
        total_days = (equity_curve.index[-1] - equity_curve.index[0]).days
        if total_days == 0:
            return 0
        total_return = (equity_curve.iloc[-1] - equity_curve.iloc[0]) / equity_curve.iloc[0]
        return (1 + total_return) ** (365 / total_days) - 1
    
    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """
        Calculate Sharpe ratio (risk-adjusted return).
        
        Args:
            returns (pd.Series): Portfolio returns over time
            
        Returns:
            float: Sharpe ratio (higher is better)
            
        Formula: (mean_return - risk_free_rate) / std_return * sqrt(252*24*60)
        - Assumes 0% risk-free rate
        - Annualized for minute-level data
        """
        if returns.std() == 0:
            return 0
        return returns.mean() / returns.std() * np.sqrt(252 * 24 * 60)  # Annualized
    
    def _calculate_max_drawdown(self, equity_curve: pd.Series) -> float:
        """
        Calculate maximum drawdown (largest peak-to-trough decline).
        
        Args:
            equity_curve (pd.Series): Portfolio value over time
            
        Returns:
            float: Maximum drawdown as negative percentage
            
        Logic: Track running peak, calculate drawdown from peak
        """
        peak = equity_curve.expanding().max()
        drawdown = (equity_curve - peak) / peak
        return drawdown.min()
    
    def _calculate_win_rate(self, portfolio: pd.DataFrame) -> float:
        """
        Calculate win rate (percentage of profitable trades).
        
        Args:
            portfolio (pd.DataFrame): Portfolio data with 'signal' and 'daily_pnl' columns
            
        Returns:
            float: Win rate as percentage (0-100%)
            
        Logic: Count trades with positive P&L / total trades
        """
        trades = portfolio[portfolio['signal'] != 0]
        if len(trades) == 0:
            return 0
        
        winning_trades = 0
        for i in range(len(trades)):
            if trades['daily_pnl'].iloc[i] > 0:
                winning_trades += 1
        
        return winning_trades / len(trades)
    
    def _calculate_profit_factor(self, portfolio: pd.DataFrame) -> float:
        """
        Calculate profit factor (gross profit / gross loss).
        
        Args:
            portfolio (pd.DataFrame): Portfolio data with 'signal' and 'daily_pnl' columns
            
        Returns:
            float: Profit factor (higher is better, >1 means profitable)
            
        Logic: Sum positive P&L / sum negative P&L
        """
        trades = portfolio[portfolio['signal'] != 0]
        if len(trades) == 0:
            return 0
        
        gross_profit = trades[trades['daily_pnl'] > 0]['daily_pnl'].sum()
        gross_loss = abs(trades[trades['daily_pnl'] < 0]['daily_pnl'].sum())
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0
        
        return gross_profit / gross_loss 