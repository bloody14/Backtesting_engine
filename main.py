import os
import json
import pandas as pd
from src.data_loader import get_historical_data
from src.strategies import ma_crossover_strategy, mean_reversion_strategy, momentum_strategy
from src.backtest_engine import run_backtest, get_benchmark
from src.metrics import calculate_metrics
from src.walk_forward import generate_walk_forward_splits

def run_strategy(prices: pd.DataFrame, strategy_func, params: dict, cost_bps: float) -> dict:
    """Runs a single strategy and returns gross and net metrics plus equity curves."""
    signals = strategy_func(prices, **params)
    results = run_backtest(prices, signals, transaction_cost_bps=cost_bps)
    
    metrics_gross = calculate_metrics(results['returns_gross'])
    metrics_net = calculate_metrics(results['returns_net'], results['turnover'])
    
    # We want a format easy to serialize to JSON for the frontend
    # Convert equity curve (DatetimeIndex) to string keys
    equity_net_series = results['equity_net'].dropna()
    
    # Take a subsample of dates if the series is too large for the frontend charting (e.g. weekly)
    # But for an accurate chart, we can keep daily but serialize cleanly
    equity_curve = [
        {"date": date.strftime("%Y-%m-%d"), "value": float(val)}
        for date, val in equity_net_series.items()
    ]
    
    # Same for rolling drawdown
    rolling_max = results['equity_net'].cummax()
    drawdown = ((results['equity_net'] - rolling_max) / rolling_max).dropna()
    drawdown_curve = [
        {"date": date.strftime("%Y-%m-%d"), "value": float(val)}
        for date, val in drawdown.items()
    ]
    
    return {
        "metrics": {
            "gross": metrics_gross,
            "net": metrics_net
        },
        "equity_curve": equity_curve,
        "drawdown_curve": drawdown_curve
    }

def main():
    print("Loading data...")
    prices = get_historical_data(start_date="2018-01-01")
    
    cost_bps = 5.0
    
    print("Running Benchmark...")
    benchmark_equity = get_benchmark(prices).dropna()
    benchmark_returns = benchmark_equity.pct_change().dropna()
    benchmark_metrics = calculate_metrics(benchmark_returns)
    
    benchmark_curve = [
        {"date": date.strftime("%Y-%m-%d"), "value": float(val)}
        for date, val in benchmark_equity.items()
    ]
    
    strategies_to_run = {
        "Moving Average Crossover": {
            "func": ma_crossover_strategy,
            "params": {"fast_window": 20, "slow_window": 50}
        },
        "Mean Reversion": {
            "func": mean_reversion_strategy,
            "params": {"window": 20, "z_threshold": 2.0}
        },
        "Momentum": {
            "func": momentum_strategy,
            "params": {"lookback": 60, "top_k": 3, "rebalance_freq": "ME"}
        }
    }
    
    results_output = {
        "benchmark": {
            "metrics": benchmark_metrics,
            "equity_curve": benchmark_curve
        },
        "strategies": {}
    }
    
    for name, strat in strategies_to_run.items():
        print(f"Running {name}...")
        strat_results = run_strategy(prices, strat["func"], strat["params"], cost_bps)
        results_output["strategies"][name] = strat_results
        
    print("Running Walk-Forward Validation on Momentum strategy...")
    # Walk-forward validation example
    splits = generate_walk_forward_splits(prices.index, train_years=3, test_years=1)
    wf_results = []
    
    # We will just collect OOS net returns
    oos_net_returns_list = []
    
    for i, (train_idx, test_idx) in enumerate(splits):
        # In a real param optimization, we'd find best params on train_prices.
        # Here we just run the fixed params to demonstrate OOS separation.
        test_prices = prices.loc[test_idx]
        
        # NOTE: Computing signals just on test_prices loses the lookback window at the start.
        # A more robust way is to compute signals on all prices, then slice returns to OOS.
        # This prevents the first 60 days of the test window from being NaN.
        signals = momentum_strategy(prices, **strategies_to_run["Momentum"]["params"])
        test_signals = signals.loc[test_idx]
        
        results = run_backtest(test_prices, test_signals, transaction_cost_bps=cost_bps)
        oos_net_returns_list.append(results['returns_net'])
        
        wf_metrics = calculate_metrics(results['returns_net'])
        wf_results.append({
            "window": i + 1,
            "start": test_idx.min().strftime("%Y-%m-%d"),
            "end": test_idx.max().strftime("%Y-%m-%d"),
            "sharpe": wf_metrics.get("Sharpe Ratio", 0.0)
        })
        
    results_output["walk_forward_momentum"] = wf_results
    
    os.makedirs("outputs", exist_ok=True)
    out_path = os.path.join("outputs", "results.json")
    with open(out_path, "w") as f:
        json.dump(results_output, f, indent=2)
        
    print(f"Done! Results saved to {out_path}")
    
if __name__ == "__main__":
    main()
