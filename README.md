# Presidential Oil Policy Reversals and Market Credibility

**An Event Study of the Whipsaw Effect**

ECON 401 Independent Study -- University of Oregon
Matthew Lertsmitivanta | Advisor: Prof. Bruce Blonigen

## Research Question

When a president announces a major oil policy and then reverses it shortly after, does the reversal just cancel out the original market reaction? Or does the back-and-forth itself spook markets, making each new announcement matter less because investors stop trusting that the policy will stick?

This project uses an **event study** -- a standard method for measuring how markets react to specific announcements -- to test whether presidential oil-policy flip-flops ("whipsaw" events) create a compounding uncertainty premium that goes beyond simply undoing the prior shock. The sample covers Trump-era oil policy events from 2017 through 2025.

## Prerequisites

- **Python 3.10+**
- **WRDS account** (optional) -- needed only for the equity (stock) analysis. Oil price results work without it. University of Oregon students can access WRDS through the library.

## Setup

```bash
# Clone the repo
git clone https://github.com/spacelertser2005/oil-policy-event-study.git
cd oil-policy-event-study

# Create and activate a virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Data

Before running the analysis, you need data files in `data/raw/`. **These files are not checked into the repo** (they are gitignored) and must be downloaded separately.

### Oil prices and volatility (free, no login)

Download these CSV files from [FRED](https://fred.stlouisfed.org/) and place them in `data/raw/`:

| File | FRED Series | What It Is |
|------|-------------|------------|
| `DCOILWTICO.csv` | DCOILWTICO | WTI crude oil daily spot price |
| `DCOILBRENTEU.csv` | DCOILBRENTEU | Brent crude oil daily spot price |
| `OVXCLS.csv` | OVXCLS | CBOE Oil Volatility Index |
| `VIXCLS.csv` | VIXCLS | CBOE Volatility Index (VIX) |

### Stock data (requires WRDS account)

```bash
python src/pull_wrds_data.py
```

This pulls daily returns for 10 oil companies (XOM, CVX, COP, EOG, OXY, DVN, VLO, MPC, SLB, HAL) and the S&P 500 index from CRSP via WRDS. You will be prompted for your WRDS credentials.

## Running the Analysis

```bash
python src/event_study.py
```

This runs the full pipeline:

1. Loads the event catalog from `src/event_catalog.py` (26 hand-coded policy events with whipsaw classifications)
2. Calculates abnormal returns around each event using a 200-day estimation window
3. Tests whether whipsaw reversals are asymmetric (do they more than undo the original shock?)
4. Runs a credibility decay regression (do markets react less as flip-flops accumulate?)
5. Performs equity cross-section analysis across oil company types (producers, refiners, oilfield services)
6. Writes all results to `output/`

## Output

Results are saved to two directories (also gitignored, since they can be regenerated):

**Tables** (`output/tables/`):
- `table1_car_results.csv` -- Cumulative abnormal returns for each event
- `table2_car_by_type.csv` -- Results grouped by policy domain
- `table3_robustness_windows.csv` -- Results across different event windows
- `table4_whipsaw_asymmetry.csv` -- Test of the core whipsaw hypothesis
- `table5_credibility_decay.csv` -- Credibility decay regression
- `table6_equity_cars.csv` -- Stock-level results for 10 oil companies

**Figures** (`output/figures/`):
- `fig1_wti_price_events.png` -- WTI price series with event markers
- `fig2_car_by_whipsaw.png` -- Abnormal returns split by whipsaw vs. non-whipsaw
- `fig3_credibility_decay.png` -- Market reaction size over successive reversals

## Project Structure

```
oil-policy-event-study/
├── data/
│   ├── raw/               # Downloaded data files (gitignored)
│   └── processed/         # Cleaned/merged data (gitignored)
├── src/
│   ├── event_catalog.py   # Master event list with whipsaw coding
│   ├── event_study.py     # Full analysis pipeline
│   └── pull_wrds_data.py  # WRDS/CRSP data download script
├── output/
│   ├── tables/            # CSV result tables (gitignored)
│   └── figures/           # PNG charts (gitignored)
├── docs/                  # Paper drafts, literature notes
├── notebooks/             # Jupyter notebooks for exploration
├── requirements.txt
└── README.md
```

## Methodology

The analysis follows the standard event study framework from MacKinlay (1997):

- **Estimation window**: 200 trading days before each event
- **Event windows**: [-1, +1] days (primary), with [-2, +2] and [-5, +5] for robustness
- **Oil prices**: Mean-adjusted model (actual return minus average return from the estimation window)
- **Equities**: Market model (actual return minus beta-predicted return based on S&P 500)

The novel part is the **whipsaw variable**: each event is coded as an "original" policy action, a "reversal," or a "re-reversal." The key test is whether the market reaction to a reversal is simply the mirror image of the original, or something different.

## Key References

- MacKinlay, A.C. (1997). "Event Studies in Economics and Finance." *Journal of Economic Literature*, 35(1), 13-39.
- Boehmer, E., Masumeci, J., & Poulsen, A.B. (1991). "Event-Study Methodology Under Conditions of Event-Induced Variance." *Journal of Financial Economics*, 30(2), 253-272.
- Kolari, J.W. & Pynnonen, S. (2010). "Event Study Testing with Cross-Sectional Correlation of Abnormal Returns." *Review of Financial Studies*, 23(11), 3996-4025.
- Hamilton, J.D. (2009). "Understanding Crude Oil Prices." *Energy Journal*, 30(2), 179-206.
