# Presidential Policy Credibility and Oil Market Volatility

**An Event Study of the Whipsaw Effect**

ECON 401 Independent Study — University of Oregon  
Student: Matthew Lertsmitivanta  
Faculty Advisor: Prof. Bruce Blonigen

## Research Question

Do presidential oil-policy reversals ("whipsaw" events) simply undo the original price shock, or do they generate a compounding uncertainty premium that erodes policy credibility over time?

## Project Structure

```
oil-policy-event-study/
├── data/
│   ├── raw/              # Original downloaded data (not tracked in git)
│   │   ├── DCOILWTICO.csv       # WTI daily spot (FRED)
│   │   ├── DCOILBRENTEU.csv     # Brent daily spot (FRED)
│   │   ├── OVXCLS.csv           # Oil volatility index (FRED)
│   │   ├── VIXCLS.csv           # VIX (FRED)
│   │   ├── SP500.csv            # S&P 500 index (FRED)
│   │   ├── crsp_oil_stocks.csv  # Oil company daily returns (WRDS/CRSP)
│   │   └── sp500_index.csv      # S&P 500 returns (WRDS/CRSP)
│   └── processed/        # Cleaned and merged data (not tracked)
├── src/
│   ├── pull_wrds_data.py  # WRDS/CRSP data download script
│   ├── event_study.py     # Core event study analysis
│   └── utils.py           # Helper functions
├── output/
│   ├── tables/            # Results tables (LaTeX/CSV)
│   └── figures/           # Charts and plots
├── docs/                  # Paper drafts, literature notes
├── notebooks/             # Jupyter notebooks for exploration
├── requirements.txt
└── README.md
```

## Data Sources

| Data | Source | File |
|------|--------|------|
| WTI spot price | FRED (DCOILWTICO) | `data/raw/DCOILWTICO.csv` |
| Brent spot price | FRED (DCOILBRENTEU) | `data/raw/DCOILBRENTEU.csv` |
| Oil Volatility Index | FRED (OVXCLS) | `data/raw/OVXCLS.csv` |
| VIX | FRED (VIXCLS) | `data/raw/VIXCLS.csv` |
| S&P 500 | FRED (SP500) | `data/raw/SP500.csv` |
| Oil company equities | WRDS/CRSP | `data/raw/crsp_oil_stocks.csv` |

## Setup

```bash
cd C:\Users\mattl\Projects\oil-policy-event-study
pip install -r requirements.txt

# Pull equity data from WRDS (requires WRDS account)
python src/pull_wrds_data.py
```

## Methodology

- **Event study**: MacKinlay (1997) framework
- **Estimation window**: 200 trading days
- **Event windows**: [-1,+1], [-2,+2], [-5,+5]
- **Statistical tests**: Boehmer et al. (1991), Kolari & Pynnönen (2010)
- **Novel variable**: Credibility decay — cumulative whipsaw count regressed on |CAR|

## Key References

- MacKinlay, A.C. (1997). "Event Studies in Economics and Finance." *JEL*, 35(1).
- Boehmer, E., Masumeci, J., & Poulsen, A.B. (1991). *JFE*, 30(2).
- Kolari, J.W. & Pynnönen, S. (2010). *RFS*, 23(11).
- Hamilton, J.D. (2009). "Understanding Crude Oil Prices." *Energy Journal*, 30(2).
