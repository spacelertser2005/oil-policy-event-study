"""
Event Study Analysis: Presidential Oil Policy Whipsaw Effect

This script implements the full event study pipeline:
1. Load and merge price/return data
2. Calculate abnormal returns using the market model
3. Compute CARs across multiple event windows
4. Test the whipsaw asymmetry hypothesis
5. Run the credibility decay regression
6. Output publication-ready tables and figures

Usage:
    python src/event_study.py

Output:
    output/tables/  - CAR results, asymmetry tests, regression tables
    output/figures/ - CAR plots, credibility decay visualization
"""

import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from event_catalog import get_event_catalog

# ── CONFIGURATION ─────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
OUTPUT_DIR = Path(__file__).parent.parent / "output"
TABLES_DIR = OUTPUT_DIR / "tables"
FIGURES_DIR = OUTPUT_DIR / "figures"

ESTIMATION_WINDOW = 200  # trading days
EVENT_WINDOWS = {
    "narrow": (-1, 1),
    "medium": (-2, 2),
    "wide": (-5, 5),
}
DEFAULT_WINDOW = "narrow"

# Ensure output dirs exist
TABLES_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


# ── DATA LOADING ──────────────────────────────────────────────────────────────

def load_fred_series(filename, col_name):
    """Load a FRED CSV and return a clean Series indexed by date."""
    path = DATA_DIR / filename
    df = pd.read_csv(path)
    date_col = df.columns[0]
    val_col = df.columns[1]
    df[date_col] = pd.to_datetime(df[date_col])
    df[val_col] = pd.to_numeric(df[val_col], errors='coerce')
    df = df.dropna(subset=[val_col])
    df = df.rename(columns={date_col: 'date', val_col: col_name})
    df = df.set_index('date').sort_index()
    return df


def load_all_data():
    """Load and merge all data sources."""
    print("Loading data...")
    
    # Oil prices
    wti = load_fred_series("DCOILWTICO.csv", "wti")
    brent = load_fred_series("DCOILBRENTEU.csv", "brent")
    
    # Volatility
    ovx = load_fred_series("OVXCLS.csv", "ovx")
    vix = load_fred_series("VIXCLS.csv", "vix")
    
    # Merge all into one DataFrame
    data = wti.join(brent, how='outer').join(ovx, how='outer').join(vix, how='outer')
    
    # Calculate log returns
    data['wti_ret'] = np.log(data['wti'] / data['wti'].shift(1))
    data['brent_ret'] = np.log(data['brent'] / data['brent'].shift(1))
    
    # Filter to study period
    data = data.loc['2016-01-01':]
    
    print(f"  WTI: {wti.index.min().date()} to {wti.index.max().date()} ({len(wti)} obs)")
    print(f"  Brent: {brent.index.min().date()} to {brent.index.max().date()} ({len(brent)} obs)")
    print(f"  OVX: {ovx.index.min().date()} to {ovx.index.max().date()} ({len(ovx)} obs)")
    print(f"  VIX: {vix.index.min().date()} to {vix.index.max().date()} ({len(vix)} obs)")
    print(f"  Combined panel: {data.index.min().date()} to {data.index.max().date()} ({len(data)} trading days)")
    
    return data


def load_equity_data():
    """Load CRSP oil stock and S&P 500 data."""
    stocks_path = DATA_DIR / "crsp_oil_stocks.csv"
    sp500_path = DATA_DIR / "sp500_index.csv"
    
    if not stocks_path.exists() or not sp500_path.exists():
        print("  CRSP/SP500 data not found — equity analysis will be skipped.")
        return None, None
    
    stocks = pd.read_csv(stocks_path, parse_dates=['date'])
    sp500 = pd.read_csv(sp500_path, parse_dates=['date'])
    
    # Clean returns
    stocks['ret'] = pd.to_numeric(stocks['ret'], errors='coerce')
    sp500['sprtrn'] = pd.to_numeric(sp500['sprtrn'], errors='coerce')
    
    print(f"  CRSP stocks: {len(stocks)} obs, tickers: {sorted(stocks['ticker'].unique())}")
    print(f"  S&P 500: {sp500['date'].min().date()} to {sp500['date'].max().date()}")
    
    return stocks, sp500


# ── EVENT STUDY CORE ──────────────────────────────────────────────────────────

def get_trading_days(data):
    """Return sorted array of trading dates from the data index."""
    return data.index.values


def find_event_day_index(trading_days, event_date):
    """Find the position of the event date in the trading day array.
    If event falls on a non-trading day, use the next trading day."""
    event_ts = np.datetime64(pd.Timestamp(event_date))
    idx = np.searchsorted(trading_days, event_ts)
    if idx >= len(trading_days):
        return None
    # If exact match or next available trading day
    return idx


def calculate_car_mean_adjusted(data, return_col, event_date, 
                                 estimation_window=200, 
                                 event_window=(-1, 1)):
    """
    Calculate CAR using the mean-adjusted model.
    
    AR_t = R_t - E[R]
    where E[R] = mean return over the estimation window
    CAR = sum of AR_t over the event window
    """
    trading_days = get_trading_days(data)
    event_idx = find_event_day_index(trading_days, event_date)
    
    if event_idx is None:
        return None
    
    # Estimation window: [event_idx - estimation_window - |event_window[0]|, event_idx + event_window[0])
    est_end = event_idx + event_window[0]  # day before event window starts
    est_start = est_end - estimation_window
    
    if est_start < 0 or event_idx + event_window[1] >= len(trading_days):
        return None
    
    # Get returns
    est_dates = trading_days[est_start:est_end]
    event_dates = trading_days[event_idx + event_window[0]:event_idx + event_window[1] + 1]
    
    est_returns = data.loc[est_dates, return_col].dropna()
    event_returns = data.loc[event_dates, return_col].dropna()
    
    if len(est_returns) < estimation_window * 0.8:  # require at least 80% of estimation window
        return None
    
    # Mean-adjusted model
    expected_return = est_returns.mean()
    est_std = est_returns.std()
    
    # Abnormal returns
    ar = event_returns - expected_return
    car = ar.sum()
    
    # T-statistic (simple)
    n_event_days = len(event_returns)
    car_std = est_std * np.sqrt(n_event_days)
    t_stat = car / car_std if car_std > 0 else 0
    p_value = 2 * stats.t.sf(abs(t_stat), df=len(est_returns) - 1)
    
    return {
        'car': car,
        'ar_series': ar,
        't_stat': t_stat,
        'p_value': p_value,
        'n_est_days': len(est_returns),
        'n_event_days': n_event_days,
        'expected_return': expected_return,
        'est_std': est_std,
        'event_dates': event_dates,
    }


def run_event_study(data, events, return_col='wti_ret', 
                     estimation_window=200, event_windows=None):
    """
    Run the full event study across all events and windows.
    Returns a DataFrame of results.
    """
    if event_windows is None:
        event_windows = EVENT_WINDOWS
    
    results = []
    
    for _, event in events.iterrows():
        for window_name, (w_start, w_end) in event_windows.items():
            result = calculate_car_mean_adjusted(
                data, return_col, event['date'],
                estimation_window=estimation_window,
                event_window=(w_start, w_end)
            )
            
            if result is not None:
                results.append({
                    'date': event['date'],
                    'description': event['description'],
                    'phase': event['phase'],
                    'domain': event['domain'],
                    'direction': event['direction'],
                    'expected_sign': event['expected_sign'],
                    'whipsaw_flag': event['whipsaw_flag'],
                    'is_whipsaw': event['is_whipsaw'],
                    'whipsaw_seq': event['whipsaw_seq'],
                    'cumulative_whipsaw_count': event['cumulative_whipsaw_count'],
                    'days_since_prior_reversal': event['days_since_prior_reversal'],
                    'window': window_name,
                    'window_range': f"[{w_start},{w_end}]",
                    'car': result['car'],
                    'car_pct': result['car'] * 100,
                    't_stat': result['t_stat'],
                    'p_value': result['p_value'],
                    'significant_10': result['p_value'] < 0.10,
                    'significant_05': result['p_value'] < 0.05,
                    'significant_01': result['p_value'] < 0.01,
                    'correct_sign': (np.sign(result['car']) == event['expected_sign']),
                })
    
    return pd.DataFrame(results)


# ── EQUITY EVENT STUDY ────────────────────────────────────────────────────────

def run_equity_event_study(stocks, sp500, events, estimation_window=200,
                            event_window=(-1, 1)):
    """
    Run event study on individual oil stocks using the market model.
    AR_t = R_it - (alpha_i + beta_i * R_mt)
    """
    results = []
    tickers = sorted(stocks['ticker'].unique())
    
    # Merge stock and market returns
    sp500_daily = sp500.set_index('date')['sprtrn']
    
    for ticker in tickers:
        stock_data = stocks[stocks['ticker'] == ticker].set_index('date')['ret'].sort_index()
        trading_days = stock_data.index.values

        for _, event in events.iterrows():
            event_date = event['date']

            # Find event date index in stock data
            event_idx = find_event_day_index(trading_days, event_date)
            
            if event_idx is None:
                continue
            
            # Estimation window
            est_end = event_idx + event_window[0]
            est_start = est_end - estimation_window
            
            if est_start < 0 or event_idx + event_window[1] >= len(trading_days):
                continue
            
            est_dates = trading_days[est_start:est_end]
            evt_dates = trading_days[event_idx + event_window[0]:event_idx + event_window[1] + 1]
            
            # Get returns for estimation window
            est_stock = stock_data.loc[est_dates].dropna()
            est_market = sp500_daily.reindex(est_dates).dropna()
            
            # Align
            common_est = est_stock.index.intersection(est_market.index)
            if len(common_est) < estimation_window * 0.7:
                continue
            
            est_stock = est_stock.loc[common_est]
            est_market = est_market.loc[common_est]
            
            # Market model regression: R_i = alpha + beta * R_m
            beta, alpha = np.polyfit(est_market.values, est_stock.values, 1)
            
            # Event window returns
            evt_stock = stock_data.reindex(evt_dates).dropna()
            evt_market = sp500_daily.reindex(evt_dates).dropna()
            common_evt = evt_stock.index.intersection(evt_market.index)
            
            if len(common_evt) == 0:
                continue
            
            evt_stock = evt_stock.loc[common_evt]
            evt_market = evt_market.loc[common_evt]
            
            # Abnormal returns
            expected = alpha + beta * evt_market.values
            ar = evt_stock.values - expected
            car = ar.sum()
            
            # Residual std from estimation
            est_predicted = alpha + beta * est_market.values
            residuals = est_stock.values - est_predicted
            res_std = residuals.std()
            
            t_stat = car / (res_std * np.sqrt(len(common_evt))) if res_std > 0 else 0
            p_value = 2 * stats.t.sf(abs(t_stat), df=len(common_est) - 2)
            
            results.append({
                'ticker': ticker,
                'date': event['date'],
                'description': event['description'],
                'direction': event['direction'],
                'expected_sign': event['expected_sign'],
                'whipsaw_flag': event['whipsaw_flag'],
                'is_whipsaw': event['is_whipsaw'],
                'car': car,
                'car_pct': car * 100,
                't_stat': t_stat,
                'p_value': p_value,
                'alpha': alpha,
                'beta': beta,
            })
    
    return pd.DataFrame(results)


# ── HYPOTHESIS TESTS ──────────────────────────────────────────────────────────

def test_whipsaw_asymmetry(results):
    """
    Test the core hypothesis: CAR(reversal) ≠ -CAR(original)
    
    If reversals fully undo originals, the sum should be ~0.
    If there's an uncertainty premium, the net effect is non-zero.
    """
    print("\n" + "="*70)
    print("WHIPSAW ASYMMETRY TEST")
    print("="*70)
    
    narrow = results[results['window'] == DEFAULT_WINDOW].copy()
    
    originals = narrow[narrow['whipsaw_flag'] == 'original']
    reversals = narrow[narrow['whipsaw_flag'].isin(['reversal', 're_reversal'])]
    
    if len(originals) == 0 or len(reversals) == 0:
        print("  Insufficient events for asymmetry test.")
        return None
    
    mean_car_original = originals['car'].mean()
    mean_car_reversal = reversals['car'].mean()
    net_effect = mean_car_original + mean_car_reversal
    
    # If reversals perfectly undo originals:
    # mean(CAR_original) + mean(CAR_reversal) = 0
    # Test: net_effect ≠ 0
    all_cars = pd.concat([originals['car'], reversals['car']])
    t_stat_net, p_value_net = stats.ttest_1samp(all_cars, 0)
    
    # Also test whether |CAR_reversal| ≠ |CAR_original|
    abs_originals = originals['car'].abs().mean()
    abs_reversals = reversals['car'].abs().mean()
    
    print(f"\n  Original events (n={len(originals)}):")
    print(f"    Mean CAR: {mean_car_original*100:.3f}%")
    print(f"    Mean |CAR|: {abs_originals*100:.3f}%")
    print(f"\n  Reversal events (n={len(reversals)}):")
    print(f"    Mean CAR: {mean_car_reversal*100:.3f}%")
    print(f"    Mean |CAR|: {abs_reversals*100:.3f}%")
    print(f"\n  Net effect (original + reversal): {net_effect*100:.3f}%")
    print(f"  |Reversal| / |Original| ratio: {abs_reversals/abs_originals:.3f}")
    print(f"\n  H0: Net effect = 0 (reversals fully undo originals)")
    print(f"  t-statistic: {t_stat_net:.3f}")
    print(f"  p-value: {p_value_net:.4f}")
    
    if p_value_net < 0.05:
        print(f"  -> REJECT H0 at 5% level: Whipsaw uncertainty premium EXISTS")
    elif p_value_net < 0.10:
        print(f"  -> REJECT H0 at 10% level: Weak evidence of whipsaw premium")
    else:
        print(f"  -> FAIL TO REJECT H0: No significant whipsaw premium")
    
    return {
        'n_originals': len(originals),
        'n_reversals': len(reversals),
        'mean_car_original': mean_car_original,
        'mean_car_reversal': mean_car_reversal,
        'net_effect': net_effect,
        'abs_ratio': abs_reversals / abs_originals,
        't_stat': t_stat_net,
        'p_value': p_value_net,
    }


def test_credibility_decay(results):
    """
    Test whether |CAR| decreases as cumulative whipsaw count increases.
    
    |CAR_t| = alpha + beta * cumulative_whipsaw_count_t + epsilon
    
    Negative beta = credibility decay (markets discount announcements)
    Positive beta = uncertainty amplification (markets overreact)
    """
    print("\n" + "="*70)
    print("CREDIBILITY DECAY REGRESSION")
    print("="*70)
    
    narrow = results[results['window'] == DEFAULT_WINDOW].copy()
    narrow['abs_car'] = narrow['car'].abs()
    
    # Only use events that are part of whipsaw sequences
    whipsaw_events = narrow[narrow['cumulative_whipsaw_count'] > 0].copy()
    
    if len(whipsaw_events) < 5:
        print("  Insufficient whipsaw events for regression.")
        return None
    
    x = whipsaw_events['cumulative_whipsaw_count'].values
    y = whipsaw_events['abs_car'].values
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    print(f"\n  Regression: |CAR| = {intercept*100:.4f}% + {slope*100:.4f}% * cumulative_whipsaw_count")
    print(f"  N = {len(whipsaw_events)} events")
    print(f"  R^2 = {r_value**2:.4f}")
    print(f"  beta (slope) = {slope*100:.4f}% per additional whipsaw")
    print(f"  SE(beta) = {std_err*100:.4f}%")
    print(f"  t-statistic = {slope/std_err:.3f}")
    print(f"  p-value = {p_value:.4f}")
    
    if slope < 0 and p_value < 0.05:
        print(f"  -> CREDIBILITY DECAY: Markets increasingly discount announcements")
    elif slope > 0 and p_value < 0.05:
        print(f"  -> UNCERTAINTY AMPLIFICATION: Each whipsaw makes markets react MORE")
    else:
        print(f"  -> No significant relationship between whipsaw count and |CAR|")
    
    return {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_value**2,
        'p_value': p_value,
        'std_err': std_err,
        'n': len(whipsaw_events),
    }


# ── OUTPUT ────────────────────────────────────────────────────────────────────

def print_car_summary(results, return_label='WTI'):
    """Print a formatted summary table of CAR results."""
    print(f"\n{'='*70}")
    print(f"CUMULATIVE ABNORMAL RETURNS — {return_label}")
    print(f"{'='*70}")
    
    for window_name in EVENT_WINDOWS:
        w = results[results['window'] == window_name]
        w_range = w['window_range'].iloc[0] if len(w) > 0 else ''
        
        print(f"\n  Event Window: {w_range}")
        print(f"  {'Date':<12} {'CAR%':>7} {'t-stat':>7} {'p':>6} {'Sig':>5} {'Dir':>12} {'Whipsaw':>10}  Description")
        print(f"  {'-'*12} {'-'*7} {'-'*7} {'-'*6} {'-'*5} {'-'*12} {'-'*10}  {'-'*40}")
        
        for _, r in w.sort_values('date').iterrows():
            sig = '***' if r['significant_01'] else '**' if r['significant_05'] else '*' if r['significant_10'] else ''
            desc = r['description'][:45]
            print(f"  {r['date'].strftime('%Y-%m-%d')} {r['car_pct']:>7.3f} {r['t_stat']:>7.3f} {r['p_value']:>6.3f} {sig:>5} {r['direction']:>12} {r['whipsaw_flag']:>10}  {desc}")
        
        # Summary stats
        print(f"\n  Summary: Mean CAR = {w['car_pct'].mean():.3f}%, "
              f"Median = {w['car_pct'].median():.3f}%, "
              f"Significant at 5%: {w['significant_05'].sum()}/{len(w)}")


def save_results_tables(results, asymmetry, decay):
    """Save publication-ready CSV tables."""
    
    # Table 1: All CARs
    narrow = results[results['window'] == DEFAULT_WINDOW].copy()
    table1 = narrow[['date', 'description', 'direction', 'whipsaw_flag', 
                      'car_pct', 't_stat', 'p_value', 'significant_05']].copy()
    table1['date'] = table1['date'].dt.strftime('%Y-%m-%d')
    table1.to_csv(TABLES_DIR / 'table1_car_results.csv', index=False)
    
    # Table 2: CARs by event type
    table2 = narrow.groupby(['direction', 'whipsaw_flag']).agg(
        n=('car', 'count'),
        mean_car_pct=('car_pct', 'mean'),
        median_car_pct=('car_pct', 'median'),
        pct_significant=('significant_05', 'mean'),
    ).round(3)
    table2.to_csv(TABLES_DIR / 'table2_car_by_type.csv')
    
    # Table 3: Robustness across windows
    table3 = results.groupby('window').agg(
        n=('car', 'count'),
        mean_car_pct=('car_pct', 'mean'),
        mean_abs_car_pct=('car_pct', lambda x: x.abs().mean()),
        pct_correct_sign=('correct_sign', 'mean'),
        pct_significant_05=('significant_05', 'mean'),
    ).round(3)
    table3.to_csv(TABLES_DIR / 'table3_robustness_windows.csv')
    
    # Table 4: Whipsaw asymmetry
    if asymmetry:
        table4 = pd.DataFrame([asymmetry])
        table4.to_csv(TABLES_DIR / 'table4_whipsaw_asymmetry.csv', index=False)
    
    # Table 5: Credibility decay
    if decay:
        table5 = pd.DataFrame([decay])
        table5.to_csv(TABLES_DIR / 'table5_credibility_decay.csv', index=False)
    
    print(f"\n  Tables saved to {TABLES_DIR}/")


def create_figures(results, data, events):
    """Create publication-quality figures."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        
        plt.rcParams.update({
            'font.family': 'serif',
            'font.size': 10,
            'axes.titlesize': 12,
            'axes.labelsize': 11,
            'figure.figsize': (10, 6),
            'figure.dpi': 150,
        })
        
        # Figure 1: WTI price with event markers
        fig, ax = plt.subplots(figsize=(12, 6))
        price_data = data['wti'].dropna().loc['2017-01-01':]
        ax.plot(price_data.index, price_data.values, color='#2c3e50', linewidth=0.8, alpha=0.9, label='WTI Price')

        direction_labels = {
            'anti_supply': 'Anti-supply event',
            'pro_supply': 'Pro-supply event',
            'ambiguous': 'Ambiguous event',
        }
        direction_colors = {
            'anti_supply': '#e74c3c',
            'pro_supply': '#27ae60',
            'ambiguous': '#f39c12',
        }
        used_labels = set()

        for _, e in events.iterrows():
            if e['date'] in price_data.index or (e['date'] >= price_data.index.min() and e['date'] <= price_data.index.max()):
                color = direction_colors.get(e['direction'], '#f39c12')
                marker = 'v' if e['is_whipsaw'] else '^'
                nearest_date = price_data.index[price_data.index.get_indexer([e['date']], method='nearest')[0]]
                label = direction_labels.get(e['direction'])
                if label is not None and label not in used_labels:
                    used_labels.add(label)
                else:
                    label = None
                ax.scatter(nearest_date, price_data.loc[nearest_date],
                          color=color, marker=marker, s=60, zorder=5,
                          edgecolors='black', linewidths=0.5, label=label)

        ax.set_xlabel('Date')
        ax.set_ylabel('WTI Spot Price ($/barrel)')
        ax.set_title('WTI Crude Oil Price with Policy Event Markers')
        ax.legend(loc='upper left')
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / 'fig1_wti_price_events.png', dpi=150, bbox_inches='tight')
        plt.close()
        
        # Figure 2: CAR distribution by whipsaw status
        narrow = results[results['window'] == DEFAULT_WINDOW]
        fig, ax = plt.subplots(figsize=(8, 5))
        
        originals = narrow[narrow['whipsaw_flag'] == 'original']['car_pct']
        reversals = narrow[narrow['whipsaw_flag'].isin(['reversal', 're_reversal'])]['car_pct']
        non_whipsaw = narrow[narrow['whipsaw_flag'] == 'none']['car_pct']
        
        positions = [1, 2, 3]
        bp = ax.boxplot([originals, reversals, non_whipsaw], positions=positions,
                       widths=0.6, patch_artist=True)
        colors = ['#3498db', '#e74c3c', '#95a5a6']
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax.set_xticklabels(['Original\nAnnouncements', 'Reversals', 'Non-Whipsaw'])
        ax.set_ylabel('CAR (%)')
        ax.set_title('Distribution of CARs by Whipsaw Status [-1,+1] Window')
        ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / 'fig2_car_by_whipsaw.png', dpi=150, bbox_inches='tight')
        plt.close()
        
        # Figure 3: Credibility decay — |CAR| vs cumulative whipsaw count
        fig, ax = plt.subplots(figsize=(8, 5))
        whipsaw_events = narrow[narrow['cumulative_whipsaw_count'] > 0].copy()
        
        if len(whipsaw_events) > 3:
            x = whipsaw_events['cumulative_whipsaw_count']
            y = whipsaw_events['car'].abs() * 100
            
            ax.scatter(x, y, color='#2c3e50', s=60, zorder=5, edgecolors='white', linewidths=0.5)
            
            # Regression line
            slope, intercept, _, _, _ = stats.linregress(x, y)
            x_line = np.linspace(x.min(), x.max(), 100)
            ax.plot(x_line, intercept + slope * x_line, color='#e74c3c', 
                   linewidth=2, linestyle='--', label=f'β = {slope:.3f}%/whipsaw')
            
            ax.set_xlabel('Cumulative Whipsaw Count')
            ax.set_ylabel('|CAR| (%)')
            ax.set_title('Policy Credibility Decay: |CAR| vs. Accumulated Reversals')
            ax.legend()
        
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / 'fig3_credibility_decay.png', dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"\n  Figures saved to {FIGURES_DIR}/")
        
    except Exception as e:
        print(f"\n  Warning: Could not generate figures: {e}")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("="*70)
    print("OIL POLICY WHIPSAW EVENT STUDY")
    print("Presidential Policy Credibility and Oil Market Volatility")
    print("="*70)
    
    # Load data
    data = load_all_data()
    events = get_event_catalog()
    
    print(f"\n  Event catalog: {len(events)} events")
    print(f"    Originals: {(events['whipsaw_flag'] == 'original').sum()}")
    print(f"    Reversals: {events['is_whipsaw'].sum()}")
    print(f"    Non-whipsaw: {(events['whipsaw_flag'] == 'none').sum()}")
    
    # ── Study 1: WTI Event Study ──
    print("\n" + "="*70)
    print("STUDY 1: WTI CRUDE OIL EVENT STUDY")
    print("="*70)
    
    wti_results = run_event_study(data, events, return_col='wti_ret')
    print_car_summary(wti_results, 'WTI')
    
    # ── Study 1b: Brent Robustness ──
    print("\n" + "="*70)
    print("ROBUSTNESS: BRENT CRUDE OIL")
    print("="*70)
    
    brent_results = run_event_study(data, events, return_col='brent_ret')
    print_car_summary(brent_results, 'Brent')
    
    # ── Study 2: Whipsaw Asymmetry Test ──
    asymmetry = test_whipsaw_asymmetry(wti_results)
    
    # ── Study 3: Credibility Decay ──
    decay = test_credibility_decay(wti_results)
    
    # ── Study 4: Equity Cross-Section (if data available) ──
    stocks, sp500 = load_equity_data()
    equity_results = None
    if stocks is not None and sp500 is not None:
        print("\n" + "="*70)
        print("STUDY 4: EQUITY CROSS-SECTIONAL ANALYSIS")
        print("="*70)
        
        equity_results = run_equity_event_study(stocks, sp500, events)
        
        if len(equity_results) > 0:
            # Summary by firm type
            firm_types = {
                'Major': ['XOM', 'CVX'],
                'E&P': ['COP', 'EOG', 'OXY', 'DVN'],
                'Refiner': ['VLO', 'MPC'],
                'OFS': ['SLB', 'HAL'],
            }
            
            for ftype, tickers in firm_types.items():
                subset = equity_results[equity_results['ticker'].isin(tickers)]
                if len(subset) > 0:
                    print(f"\n  {ftype} ({', '.join(tickers)}):")
                    print(f"    Mean CAR: {subset['car_pct'].mean():.3f}%")
                    print(f"    Whipsaw events mean CAR: {subset[subset['is_whipsaw']]['car_pct'].mean():.3f}%")
                    print(f"    Non-whipsaw mean CAR: {subset[~subset['is_whipsaw']]['car_pct'].mean():.3f}%")
            
            equity_results.to_csv(TABLES_DIR / 'table6_equity_cars.csv', index=False)
    
    # ── Save outputs ──
    save_results_tables(wti_results, asymmetry, decay)
    create_figures(wti_results, data, events)
    
    # Save full results for further analysis
    wti_results.to_csv(TABLES_DIR / 'full_wti_results.csv', index=False)
    brent_results.to_csv(TABLES_DIR / 'full_brent_results.csv', index=False)
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print(f"\n  Results saved to: {TABLES_DIR}/")
    print(f"  Figures saved to: {FIGURES_DIR}/")
    print(f"\n  Next steps:")
    print(f"    1. Review table1_car_results.csv for individual event CARs")
    print(f"    2. Check table4_whipsaw_asymmetry.csv for the core hypothesis test")
    print(f"    3. Check table5_credibility_decay.csv for the decay regression")
    print(f"    4. Verify event catalog dates against primary sources")


if __name__ == "__main__":
    main()
