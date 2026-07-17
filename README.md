# Quantitative Strategy Backtesting Engine

Built a vectorized backtesting engine in Python testing 3 systematic equity strategies (moving average crossover, mean reversion, momentum) across 20 liquid equities over 6+ years; achieved 1.01 Sharpe ratio using explicit look-ahead-bias controls and transaction-cost-adjusted returns.

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
| Benchmark | 1.03 | - | 19.23% | - | -32.95% | - |
| Moving Average Crossover | -0.19 | -0.23 | -3.32% | -3.86% | -34.37% | -36.71% |
| Mean Reversion | -0.01 | -0.16 | -1.75% | -4.38% | -33.87% | -38.51% |
| Momentum | 1.02 | 1.01 | 25.07% | 24.51% | -28.45% | -28.50% |

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
