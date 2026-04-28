"""
Event Study Analysis: Presidential Oil Policy Whipsaw Effect

This script implements the full event study pipeline:
1. Load and merge price/return data
2. Calculate abnormal returns (mean-adjusted and AR(1) models)
3. Compute CARs across multiple event windows
4. Test the whipsaw asymmetry hypothesis
5. Run the credibility decay regression
6. Statistical inference: Boehmer (1991), Kolari-Pynnonen (2010)
7. Robustness: placebo test, communication channel analysis, AR(1)
8. Output publication-ready tables and figures

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
import hashlib
import json
import warnings

from event_catalog import get_event_catalog

# Suppress pandas 2.x Copy-on-Write FutureWarnings (false positives on
# column assignment to DataFrames we own) and NaN-comparison RuntimeWarnings.
warnings.filterwarnings('ignore', category=FutureWarning,
                        message='.*ChainedAssignment.*')
warnings.filterwarnings('ignore', category=FutureWarning, module='pandas')
warnings.filterwarnings('ignore', category=RuntimeWarning, message='invalid value')

# ── CONFIGURATION ─────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
OUTPUT_DIR = Path(__file__).parent.parent / "output"
TABLES_DIR = OUTPUT_DIR / "tables"
FIGURES_DIR = OUTPUT_DIR / "figures"

ESTIMATION_WINDOW = 200  # trading days
ESTIMATION_GAP = 5       # trading-day gap between estimation and event windows
EVENT_WINDOWS = {
    "narrow": (-1, 1),
    "medium": (-2, 2),
    "wide": (-5, 5),
}
DEFAULT_WINDOW = "narrow"
PLACEBO_ITERATIONS = 1000

# Ensure output dirs exist
TABLES_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


# ── DATA LOADING ──────────────────────────────────────────────────────────────

def load_fred_series(filename, col_name):
    """Load a FRED CSV and return a clean Series indexed by date."""
    path = DATA_DIR / filename
    df = pd.read_csv(path).copy()
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


# ── DATA INTEGRITY ────────────────────────────────────────────────────────────

def verify_data_files():
    """Compute SHA-256 checksums of raw data files for version tracking.

    Saves checksums to data/processed/data_checksums.json.  On subsequent
    runs, compares against the saved baseline and warns if any file has
    changed (e.g. a silent FRED revision).
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    checksum_path = PROCESSED_DIR / "data_checksums.json"

    current = {}
    for f in sorted(DATA_DIR.glob('*.csv')):
        h = hashlib.sha256(f.read_bytes()).hexdigest()[:16]
        current[f.name] = h

    if not current:
        print("  No data files found in data/raw/ — skipping checksum verification.")
        return current

    if checksum_path.exists():
        with open(checksum_path) as fh:
            saved = json.load(fh)

        changed = [n for n, h in current.items() if n in saved and saved[n] != h]
        new_files = [n for n in current if n not in saved]

        if changed:
            print(f"  WARNING: {len(changed)} data file(s) changed since last run:")
            for name in changed:
                print(f"    {name}: {saved[name]} -> {current[name]}")
        if new_files:
            print(f"  New data files: {', '.join(new_files)}")
        if not changed and not new_files:
            print("  Data checksums OK — no changes since last run.")
    else:
        print(f"  First run — saving data checksums to {checksum_path}")

    with open(checksum_path, 'w') as fh:
        json.dump(current, fh, indent=2)

    return current


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
    return idx


def check_event_coverage(data, events, return_col='wti_ret'):
    """Warn about events that fall outside the data's date range or lack
    sufficient estimation-window history."""
    trading_days = get_trading_days(data)
    data_start = pd.Timestamp(trading_days[0])
    data_end = pd.Timestamp(trading_days[-1])

    min_required = ESTIMATION_WINDOW + ESTIMATION_GAP + 10

    issues = []
    for _, event in events.iterrows():
        edate = event['date']
        if edate < data_start:
            issues.append((edate, event['description'], 'before data start'))
        elif edate > data_end:
            issues.append((edate, event['description'], 'after data end'))
        else:
            idx = find_event_day_index(trading_days, edate)
            if idx is not None and idx < min_required:
                issues.append((edate, event['description'],
                               f'insufficient estimation window '
                               f'({idx} days available, {min_required} needed)'))

    if issues:
        print(f"\n  WARNING: {len(issues)} event(s) with data-coverage issues:")
        for date, desc, reason in issues:
            print(f"    {date.strftime('%Y-%m-%d')}: {reason} — {desc[:50]}")

    return issues


def calculate_car_mean_adjusted(data, return_col, event_date,
                                estimation_window=ESTIMATION_WINDOW,
                                event_window=(-1, 1),
                                gap=ESTIMATION_GAP):
    """
    Calculate CAR using the mean-adjusted model.

    AR_t = R_t - E[R]   where E[R] = mean return over the estimation window.
    CAR  = sum of AR_t over the event window.

    A gap of *gap* trading days separates the estimation window from the
    event window to prevent event anticipation from contaminating the
    expected-return estimate.
    """
    trading_days = get_trading_days(data)
    event_idx = find_event_day_index(trading_days, event_date)

    if event_idx is None:
        return None

    # Estimation window ends *gap* days before the event window starts
    est_end = event_idx + event_window[0] - gap
    est_start = est_end - estimation_window

    if est_start < 0 or event_idx + event_window[1] >= len(trading_days):
        return None

    # Get returns
    est_dates = trading_days[est_start:est_end]
    event_dates = trading_days[event_idx + event_window[0]:event_idx + event_window[1] + 1]

    est_returns = data.loc[est_dates, return_col].dropna()
    event_returns = data.loc[event_dates, return_col].dropna()

    if len(est_returns) < estimation_window * 0.8:
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
    sar = car / car_std if car_std > 0 else 0

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
        'sar': sar,
        'car_std': car_std,
    }


def calculate_car_ar1(data, return_col, event_date,
                      estimation_window=ESTIMATION_WINDOW,
                      event_window=(-1, 1),
                      gap=ESTIMATION_GAP):
    """
    Calculate CAR using an AR(1) model for expected returns.

    R_t = phi_0 + phi_1 * R_{t-1} + epsilon_t
    AR_t = R_t - (phi_0 + phi_1 * R_{t-1})

    This captures first-order autocorrelation in returns, which the
    mean-adjusted model ignores.
    """
    trading_days = get_trading_days(data)
    event_idx = find_event_day_index(trading_days, event_date)

    if event_idx is None:
        return None

    est_end = event_idx + event_window[0] - gap
    est_start = est_end - estimation_window

    if est_start < 1 or event_idx + event_window[1] >= len(trading_days):
        return None

    est_dates = trading_days[est_start:est_end]
    event_dates_arr = trading_days[event_idx + event_window[0]:event_idx + event_window[1] + 1]

    est_returns = data.loc[est_dates, return_col].dropna()

    if len(est_returns) < estimation_window * 0.8:
        return None

    # Fit AR(1): R_t = phi_0 + phi_1 * R_{t-1}
    y = est_returns.values[1:]
    x = est_returns.values[:-1]
    if len(x) < 2:
        return None
    phi_1, phi_0 = np.polyfit(x, y, 1)

    # Need one extra day before event window for the lagged return
    extended_start = event_idx + event_window[0] - 1
    if extended_start < 0:
        return None
    extended_dates = trading_days[extended_start:event_idx + event_window[1] + 1]
    all_returns = data.loc[extended_dates, return_col].dropna()

    if len(all_returns) < 2:
        return None

    # Abnormal returns in event window
    actual = all_returns.values[1:]
    lagged = all_returns.values[:-1]
    expected = phi_0 + phi_1 * lagged
    ar = actual - expected
    car = ar.sum()

    # Residual std from estimation window
    est_predicted = phi_0 + phi_1 * x
    residuals = y - est_predicted
    res_std = residuals.std()

    n_event_days = len(ar)
    car_std = res_std * np.sqrt(n_event_days)
    t_stat = car / car_std if car_std > 0 else 0
    p_value = 2 * stats.t.sf(abs(t_stat), df=len(est_returns) - 2)
    sar = car / car_std if car_std > 0 else 0

    event_index = all_returns.index[1:]

    return {
        'car': car,
        'ar_series': pd.Series(ar, index=event_index),
        't_stat': t_stat,
        'p_value': p_value,
        'n_est_days': len(est_returns),
        'n_event_days': n_event_days,
        'expected_return': phi_0,
        'est_std': res_std,
        'event_dates': event_dates_arr,
        'sar': sar,
        'car_std': car_std,
    }


def run_event_study(data, events, return_col='wti_ret',
                    estimation_window=ESTIMATION_WINDOW,
                    event_windows=None, model='mean_adjusted'):
    """
    Run the full event study across all events and windows.

    Args:
        model: 'mean_adjusted' (default) or 'ar1'
    """
    if event_windows is None:
        event_windows = EVENT_WINDOWS

    car_fn = calculate_car_ar1 if model == 'ar1' else calculate_car_mean_adjusted

    results = []

    for _, event in events.iterrows():
        for window_name, (w_start, w_end) in event_windows.items():
            result = car_fn(
                data, return_col, event['date'],
                estimation_window=estimation_window,
                event_window=(w_start, w_end)
            )

            if result is not None:
                row = {
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
                    'sar': result['sar'],
                    'car_std': result['car_std'],
                }

                if 'communication' in event.index:
                    row['communication'] = event['communication']
                if 'verified' in event.index:
                    row['verified'] = event['verified']

                results.append(row)

    return pd.DataFrame(results)


# ── EQUITY EVENT STUDY ────────────────────────────────────────────────────────

def run_equity_event_study(stocks, sp500, events,
                           estimation_window=ESTIMATION_WINDOW,
                           event_window=(-1, 1), gap=ESTIMATION_GAP):
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

            # Estimation window with gap
            est_end = event_idx + event_window[0] - gap
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

            n_evt = len(common_evt)
            car_std = res_std * np.sqrt(n_evt)
            t_stat = car / car_std if res_std > 0 else 0
            p_value = 2 * stats.t.sf(abs(t_stat), df=len(common_est) - 2)
            sar = car / car_std if car_std > 0 else 0

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
                'sar': sar,
                'car_std': car_std,
            })

    return pd.DataFrame(results)


# ── STATISTICAL TESTS ─────────────────────────────────────────────────────────

def boehmer_test(cars, car_stds):
    """
    Boehmer, Masumeci, Poulsen (1991) standardized cross-sectional test.

    Instead of using the time-series variance (which assumes constant
    variance), this test standardizes each event's CAR by its own
    estimation-window volatility, then checks whether the average
    standardized abnormal return (SAR) is significantly different from zero.

    This matters when the event itself changes volatility — e.g. a war
    or sanctions announcement that makes prices much more volatile.

    T_BMP = sqrt(N) * mean(SAR) / std(SAR)
    """
    cars = np.asarray(cars, dtype=float)
    car_stds = np.asarray(car_stds, dtype=float)

    valid = np.isfinite(cars) & np.isfinite(car_stds) & (car_stds > 0)
    if valid.sum() < 2:
        return {'t_stat': np.nan, 'p_value': np.nan, 'n': int(valid.sum())}

    sars = cars[valid] / car_stds[valid]
    n = len(sars)

    t_bmp = np.sqrt(n) * sars.mean() / sars.std(ddof=1)
    p_value = 2 * stats.t.sf(abs(t_bmp), df=n - 1)

    return {
        't_stat': t_bmp,
        'p_value': p_value,
        'n': n,
        'mean_sar': float(sars.mean()),
        'std_sar': float(sars.std(ddof=1)),
    }


def kolari_pynnonen_test(equity_results, events):
    """
    Kolari & Pynnonen (2010) adjustment for cross-sectional correlation.

    When multiple stocks react to the same event, their abnormal returns
    are correlated (they all respond to the same news).  The standard
    Boehmer test ignores this, inflating the test statistic.

    K&P deflates the Boehmer stat by a factor that accounts for the
    average pairwise correlation of SARs across stocks:

        T_KP = T_BMP * sqrt((1 - r_bar) / (1 + (N - 1) * r_bar))

    Only applicable to the equity cross-section (multiple stocks per event).
    """
    if equity_results is None or len(equity_results) == 0:
        return None

    # Build SAR matrix: rows = events, columns = stocks
    tickers = sorted(equity_results['ticker'].unique())
    event_dates = sorted(equity_results['date'].unique())

    sar_matrix = []
    event_bmp = []

    for edate in event_dates:
        evt = equity_results[equity_results['date'] == edate]
        if len(evt) < 2:
            continue

        # Boehmer test for this event across stocks
        bmp = boehmer_test(evt['car'].values, evt['car_std'].values)

        row = {}
        for _, r in evt.iterrows():
            if r['car_std'] > 0:
                row[r['ticker']] = r['car'] / r['car_std']
        if len(row) >= 2:
            sar_matrix.append(row)

        if not np.isnan(bmp['t_stat']):
            event_bmp.append({
                'date': edate,
                'n_stocks': len(evt),
                'mean_car_pct': evt['car_pct'].mean(),
                't_bmp': bmp['t_stat'],
                'p_bmp': bmp['p_value'],
            })

    if len(sar_matrix) < 3 or not event_bmp:
        return pd.DataFrame(event_bmp) if event_bmp else None

    # Estimate r_bar from cross-event SAR correlation matrix
    sar_df = pd.DataFrame(sar_matrix)
    corr = sar_df.corr()
    mask = np.triu(np.ones(corr.shape), k=1).astype(bool)
    pairwise = corr.values[mask]
    pairwise = pairwise[np.isfinite(pairwise)]
    r_bar = pairwise.mean() if len(pairwise) > 0 else 0

    # Apply K&P adjustment to each event
    for row in event_bmp:
        n = row['n_stocks']
        denom = 1 + (n - 1) * r_bar
        if denom > 0:
            adj = np.sqrt((1 - r_bar) / denom)
            row['t_kp'] = row['t_bmp'] * adj
            row['p_kp'] = 2 * stats.t.sf(abs(row['t_kp']), df=n - 1)
        else:
            row['t_kp'] = row['t_bmp']
            row['p_kp'] = row['p_bmp']

    result_df = pd.DataFrame(event_bmp)
    result_df.attrs['r_bar'] = r_bar
    result_df.attrs['n_stocks'] = len(tickers)

    return result_df


def expected_sign_test(results):
    """
    Binomial test: do CARs match the expected sign more often than chance?

    Each event is coded with an expected_sign (+1 or -1).  If the study
    is picking up real policy effects, CARs should match their expected
    sign more than 50% of the time.
    """
    narrow = results[results['window'] == DEFAULT_WINDOW].copy()

    n_correct = int(narrow['correct_sign'].sum())
    n_total = len(narrow)

    if n_total == 0:
        return None

    pct_correct = n_correct / n_total

    # Use binomtest (scipy >= 1.7) with binom_test fallback
    try:
        binom_p = stats.binomtest(n_correct, n_total, 0.5,
                                  alternative='greater').pvalue
    except AttributeError:
        binom_p = stats.binom_test(n_correct, n_total, 0.5,
                                   alternative='greater')

    print(f"\n{'='*70}")
    print("EXPECTED-SIGN TEST (Binomial)")
    print(f"{'='*70}")
    print(f"\n  Events with correct sign: {n_correct}/{n_total} ({pct_correct:.1%})")
    print(f"  H0: CARs match expected sign 50% of the time (random)")
    print(f"  p-value (one-sided): {binom_p:.4f}")

    if binom_p < 0.05:
        print(f"  -> SIGNIFICANT: Market responds in the predicted direction")
    else:
        print(f"  -> NOT SIGNIFICANT: Sign accuracy no better than chance")

    # Breakdown by whipsaw type
    for flag in ['original', 'reversal', 're_reversal', 'none']:
        subset = narrow[narrow['whipsaw_flag'] == flag]
        if len(subset) > 0:
            correct = int(subset['correct_sign'].sum())
            total = len(subset)
            print(f"    {flag:>12}: {correct}/{total} correct ({correct/total:.0%})")

    return {
        'n_correct': n_correct,
        'n_total': n_total,
        'pct_correct': pct_correct,
        'p_value': binom_p,
    }


def power_analysis(results):
    """
    Given current N and observed effect variability, estimate the minimum
    detectable effect size and statistical power.

    Answers the practical question: do we have enough events to detect the
    whipsaw effect, or do we need more?
    """
    narrow = results[results['window'] == DEFAULT_WINDOW].copy()

    n = len(narrow)
    if n < 3:
        return None

    car_std = narrow['car'].std()
    observed_mean = abs(narrow['car'].mean())

    # Minimum detectable effect (two-sided, alpha = 0.05)
    alpha = 0.05
    t_crit = stats.t.ppf(1 - alpha / 2, df=n - 1)
    mde = t_crit * car_std / np.sqrt(n)

    # Power at observed effect size via non-central t
    ncp = observed_mean / (car_std / np.sqrt(n)) if car_std > 0 else 0
    if ncp > 0:
        power = (1 - stats.nct.cdf(t_crit, df=n - 1, nc=ncp)
                 + stats.nct.cdf(-t_crit, df=n - 1, nc=ncp))
    else:
        power = alpha

    # How many events for 80% power?
    n_needed_80 = None
    if observed_mean > 0 and car_std > 0:
        for n_try in range(n, 500):
            ncp_try = observed_mean / (car_std / np.sqrt(n_try))
            t_crit_try = stats.t.ppf(1 - alpha / 2, df=max(n_try - 1, 1))
            pow_try = (1 - stats.nct.cdf(t_crit_try, df=n_try - 1, nc=ncp_try)
                       + stats.nct.cdf(-t_crit_try, df=n_try - 1, nc=ncp_try))
            if pow_try >= 0.80:
                n_needed_80 = n_try
                break

    print(f"\n{'='*70}")
    print("POWER ANALYSIS")
    print(f"{'='*70}")
    print(f"\n  Current N: {n} events")
    print(f"  Observed mean |CAR|: {observed_mean*100:.3f}%")
    print(f"  Observed CAR std:    {car_std*100:.3f}%")
    print(f"  Min detectable effect (alpha=0.05): {mde*100:.3f}%")
    print(f"  Power at observed effect: {power:.1%}")
    if n_needed_80:
        gap = max(0, n_needed_80 - n)
        print(f"  Events needed for 80% power: {n_needed_80} ({gap} more to add)")
    elif observed_mean == 0:
        print(f"  Events needed for 80% power: N/A (no observed effect)")
    else:
        print(f"  Events needed for 80% power: >500")

    return {
        'n': n,
        'mean_abs_car': observed_mean,
        'car_std': car_std,
        'mde': mde,
        'power': power,
        'n_needed_80': n_needed_80,
    }


# ── HYPOTHESIS TESTS ──────────────────────────────────────────────────────────

def test_whipsaw_asymmetry(results):
    """
    Test the core hypothesis: CAR(reversal) != -CAR(original)

    If reversals fully undo originals, the average net CAR should be ~0.
    Reports simple t-test, Boehmer (1991) test, and magnitude comparison.
    """
    print(f"\n{'='*70}")
    print("WHIPSAW ASYMMETRY TEST")
    print(f"{'='*70}")

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
    all_cars = pd.concat([originals['car'], reversals['car']])
    t_stat_net, p_value_net = stats.ttest_1samp(all_cars, 0)

    abs_originals = originals['car'].abs().mean()
    abs_reversals = reversals['car'].abs().mean()

    # Boehmer (1991) test — robust to event-induced variance
    bmp_orig = boehmer_test(originals['car'].values, originals['car_std'].values)
    bmp_rev = boehmer_test(reversals['car'].values, reversals['car_std'].values)
    bmp_all = boehmer_test(
        all_cars.values,
        pd.concat([originals['car_std'], reversals['car_std']]).values
    )

    print(f"\n  Original events (n={len(originals)}):")
    print(f"    Mean CAR: {mean_car_original*100:.3f}%")
    print(f"    Mean |CAR|: {abs_originals*100:.3f}%")
    print(f"\n  Reversal events (n={len(reversals)}):")
    print(f"    Mean CAR: {mean_car_reversal*100:.3f}%")
    print(f"    Mean |CAR|: {abs_reversals*100:.3f}%")
    print(f"\n  Net effect (original + reversal): {net_effect*100:.3f}%")
    print(f"  |Reversal| / |Original| ratio: {abs_reversals/abs_originals:.3f}")

    print(f"\n  --- Simple t-test ---")
    print(f"  H0: Net effect = 0 (reversals fully undo originals)")
    print(f"  t-statistic: {t_stat_net:.3f}")
    print(f"  p-value: {p_value_net:.4f}")

    print(f"\n  --- Boehmer (1991) test ---")
    print(f"  All whipsaw events: T_BMP = {bmp_all['t_stat']:.3f}, p = {bmp_all['p_value']:.4f}")
    print(f"  Originals only:    T_BMP = {bmp_orig['t_stat']:.3f}, p = {bmp_orig['p_value']:.4f}")
    print(f"  Reversals only:    T_BMP = {bmp_rev['t_stat']:.3f}, p = {bmp_rev['p_value']:.4f}")

    if p_value_net < 0.05:
        print(f"\n  -> REJECT H0 at 5%: Whipsaw uncertainty premium EXISTS")
    elif p_value_net < 0.10:
        print(f"\n  -> REJECT H0 at 10%: Weak evidence of whipsaw premium")
    else:
        print(f"\n  -> FAIL TO REJECT H0: No significant whipsaw premium")

    return {
        'n_originals': len(originals),
        'n_reversals': len(reversals),
        'mean_car_original': mean_car_original,
        'mean_car_reversal': mean_car_reversal,
        'net_effect': net_effect,
        'abs_ratio': abs_reversals / abs_originals,
        't_stat': t_stat_net,
        'p_value': p_value_net,
        't_bmp': bmp_all['t_stat'],
        'p_bmp': bmp_all['p_value'],
    }


def test_credibility_decay(results, data=None):
    """
    Test whether |CAR| decreases as cumulative whipsaw count increases.

    |CAR_t| = alpha + beta * cumulative_whipsaw_count_t + epsilon

    Negative beta = credibility decay (markets discount announcements)
    Positive beta = uncertainty amplification (markets overreact more)

    If *data* is provided and contains OVX, a second regression adds OVX
    as a control to separate volatility-regime effects from true credibility
    decay.
    """
    print(f"\n{'='*70}")
    print("CREDIBILITY DECAY REGRESSION")
    print(f"{'='*70}")

    narrow = results[results['window'] == DEFAULT_WINDOW].copy()
    narrow['abs_car'] = narrow['car'].abs()

    # Only use events that are part of whipsaw sequences
    whipsaw_events = narrow[narrow['cumulative_whipsaw_count'] > 0].copy()

    if len(whipsaw_events) < 5:
        print("  Insufficient whipsaw events for regression.")
        return None

    x = whipsaw_events['cumulative_whipsaw_count'].values.astype(float)
    y = whipsaw_events['abs_car'].values

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    print(f"\n  --- Baseline regression ---")
    print(f"  |CAR| = {intercept*100:.4f}% + {slope*100:.4f}% * cumulative_whipsaw_count")
    print(f"  N = {len(whipsaw_events)} events")
    print(f"  R^2 = {r_value**2:.4f}")
    print(f"  beta = {slope*100:.4f}% per additional whipsaw")
    print(f"  SE(beta) = {std_err*100:.4f}%")
    t_val = slope / std_err if std_err > 0 else 0
    print(f"  t-stat = {t_val:.3f}")
    print(f"  p-value = {p_value:.4f}")

    result = {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_value**2,
        'p_value': p_value,
        'std_err': std_err,
        'n': len(whipsaw_events),
    }

    # ── OVX control regression ──
    if data is not None and 'ovx' in data.columns:
        ovx_values = []
        for _, row in whipsaw_events.iterrows():
            edate = row['date']
            if edate in data.index and pd.notna(data.loc[edate, 'ovx']):
                ovx_values.append(data.loc[edate, 'ovx'])
            else:
                nearest_idx = data.index.get_indexer([edate], method='nearest')[0]
                if 0 <= nearest_idx < len(data):
                    ovx_val = data.iloc[nearest_idx]['ovx']
                    ovx_values.append(ovx_val if pd.notna(ovx_val) else np.nan)
                else:
                    ovx_values.append(np.nan)

        whipsaw_events = whipsaw_events.copy()
        whipsaw_events['ovx'] = ovx_values
        valid = whipsaw_events.dropna(subset=['ovx'])

        if len(valid) >= 5:
            X = np.column_stack([
                np.ones(len(valid)),
                valid['cumulative_whipsaw_count'].values.astype(float),
                valid['ovx'].values,
            ])
            y_ovx = valid['abs_car'].values

            coeffs, _, _, _ = np.linalg.lstsq(X, y_ovx, rcond=None)
            y_hat = X @ coeffs
            ss_res = ((y_ovx - y_hat) ** 2).sum()
            ss_tot = ((y_ovx - y_ovx.mean()) ** 2).sum()
            r2_ovx = 1 - ss_res / ss_tot if ss_tot > 0 else 0

            n_ovx = len(valid)
            k = 3
            mse = ss_res / (n_ovx - k) if n_ovx > k else np.inf

            try:
                cov = mse * np.linalg.inv(X.T @ X)
                se = np.sqrt(np.diag(cov))
                t_stats_ovx = coeffs / se
                p_vals = [2 * stats.t.sf(abs(t), df=n_ovx - k) for t in t_stats_ovx]
            except np.linalg.LinAlgError:
                se = np.full(k, np.nan)
                p_vals = [np.nan] * k

            print(f"\n  --- With OVX control ---")
            print(f"  |CAR| = {coeffs[0]*100:.4f}% "
                  f"+ {coeffs[1]*100:.4f}% * whipsaw_count "
                  f"+ {coeffs[2]*100:.6f}% * OVX")
            print(f"  N = {n_ovx}, R^2 = {r2_ovx:.4f}")
            print(f"  beta(whipsaw) = {coeffs[1]*100:.4f}% "
                  f"(SE={se[1]*100:.4f}%, p={p_vals[1]:.4f})")
            print(f"  beta(OVX)     = {coeffs[2]*100:.6f}% "
                  f"(SE={se[2]*100:.6f}%, p={p_vals[2]:.4f})")

            result['ovx_slope'] = coeffs[1]
            result['ovx_r_squared'] = r2_ovx
            result['ovx_p_value'] = p_vals[1]
            result['ovx_control_p'] = p_vals[2]

    if slope < 0 and p_value < 0.05:
        print(f"\n  -> CREDIBILITY DECAY: Markets increasingly discount announcements")
    elif slope > 0 and p_value < 0.05:
        print(f"\n  -> UNCERTAINTY AMPLIFICATION: Each whipsaw makes markets react MORE")
    else:
        print(f"\n  -> No significant relationship between whipsaw count and |CAR|")

    return result


def domain_credibility_decay(results):
    """
    Run credibility decay regression separately by policy domain.

    Tests whether credibility decays differently for sanctions vs. drilling
    vs. OPEC diplomacy, etc.
    """
    print(f"\n{'='*70}")
    print("DOMAIN-SPECIFIC CREDIBILITY DECAY")
    print(f"{'='*70}")

    narrow = results[results['window'] == DEFAULT_WINDOW].copy()
    narrow['abs_car'] = narrow['car'].abs()

    domain_results = {}
    for domain in sorted(narrow['domain'].unique()):
        subset = narrow[(narrow['domain'] == domain)
                        & (narrow['cumulative_whipsaw_count'] > 0)]
        if len(subset) < 3:
            continue

        x = subset['cumulative_whipsaw_count'].values.astype(float)
        y = subset['abs_car'].values

        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        sig = '***' if p_value < 0.01 else '**' if p_value < 0.05 else '*' if p_value < 0.10 else ''

        print(f"\n  {domain} (n={len(subset)}):")
        print(f"    beta = {slope*100:.4f}% per whipsaw, "
              f"p = {p_value:.4f} {sig}")
        print(f"    R^2 = {r_value**2:.4f}")

        domain_results[domain] = {
            'n': len(subset),
            'slope': slope,
            'r_squared': r_value**2,
            'p_value': p_value,
        }

    return domain_results


# ── ROBUSTNESS TESTS ──────────────────────────────────────────────────────────

def run_placebo_test(data, events, return_col='wti_ret',
                     n_iterations=PLACEBO_ITERATIONS, seed=42):
    """
    Placebo / randomization test: run the event study on random non-event dates.

    If the real event dates are meaningful, their average |CAR| should be
    larger than what random dates produce.  Returns the percentile rank
    of the actual mean |CAR| in the placebo distribution; a rank above 95
    means the real events are significantly different from noise.
    """
    print(f"\n{'='*70}")
    print(f"PLACEBO TEST ({n_iterations} iterations)")
    print(f"{'='*70}")

    rng = np.random.RandomState(seed)

    # Actual results for comparison
    w_start, w_end = EVENT_WINDOWS[DEFAULT_WINDOW]
    actual_cars = []
    actual_pvals = []
    for _, event in events.iterrows():
        result = calculate_car_mean_adjusted(
            data, return_col, event['date'],
            event_window=(w_start, w_end)
        )
        if result is not None:
            actual_cars.append(abs(result['car']))
            actual_pvals.append(result['p_value'])

    if not actual_cars:
        print("  No actual results to compare against.")
        return None

    actual_mean_abs_car = np.mean(actual_cars)
    actual_pct_sig = np.mean([p < 0.05 for p in actual_pvals])

    # Valid indices for random sampling (must have estimation window room)
    trading_days = get_trading_days(data)
    min_idx = ESTIMATION_WINDOW + ESTIMATION_GAP + 10
    max_idx = len(trading_days) - 10
    valid_indices = np.arange(min_idx, max_idx)
    n_events = len(events)

    placebo_abs_cars = np.empty(n_iterations)
    placebo_pct_sig = np.empty(n_iterations)

    for i in range(n_iterations):
        chosen = rng.choice(valid_indices, size=n_events, replace=False)
        cars_i = []
        pvals_i = []
        for j in chosen:
            result = calculate_car_mean_adjusted(
                data, return_col, trading_days[j],
                event_window=(w_start, w_end)
            )
            if result is not None:
                cars_i.append(abs(result['car']))
                pvals_i.append(result['p_value'])

        placebo_abs_cars[i] = np.mean(cars_i) if cars_i else 0
        placebo_pct_sig[i] = np.mean([p < 0.05 for p in pvals_i]) if pvals_i else 0

    percentile = (placebo_abs_cars < actual_mean_abs_car).mean() * 100

    print(f"\n  Actual mean |CAR|:  {actual_mean_abs_car*100:.3f}%")
    print(f"  Placebo mean |CAR|: {placebo_abs_cars.mean()*100:.3f}% "
          f"(std: {placebo_abs_cars.std()*100:.3f}%)")
    print(f"  Actual percentile rank: {percentile:.1f}%")
    print(f"  Actual pct significant (5%):  {actual_pct_sig:.1%}")
    print(f"  Placebo pct significant (5%): {placebo_pct_sig.mean():.1%}")

    if percentile > 95:
        print(f"  -> PASS: Actual events produce significantly larger CARs than random dates")
    elif percentile > 90:
        print(f"  -> MARGINAL: Actual events somewhat larger than random "
              f"(p~{1 - percentile / 100:.2f})")
    else:
        print(f"  -> FAIL: Cannot distinguish actual events from random dates")

    return {
        'actual_mean_abs_car': actual_mean_abs_car,
        'placebo_mean': float(placebo_abs_cars.mean()),
        'placebo_std': float(placebo_abs_cars.std()),
        'percentile': percentile,
        'p_value': 1 - percentile / 100,
        'n_iterations': n_iterations,
        'placebo_distribution': placebo_abs_cars,
    }


def analyze_by_communication(results):
    """
    Test whether the communication channel affects market-reaction magnitude.

    Theory: executive orders (formal, legally binding) might produce larger
    CARs than social-media posts (informal, easily reversed).
    """
    print(f"\n{'='*70}")
    print("COMMUNICATION CHANNEL ANALYSIS")
    print(f"{'='*70}")

    narrow = results[results['window'] == DEFAULT_WINDOW].copy()

    if 'communication' not in narrow.columns:
        print("  No communication field in results — skipping.")
        return None

    narrow['abs_car'] = narrow['car'].abs()

    channel_stats = {}
    print(f"\n  {'Channel':<22} {'N':>3} {'Mean |CAR|%':>12} "
          f"{'Median |CAR|%':>14} {'Pct Sig':>8}")
    print(f"  {'-'*22} {'-'*3} {'-'*12} {'-'*14} {'-'*8}")

    for channel in sorted(narrow['communication'].dropna().unique()):
        subset = narrow[narrow['communication'] == channel]
        if len(subset) == 0:
            continue

        mean_abs = subset['abs_car'].mean() * 100
        median_abs = subset['abs_car'].median() * 100
        pct_sig = subset['significant_05'].mean()

        print(f"  {channel:<22} {len(subset):>3} "
              f"{mean_abs:>12.3f} {median_abs:>14.3f} {pct_sig:>8.0%}")

        channel_stats[channel] = {
            'n': len(subset),
            'mean_abs_car_pct': mean_abs,
            'median_abs_car_pct': median_abs,
            'pct_significant': pct_sig,
        }

    # Kruskal-Wallis test (non-parametric ANOVA)
    groups = [g['abs_car'].values
              for _, g in narrow.groupby('communication') if len(g) >= 2]
    if len(groups) >= 2:
        h_stat, kw_p = stats.kruskal(*groups)
        print(f"\n  Kruskal-Wallis test: H = {h_stat:.3f}, p = {kw_p:.4f}")
        if kw_p < 0.05:
            print(f"  -> SIGNIFICANT: Communication channel affects reaction size")
        else:
            print(f"  -> NOT SIGNIFICANT: No evidence channel matters")

    return channel_stats


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
        print(f"  {'Date':<12} {'CAR%':>7} {'t-stat':>7} {'p':>6} "
              f"{'Sig':>5} {'Dir':>12} {'Whipsaw':>10}  Description")
        print(f"  {'-'*12} {'-'*7} {'-'*7} {'-'*6} "
              f"{'-'*5} {'-'*12} {'-'*10}  {'-'*40}")

        for _, r in w.sort_values('date').iterrows():
            sig = ('***' if r['significant_01'] else
                   '**' if r['significant_05'] else
                   '*' if r['significant_10'] else '')
            desc = r['description'][:45]
            print(f"  {r['date'].strftime('%Y-%m-%d')} "
                  f"{r['car_pct']:>7.3f} {r['t_stat']:>7.3f} "
                  f"{r['p_value']:>6.3f} {sig:>5} "
                  f"{r['direction']:>12} {r['whipsaw_flag']:>10}  {desc}")

        # Summary stats
        print(f"\n  Summary: Mean CAR = {w['car_pct'].mean():.3f}%, "
              f"Median = {w['car_pct'].median():.3f}%, "
              f"Significant at 5%: {w['significant_05'].sum()}/{len(w)}")


def save_results_tables(results, asymmetry, decay, sign_test=None,
                        power=None, placebo=None, domain_decay=None,
                        comm=None, ar1_results=None):
    """Save publication-ready CSV tables."""

    # Table 1: All CARs (narrow window)
    narrow = results[results['window'] == DEFAULT_WINDOW].copy()
    cols = ['date', 'description', 'direction', 'whipsaw_flag',
            'car_pct', 't_stat', 'p_value', 'significant_05']
    if 'verified' in narrow.columns:
        cols.append('verified')
    table1 = narrow[cols].copy()
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
        pd.DataFrame([asymmetry]).to_csv(
            TABLES_DIR / 'table4_whipsaw_asymmetry.csv', index=False)

    # Table 5: Credibility decay
    if decay:
        pd.DataFrame([decay]).to_csv(
            TABLES_DIR / 'table5_credibility_decay.csv', index=False)

    # Table 7: AR(1) robustness comparison
    if ar1_results is not None and len(ar1_results) > 0:
        ar1_narrow = ar1_results[ar1_results['window'] == DEFAULT_WINDOW].copy()
        comparison = narrow[['date', 'car_pct', 't_stat', 'p_value']].rename(
            columns={'car_pct': 'car_pct_mean_adj', 't_stat': 't_mean_adj',
                     'p_value': 'p_mean_adj'})
        ar1_cols = ar1_narrow[['date', 'car_pct', 't_stat', 'p_value']].rename(
            columns={'car_pct': 'car_pct_ar1', 't_stat': 't_ar1',
                     'p_value': 'p_ar1'})
        comparison['date'] = pd.to_datetime(comparison['date'])
        ar1_cols['date'] = pd.to_datetime(ar1_cols['date'])
        table7 = comparison.merge(ar1_cols, on='date', how='outer')
        table7['date'] = table7['date'].dt.strftime('%Y-%m-%d')
        table7.to_csv(TABLES_DIR / 'table7_ar1_robustness.csv', index=False)

    # Table 8: Placebo test
    if placebo:
        placebo_save = {k: v for k, v in placebo.items()
                        if k != 'placebo_distribution'}
        pd.DataFrame([placebo_save]).to_csv(
            TABLES_DIR / 'table8_placebo.csv', index=False)

    # Table 9: Communication channel
    if comm:
        pd.DataFrame(comm).T.to_csv(TABLES_DIR / 'table9_communication.csv')

    # Table 10: Expected sign test
    if sign_test:
        pd.DataFrame([sign_test]).to_csv(
            TABLES_DIR / 'table10_sign_test.csv', index=False)

    # Table 11: Power analysis
    if power:
        pd.DataFrame([power]).to_csv(
            TABLES_DIR / 'table11_power.csv', index=False)

    # Table 12: Domain-specific decay
    if domain_decay:
        pd.DataFrame(domain_decay).T.to_csv(
            TABLES_DIR / 'table12_domain_decay.csv')

    print(f"\n  Tables saved to {TABLES_DIR}/")


def create_figures(results, data, events, placebo=None):
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

        # ── Figure 1: WTI price with event markers ──
        fig, ax = plt.subplots(figsize=(12, 6))
        price_data = data['wti'].dropna().loc['2017-01-01':]
        ax.plot(price_data.index, price_data.values,
                color='#2c3e50', linewidth=0.8, alpha=0.9, label='WTI Price')

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
            if (e['date'] in price_data.index or
                    (e['date'] >= price_data.index.min() and
                     e['date'] <= price_data.index.max())):
                color = direction_colors.get(e['direction'], '#f39c12')
                marker = 'v' if e['is_whipsaw'] else '^'
                nearest_date = price_data.index[
                    price_data.index.get_indexer([e['date']], method='nearest')[0]]
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
        plt.savefig(FIGURES_DIR / 'fig1_wti_price_events.png',
                    dpi=150, bbox_inches='tight')
        plt.close()

        # ── Figure 2: CAR distribution by whipsaw status ──
        narrow = results[results['window'] == DEFAULT_WINDOW]
        fig, ax = plt.subplots(figsize=(8, 5))

        originals = narrow[narrow['whipsaw_flag'] == 'original']['car_pct']
        reversals = narrow[narrow['whipsaw_flag'].isin(
            ['reversal', 're_reversal'])]['car_pct']
        non_whipsaw = narrow[narrow['whipsaw_flag'] == 'none']['car_pct']

        positions = [1, 2, 3]
        bp = ax.boxplot([originals, reversals, non_whipsaw],
                        positions=positions, widths=0.6, patch_artist=True)
        colors = ['#3498db', '#e74c3c', '#95a5a6']
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        ax.set_xticklabels(['Original\nAnnouncements', 'Reversals',
                            'Non-Whipsaw'])
        ax.set_ylabel('CAR (%)')
        ax.set_title('Distribution of CARs by Whipsaw Status [-1,+1] Window')
        ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / 'fig2_car_by_whipsaw.png',
                    dpi=150, bbox_inches='tight')
        plt.close()

        # ── Figure 3: Credibility decay ──
        fig, ax = plt.subplots(figsize=(8, 5))
        whipsaw_events = narrow[narrow['cumulative_whipsaw_count'] > 0].copy()

        if len(whipsaw_events) > 3:
            x = whipsaw_events['cumulative_whipsaw_count']
            y = whipsaw_events['car'].abs() * 100

            ax.scatter(x, y, color='#2c3e50', s=60, zorder=5,
                       edgecolors='white', linewidths=0.5)

            slope, intercept, _, _, _ = stats.linregress(x, y)
            x_line = np.linspace(x.min(), x.max(), 100)
            ax.plot(x_line, intercept + slope * x_line, color='#e74c3c',
                    linewidth=2, linestyle='--',
                    label=f'slope = {slope:.3f}%/whipsaw')

            ax.set_xlabel('Cumulative Whipsaw Count')
            ax.set_ylabel('|CAR| (%)')
            ax.set_title('Policy Credibility Decay: '
                         '|CAR| vs. Accumulated Reversals')
            ax.legend()

        plt.tight_layout()
        plt.savefig(FIGURES_DIR / 'fig3_credibility_decay.png',
                    dpi=150, bbox_inches='tight')
        plt.close()

        # ── Figure 4: Placebo distribution ──
        if placebo and 'placebo_distribution' in placebo:
            fig, ax = plt.subplots(figsize=(8, 5))
            dist = placebo['placebo_distribution'] * 100
            ax.hist(dist, bins=50, color='#95a5a6', alpha=0.7,
                    edgecolor='white', label='Placebo distribution')
            ax.axvline(placebo['actual_mean_abs_car'] * 100,
                       color='#e74c3c', linewidth=2, linestyle='--',
                       label=f"Actual mean |CAR| "
                             f"({placebo['actual_mean_abs_car']*100:.3f}%)")
            ax.set_xlabel('Mean |CAR| (%)')
            ax.set_ylabel('Frequency')
            ax.set_title(f"Placebo Test: Actual vs. {placebo['n_iterations']} "
                         f"Random Date Sets")
            ax.legend()
            pctile = placebo['percentile']
            ax.text(0.98, 0.95,
                    f"Percentile: {pctile:.1f}%\np = {1-pctile/100:.3f}",
                    transform=ax.transAxes, ha='right', va='top',
                    fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat',
                                           alpha=0.5))
            plt.tight_layout()
            plt.savefig(FIGURES_DIR / 'fig4_placebo_distribution.png',
                        dpi=150, bbox_inches='tight')
            plt.close()

        print(f"\n  Figures saved to {FIGURES_DIR}/")

    except Exception as e:
        print(f"\n  Warning: Could not generate figures: {e}")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("OIL POLICY WHIPSAW EVENT STUDY")
    print("Presidential Policy Credibility and Oil Market Volatility")
    print("=" * 70)

    # ── Load and verify data ──
    data = load_all_data()
    verify_data_files()
    stocks, sp500 = load_equity_data()

    # ── Load event catalog ──
    events = get_event_catalog()

    print(f"\n  Event catalog: {len(events)} events")
    print(f"    Originals:   {(events['whipsaw_flag'] == 'original').sum()}")
    print(f"    Reversals:   {events['is_whipsaw'].sum()}")
    print(f"    Non-whipsaw: {(events['whipsaw_flag'] == 'none').sum()}")
    if 'verified' in events.columns:
        print(f"    Verified:    {events['verified'].sum()}/{len(events)}")

    print(f"\n  Configuration:")
    print(f"    Estimation window: {ESTIMATION_WINDOW} trading days")
    print(f"    Estimation gap:    {ESTIMATION_GAP} trading days")
    print(f"    Default window:    {EVENT_WINDOWS[DEFAULT_WINDOW]}")

    # ── Check event coverage ──
    check_event_coverage(data, events)

    # ═══════════════════════════════════════════════════════════════════════
    # STUDY 1: WTI CRUDE OIL EVENT STUDY (Mean-Adjusted)
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print("STUDY 1: WTI CRUDE OIL EVENT STUDY")
    print(f"{'='*70}")

    wti_results = run_event_study(data, events, return_col='wti_ret')
    print_car_summary(wti_results, 'WTI')

    # ── Brent robustness ──
    print(f"\n{'='*70}")
    print("ROBUSTNESS: BRENT CRUDE OIL")
    print(f"{'='*70}")

    brent_results = run_event_study(data, events, return_col='brent_ret')
    print_car_summary(brent_results, 'Brent')

    # ── AR(1) model robustness ──
    print(f"\n{'='*70}")
    print("ROBUSTNESS: AR(1) MODEL")
    print(f"{'='*70}")

    ar1_results = run_event_study(data, events, return_col='wti_ret',
                                  model='ar1')
    print_car_summary(ar1_results, 'WTI (AR(1) model)')

    # ═══════════════════════════════════════════════════════════════════════
    # STUDY 2: WHIPSAW ASYMMETRY TEST
    # ═══════════════════════════════════════════════════════════════════════
    asymmetry = test_whipsaw_asymmetry(wti_results)

    # ═══════════════════════════════════════════════════════════════════════
    # STUDY 3: CREDIBILITY DECAY
    # ═══════════════════════════════════════════════════════════════════════
    decay = test_credibility_decay(wti_results, data=data)
    domain_decay = domain_credibility_decay(wti_results)

    # ═══════════════════════════════════════════════════════════════════════
    # STATISTICAL TESTS
    # ═══════════════════════════════════════════════════════════════════════
    sign_test = expected_sign_test(wti_results)
    power = power_analysis(wti_results)
    comm = analyze_by_communication(wti_results)

    # ═══════════════════════════════════════════════════════════════════════
    # PLACEBO TEST (may take a minute)
    # ═══════════════════════════════════════════════════════════════════════
    placebo = run_placebo_test(data, events)

    # ═══════════════════════════════════════════════════════════════════════
    # STUDY 4: EQUITY CROSS-SECTIONAL ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════
    equity_results = None
    kp_results = None
    if stocks is not None and sp500 is not None:
        print(f"\n{'='*70}")
        print("STUDY 4: EQUITY CROSS-SECTIONAL ANALYSIS")
        print(f"{'='*70}")

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
                    whip = subset[subset['is_whipsaw']]['car_pct']
                    non_whip = subset[~subset['is_whipsaw']]['car_pct']
                    print(f"\n  {ftype} ({', '.join(tickers)}):")
                    print(f"    Mean CAR: {subset['car_pct'].mean():.3f}%")
                    if len(whip) > 0:
                        print(f"    Whipsaw events: {whip.mean():.3f}%")
                    if len(non_whip) > 0:
                        print(f"    Non-whipsaw:    {non_whip.mean():.3f}%")

            equity_results.to_csv(
                TABLES_DIR / 'table6_equity_cars.csv', index=False)

            # Kolari & Pynnonen (2010) test
            print(f"\n  --- Kolari & Pynnonen (2010) Cross-Sectional Test ---")
            kp_results = kolari_pynnonen_test(equity_results, events)
            if kp_results is not None and len(kp_results) > 0:
                r_bar = kp_results.attrs.get('r_bar', 'N/A')
                print(f"  Average pairwise SAR correlation (r_bar): {r_bar:.4f}")
                n_sig_bmp = (kp_results['p_bmp'] < 0.05).sum()
                n_sig_kp = (kp_results['p_kp'] < 0.05).sum()
                print(f"  Events significant at 5% (Boehmer): {n_sig_bmp}/{len(kp_results)}")
                print(f"  Events significant at 5% (K&P adj): {n_sig_kp}/{len(kp_results)}")
                kp_results.to_csv(
                    TABLES_DIR / 'table13_kp_equity.csv', index=False)

    # ═══════════════════════════════════════════════════════════════════════
    # SAVE ALL OUTPUTS
    # ═══════════════════════════════════════════════════════════════════════
    save_results_tables(wti_results, asymmetry, decay,
                        sign_test=sign_test, power=power,
                        placebo=placebo, domain_decay=domain_decay,
                        comm=comm, ar1_results=ar1_results)
    create_figures(wti_results, data, events, placebo=placebo)

    # Save full results for further analysis
    wti_results.to_csv(TABLES_DIR / 'full_wti_results.csv', index=False)
    brent_results.to_csv(TABLES_DIR / 'full_brent_results.csv', index=False)
    ar1_results.to_csv(TABLES_DIR / 'full_wti_ar1_results.csv', index=False)

    print(f"\n{'='*70}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*70}")
    print(f"\n  Results saved to: {TABLES_DIR}/")
    print(f"  Figures saved to: {FIGURES_DIR}/")
    print(f"\n  Next steps:")
    print(f"    1. Review table1_car_results.csv for individual event CARs")
    print(f"    2. Check table4_whipsaw_asymmetry.csv (core hypothesis)")
    print(f"    3. Check table5_credibility_decay.csv (decay regression)")
    print(f"    4. Review table8_placebo.csv (are events real or noise?)")
    print(f"    5. Check table11_power.csv (do you need more events?)")
    print(f"    6. Verify event catalog dates against primary sources")


if __name__ == "__main__":
    main()
