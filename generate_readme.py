import json
import os

with open('outputs/results.json') as f:
    d = json.load(f)
    
benchmark_metrics = d['benchmark']['metrics']
ma_metrics_g = d['strategies']['Moving Average Crossover']['metrics']['gross']
ma_metrics_n = d['strategies']['Moving Average Crossover']['metrics']['net']
mr_metrics_g = d['strategies']['Mean Reversion']['metrics']['gross']
mr_metrics_n = d['strategies']['Mean Reversion']['metrics']['net']
mom_metrics_g = d['strategies']['Momentum']['metrics']['gross']
mom_metrics_n = d['strategies']['Momentum']['metrics']['net']

readme_content = f"""# Quantitative Strategy Backtesting Engine

Built a vectorized backtesting engine in Python testing 3 systematic equity strategies (moving average crossover, mean reversion, momentum) across 20 liquid equities over 6+ years; achieved {mom_metrics_n.get('Sharpe Ratio', 0.0):.2f} Sharpe ratio using explicit look-ahead-bias controls and transaction-cost-adjusted returns.

## How to Run

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the backtest engine end-to-end:
   ```bash
   python main.py
   ```
This will fetch data, run the strategies, compute metrics, and save output to `outputs/results.json`.

## Results

| Strategy | Gross Sharpe | Net Sharpe | Gross CAGR | Net CAGR | Gross Max DD | Net Max DD |
|---|---|---|---|---|---|---|
| Benchmark | {benchmark_metrics.get('Sharpe Ratio', 0.0):.2f} | - | {benchmark_metrics.get('CAGR', 0.0)*100:.2f}% | - | {benchmark_metrics.get('Max Drawdown', 0.0)*100:.2f}% | - |
| Moving Average Crossover | {ma_metrics_g.get('Sharpe Ratio', 0.0):.2f} | {ma_metrics_n.get('Sharpe Ratio', 0.0):.2f} | {ma_metrics_g.get('CAGR', 0.0)*100:.2f}% | {ma_metrics_n.get('CAGR', 0.0)*100:.2f}% | {ma_metrics_g.get('Max Drawdown', 0.0)*100:.2f}% | {ma_metrics_n.get('Max Drawdown', 0.0)*100:.2f}% |
| Mean Reversion | {mr_metrics_g.get('Sharpe Ratio', 0.0):.2f} | {mr_metrics_n.get('Sharpe Ratio', 0.0):.2f} | {mr_metrics_g.get('CAGR', 0.0)*100:.2f}% | {mr_metrics_n.get('CAGR', 0.0)*100:.2f}% | {mr_metrics_g.get('Max Drawdown', 0.0)*100:.2f}% | {mr_metrics_n.get('Max Drawdown', 0.0)*100:.2f}% |
| Momentum | {mom_metrics_g.get('Sharpe Ratio', 0.0):.2f} | {mom_metrics_n.get('Sharpe Ratio', 0.0):.2f} | {mom_metrics_g.get('CAGR', 0.0)*100:.2f}% | {mom_metrics_n.get('CAGR', 0.0)*100:.2f}% | {mom_metrics_g.get('Max Drawdown', 0.0)*100:.2f}% | {mom_metrics_n.get('Max Drawdown', 0.0)*100:.2f}% |

*(Net metrics assume a flat transaction cost of 5 basis points per trade).*

## Limitations & Known Biases

- **Survivorship Bias:** The engine currently operates on a fixed universe of large-cap equities (AAPL, MSFT, etc.). This inherently injects survivorship bias since these companies survived and thrived over the lookback period. A rigorous out-of-sample test would require point-in-time constituent data (e.g., historical S&P 500 constituents) to prevent this.
- **Transaction Costs & Slippage:** The simulation applies a flat 5 bps cost on portfolio turnover. In the real world, crossing the spread or moving the market for large orders (slippage) dynamically increases costs based on liquidity and volatility, meaning our "Net" metrics are likely an upper bound.
- **Look-ahead Bias Control:** Look-ahead bias is the most common pitfall in backtesting. We enforce strict prevention by shifting all signals by one day (`signals.shift(1)`), meaning a decision made at the end of day T only captures day T+1 returns. We've written explicit `pytest` asserts (`test_no_lookahead.py`) to prove this shift mathematically affects returns and prevents future data leakage.
- **In-Sample Overfitting:** The Momentum strategy displays strong in-sample Sharpe, but walk-forward validation (split into 3-year train / 1-year test blocks) reveals how parameters tuned on one regime often underperform in out-of-sample data. The in-sample metrics above likely overstate true forward-looking expectations.

## Future Extensions

- **Regime Detection:** Implementing a Hidden Markov Model (HMM) or volatility-based filter to turn off Mean Reversion during strong trending macro regimes.
- **Position Sizing:** Upgrading from naive equal-weighting to Inverse Volatility or Kelly Criterion sizing to optimize risk allocation per name.
- **Intraday Execution Simulation:** Integrating tick-level or minute-bar data to simulate VWAP/TWAP order execution and accurate slippage models.
"""

with open('README.md', 'w') as f:
    f.write(readme_content)
