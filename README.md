# Crypto modern portfolio theory

select high return, low volatility combination of tokens.

![alt text](https://github.com/ertosns/finai-solutions/mpt/blob/main/img/volatility.png?raw=true)

## method

- from all crypto pairs (symbol-usd) from coinbase pro API.
- scrap market-cap (no avail free market-cap API) from coinmarketcap.com, filter tokens by market-cap above target see configurations.py
- retrieve historical close price at in range `start_date`-`end_date` in configurations.py, and at granularity specified.
- for filtered tokens, optimize portfolio weights for maximum sharpe (highest return, relatively low volatility), and variance(highest return for low volatility)
- write portfolio to portfolio_sharpe.json, portfolio_var.json

![alt text](https://github.com/finai-solutions/mpt/blob/main/img/portfolio.png?raw=true)
