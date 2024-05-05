# Crypto modern portfolio theory

select high return, low volatility combination of tokens.

![alt text](https://github.com/finai-solutions/mpt/blob/main/img/volatility.png?raw=true)

## method

- from all crypto pairs (symbol-usd) from coinbase pro API.
- scrape market-cap (no avail free market-cap API) from coinmarketcap.com, filter tokens by market-cap above target see configurations.py
- retrieve historical close price at in range `start_date`-`end_date` in configurations.py, and at granularity specified.
- for filtered tokens, optimize portfolio weights for maximum sharpe (highest return, relatively low volatility), and variance(highest return for low volatility)
- write portfolio to portfolio_sharpe.json, portfolio_var.json under data directory.

![alt text](https://github.com/finai-solutions/mpt/blob/main/img/portfolio.png?raw=true)

## experiments on granularity effect on portfolio

max sharpe portfolio via low granularity 1day per record resolution results in a portfolio with low volatility, and relatively lower return, and experiments shows the higher the granularity the higher the volatility, and return of the max sharpe portfolio.

## returns predictions

use recurrent neural networks to predict portfolio return in the future

![the network isn't trained long enough, the example is dummy](https://github.com/finai-solutions/mpt/blob/main/img/portfolios_predictions.png?raw=true)

## TODO

- coinbase free pro api doesn't retrieve all pairs
- coinbase free pro api fails on some pairs query
