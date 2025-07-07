import numpy as np
import pandas as pd
from scipy.stats import norm
import logging

logging.basicConfig(level=logging.INFO)


# === SPOT POSITION DELTA ===
def calculate_spot_delta(position_size: float, spot_price: float) -> float:
    return position_size * spot_price  # delta = quantity × price


# === PERPETUAL HEDGE SIZE CALCULATION ===
def calculate_perp_hedge_size(spot_delta: float, perp_price: float, contract_size: float = 1) -> float:
    return -spot_delta / (perp_price * contract_size)  # contracts to short (negative for sell)


# === BLACK-SCHOLES GREEKS ===
def calculate_option_greeks(S, K, T, r, sigma, option_type='call'):
    try:
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if option_type == 'call':
            delta = norm.cdf(d1)
            theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))) - r * K * np.exp(-r * T) * norm.cdf(d2)
        else:
            delta = -norm.cdf(-d1)
            theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))) + r * K * np.exp(-r * T) * norm.cdf(-d2)

        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        vega = S * norm.pdf(d1) * np.sqrt(T)

        return {
            'delta': delta,
            'gamma': gamma,
            'theta': theta / 365,
            'vega': vega / 100
        }
    except Exception as e:
        logging.error(f"Greek calculation error: {e}")
        return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0}


# === VALUE AT RISK (VAR) ===
def calculate_var(portfolio_returns, confidence_level=0.95):
    return -np.percentile(portfolio_returns, (1 - confidence_level) * 100)


# === MAX DRAWDOWN ===
def max_drawdown(equity_curve):
    peak = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - peak) / peak
    return np.min(drawdown)


# === CORRELATION MATRIX ===
def correlation_matrix(price_data_dict):
    df = pd.DataFrame(price_data_dict)
    return df.pct_change().corr()


# === DELTA EXPOSURE ALERT ===
def check_and_alert_delta(delta_exposure: float, threshold: float):
    if abs(delta_exposure) > threshold:
        return {
            'alert': True,
            'message': f"⚠️ Delta exposure ${delta_exposure:,.2f} exceeds threshold ${threshold:,}. Recommend hedging!"
        }
    return {
        'alert': False,
        'message': f"✅ Delta exposure ${delta_exposure:,.2f} within safe threshold."
    }


# === RISK SUMMARY REPORT ===
def generate_risk_report(position, spot_price, perp_price, returns, equity_curve, threshold):
    delta = calculate_spot_delta(position['size'], spot_price)
    hedge_size = calculate_perp_hedge_size(delta, perp_price)

    alert = check_and_alert_delta(delta, threshold)

    var = calculate_var(returns)
    drawdown = max_drawdown(equity_curve)

    report = {
        'delta_exposure': delta,
        'recommended_hedge_contracts': hedge_size,
        'VaR_95%': var,
        'Max_Drawdown': drawdown,
        'Alert': alert
    }
    return report


# === EXAMPLE USAGE ===
if __name__ == "__main__":
    # Example data
    position = {'asset': 'BTC', 'size': 3}
    spot_price = 60000
    perp_price = 60000
    delta_threshold = 10000

    # Simulated return & equity data
    returns = np.random.normal(0, 0.02, 100)
    equity = np.cumprod(1 + returns)

    risk_report = generate_risk_report(position, spot_price, perp_price, returns, equity, delta_threshold)

    for k, v in risk_report.items():
        print(f"{k}: {v}")
