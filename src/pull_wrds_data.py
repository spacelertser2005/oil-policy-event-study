"""
Pull oil company equity data and S&P 500 index from WRDS/CRSP.

Usage:
    python src/pull_wrds_data.py

Requires WRDS account credentials (will prompt on first run).
Install: pip install wrds
"""

import wrds
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "raw"

# Oil company tickers: majors, E&P, refiners, oilfield services
OIL_TICKERS = ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'VLO', 'MPC', 'HAL', 'OXY', 'DVN']

START_DATE = '2016-01-01'
END_DATE = '2026-04-18'


def pull_stock_data(conn):
    """Pull daily stock data for oil companies from CRSP."""
    print(f"Pulling daily stock data for: {', '.join(OIL_TICKERS)}")
    
    tickers_str = "', '".join(OIL_TICKERS)
    
    # Try CIZ (v2) format first, fall back to legacy SIZ
    try:
        data = conn.raw_sql(f"""
            SELECT permno, dlycaldt AS date, ticker, dlyprc AS prc, dlyret AS ret, dlyretx AS retx
            FROM crsp.dsf_v2
            WHERE ticker IN ('{tickers_str}')
            AND dlycaldt BETWEEN '{START_DATE}' AND '{END_DATE}'
            ORDER BY ticker, dlycaldt
        """, date_cols=['date'])
        print(f"  Retrieved {len(data)} rows from crsp.dsf_v2 (CIZ format)")
    except Exception as e:
        print(f"  CIZ format failed ({e}), trying legacy SIZ...")
        data = conn.raw_sql(f"""
            SELECT a.permno, b.date, b.ticker, b.prc, b.ret, b.retx
            FROM crsp.dsenames AS a
            JOIN crsp.dsf AS b ON a.permno = b.permno
            WHERE a.ticker IN ('{tickers_str}')
            AND b.date BETWEEN '{START_DATE}' AND '{END_DATE}'
            AND a.namedt <= b.date AND b.date <= a.nameendt
            ORDER BY b.ticker, b.date
        """, date_cols=['date'])
        print(f"  Retrieved {len(data)} rows from crsp.dsf (legacy SIZ format)")
    
    return data


def pull_sp500_index(conn):
    """Pull S&P 500 daily index level and returns.

    Tries crsp.dsp500_v2 first, then crsp.dsi.  If the S&P 500 data
    has a gap (e.g. dsi only through Dec 2024), supplements with SPY
    ETF returns from crsp.dsf_v2 (available through Dec 2025).
    """
    print("Pulling S&P 500 index data...")

    sp500 = None
    try:
        sp500 = conn.raw_sql(f"""
            SELECT caldt AS date, spindx, sprtrn
            FROM crsp.dsp500_v2
            WHERE caldt BETWEEN '{START_DATE}' AND '{END_DATE}'
            ORDER BY caldt
        """, date_cols=['date'])
        print(f"  Retrieved {len(sp500)} rows from crsp.dsp500_v2")
    except Exception as e:
        print(f"  V2 failed ({e}), trying legacy crsp.dsi...")
        try:
            sp500 = conn.raw_sql(f"""
                SELECT date, spindx, sprtrn
                FROM crsp.dsi
                WHERE date BETWEEN '{START_DATE}' AND '{END_DATE}'
                ORDER BY date
            """, date_cols=['date'])
            print(f"  Retrieved {len(sp500)} rows from crsp.dsi")
        except Exception as e2:
            print(f"  dsi also failed ({e2})")

    # Supplement with SPY ETF returns for dates beyond S&P 500 coverage
    try:
        spy = conn.raw_sql(f"""
            SELECT dlycaldt AS date, dlyret AS sprtrn
            FROM crsp.dsf_v2
            WHERE ticker = 'SPY'
            AND dlycaldt BETWEEN '{START_DATE}' AND '{END_DATE}'
            ORDER BY dlycaldt
        """, date_cols=['date'])
        print(f"  Retrieved {len(spy)} rows of SPY (market proxy) from crsp.dsf_v2")

        if sp500 is not None and len(sp500) > 0:
            sp500_dates = set(sp500['date'])
            spy_fill = spy[~spy['date'].isin(sp500_dates)].copy()
            if len(spy_fill) > 0:
                print(f"  Supplementing {len(spy_fill)} gap dates with SPY returns")
                sp500 = pd.concat([sp500, spy_fill], ignore_index=True)
                sp500 = sp500.sort_values('date').reset_index(drop=True)
        elif sp500 is None or len(sp500) == 0:
            print("  Using SPY as sole market proxy (S&P 500 tables unavailable)")
            sp500 = spy
    except Exception as e3:
        print(f"  SPY supplement failed ({e3}) — equity analysis limited to S&P 500 date range")

    if sp500 is not None:
        print(f"  Final market data: {sp500['date'].min().date()} to {sp500['date'].max().date()}")

    return sp500


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Connecting to WRDS...")
    conn = wrds.Connection()
    
    # Pull stock data
    stocks = pull_stock_data(conn)
    stocks_path = DATA_DIR / "crsp_oil_stocks.csv"
    stocks.to_csv(stocks_path, index=False)
    print(f"  Saved to {stocks_path}")
    
    # Pull S&P 500
    sp500 = pull_sp500_index(conn)
    sp500_path = DATA_DIR / "sp500_index.csv"
    sp500.to_csv(sp500_path, index=False)
    print(f"  Saved to {sp500_path}")
    
    conn.close()
    print("\nDone. Files saved to data/raw/")


if __name__ == "__main__":
    main()