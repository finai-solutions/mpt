import numpy as np
import matplotlib.pyplot as plt

def plot(hist_prices, tickers, balance, return_period, mean_return, cov, equally_weighted_return, equally_weighted_std, equally_weighted_weights, gmv_return, gmv_std, gmv_weights, max_sharpe_return, max_sharpe_std, max_sharpe_weights):
    # simulate randomized portfolios
    n_portfolios = len(hist_prices.columns)
    portfolio_returns = []
    portfolio_stds = []
    for i in range(n_portfolios):
        weights = np.random.rand(len(tickers))
        weights = weights / sum(weights)
        port_return = portfolio_return(weights, mean_return, return_period)
        port_std = portfolio_std(weights, cov)
        sharpe_ratio = portfolio_sharpe(port_return, port_std)
        portfolio_returns.append(port_return)
        portfolio_stds.append(port_std)


    # figure out the range for target return. 10% lower than min value, 10% higher than max value.
    min_return = min(portfolio_returns+[gmv_return])
    min_return = min_return*1.1 if min_return<0 else min_return*0.9
    max_return = max(portfolio_returns+[max_sharpe_return])
    max_return = max_return*1.1 if max_return>0 else max_return*0.9
    target_returns = np.linspace(min_return, max_return, 100)
    efficient_frontier_risk = efficient_frontier(target_returns, cov, mean_return, equally_weighted_weights, len(tickers))

    # portfolio value over time
    date_range = []
    equally_weighted_portfolio = []
    gmv_portfolio = []
    max_sharpe_portfolio = []
    FINAL_BALANCE = 0
    for index, day in hist_prices.iterrows():
        equal_weighted_port_val = 0
        gmv_port_val = 0
        max_sharpe_port_val = 0
        for i, asset in enumerate(tickers):
            equal_weighted_port_val += equally_weighted_weights[i] * balance / hist_prices[asset].iloc[1] * day[asset]
            gmv_port_val += gmv_weights[i] * balance / hist_prices[asset].iloc[1] * day[asset]
            max_sharpe_port_val += max_sharpe_weights[i] * balance / hist_prices[asset].iloc[1] * day[asset]
        date_range.append(index)
        equally_weighted_portfolio.append(equal_weighted_port_val)
        gmv_portfolio.append(gmv_port_val)
        max_sharpe_portfolio.append(max_sharpe_port_val)

    # plot return vs volatility
    plt.plot(date_range, equally_weighted_portfolio, label='equally weighted portfolio')
    plt.plot(date_range, gmv_portfolio, label='global min variance portfolio')
    plt.plot(date_range, max_sharpe_portfolio, label='max sharpe portfolio')

    plt.title('Portfolio Value')
    plt.xlabel('Date')
    plt.ylabel('Value in dollars')

    plt.legend()
    plt.savefig(get_write_path('portfolio', ext='png'))
    plt.clf()

    # Display portfolios
    plt.scatter(portfolio_stds, portfolio_returns, marker='o', s=3, label='Random')
    plt.plot(efficient_frontier_risk, target_returns, 'og', markersize=3, label='Efficient Frontier')
    plt.plot(equally_weighted_std, equally_weighted_return, 'or', label='Equally Weighted')
    plt.plot(gmv_std, gmv_return, 'oc', label='Global Minimum Variance')
    plt.plot(max_sharpe_std, max_sharpe_return, 'om', label='Max Sharpe')
    plt.title('Volatility vs Returns for Different Portfolios')
    plt.xlabel('Expected Volatility')
    plt.ylabel('Expected Returns')
    plt.legend()
    plt.savefig(get_write_path('volatility', ext='png'))
