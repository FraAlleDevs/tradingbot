# Market Periods for Backtesting

This document lists all predefined market periods available for testing trading strategies in different market conditions.

## Usage

```bash
# Test a specific period
python main.py --period bull_2017

# Test with custom risk parameters
python main.py --period bear_2022 --stop_loss 0.03 --position_size 0.1

# Use custom date range
python main.py --start_date 2023-01-01 --end_date 2023-01-31
```

## Available Periods

### Bull Markets

| Period | Dates | Description |
|--------|-------|-------------|
| `bull_2017` | 2017-01-01 to 2017-12-31 | Strong bull market, Bitcoin rose from ~$1,000 to ~$13,000 |
| `bull_2019` | 2019-01-01 to 2019-12-31 | Recovery bull market after 2018 crash |
| `bull_2021` | 2021-01-01 to 2021-12-31 | Crypto boom, Bitcoin reached ~$69,000 |
| `december_2017` | 2017-12-01 to 2017-12-31 | Peak of 2017 bull market |

### Bear Markets

| Period | Dates | Description |
|--------|-------|-------------|
| `bear_2018` | 2018-01-01 to 2018-12-31 | Crypto winter, Bitcoin fell from ~$13,000 to ~$3,800 |
| `bear_2022` | 2022-01-01 to 2022-12-31 | Major bear market, Bitcoin fell from ~$47,000 to ~$16,500 |

### Crisis Periods

| Period | Dates | Description |
|--------|-------|-------------|
| `covid_crash_2020` | 2020-02-01 to 2020-04-30 | COVID-19 pandemic crash and recovery |
| `march_2020` | 2020-03-01 to 2020-03-31 | March 2020 COVID panic (Black Thursday) |

### Recovery Periods

| Period | Dates | Description |
|--------|-------|-------------|
| `recovery_2023` | 2023-01-01 to 2023-12-31 | Post-2022 bear market recovery |
| `jan_2023` | 2023-01-01 to 2023-01-31 | January 2023 (recovery period) |

## Testing Strategy

### For Bull Markets
- Use more aggressive position sizing (20-30%)
- Higher stop-loss tolerance (5-8%)
- Trend-following strategies typically perform well

### For Bear Markets
- Use conservative position sizing (10-15%)
- Tighter stop-losses (3-5%)
- Mean reversion strategies may perform better

### For Crisis Periods
- Very conservative position sizing (5-10%)
- Tight stop-losses (2-3%)
- Focus on capital preservation

## Example Commands

```bash
# Test bull market performance
python main.py --period bull_2021 --stop_loss 0.08 --position_size 0.3

# Test bear market performance
python main.py --period bear_2022 --stop_loss 0.03 --position_size 0.1

# Test crisis period
python main.py --period covid_crash_2020 --stop_loss 0.02 --position_size 0.05

# Compare strategies across different periods
python main.py --period bull_2017
python main.py --period bear_2018
python main.py --period covid_crash_2020
```

## Adding New Periods

To add new periods, edit the `MARKET_PERIODS` dictionary in `main.py`:

```python
MARKET_PERIODS = {
    'your_period': ('YYYY-MM-DD', 'YYYY-MM-DD', 'Description'),
    # ... existing periods
}
``` 