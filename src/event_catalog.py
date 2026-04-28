"""
Event catalog for the oil policy whipsaw study.

Each event is coded with:
- date: event date (YYYY-MM-DD)
- description: brief description
- phase: which phase of Trump presidency
- domain: policy domain (iran_military, drilling_permitting, sanctions, spr, opec_diplomacy)
- direction: pro_supply, anti_supply, or ambiguous
- expected_sign: expected effect on oil prices (+1 = price increase, -1 = price decrease)
- whipsaw_flag: original, reversal, re_reversal, or none
- whipsaw_seq: sequence number within a whipsaw chain
    0 = none, 1 = original, 2 = first reversal, 3 = re_reversal, 4+ = subsequent reversals
- communication: executive_order, truth_social, press_briefing, military_action, official_statement
- source: primary source for the event
"""

import pandas as pd
from pathlib import Path
import warnings

EVENTS = [
    # ── TRUMP 1.0: 2017-2021 ──────────────────────────────────────────────
    {
        "date": "2017-01-24",
        "description": "Executive orders to advance Keystone XL and Dakota Access pipelines",
        "phase": "trump1_early",
        "domain": "drilling_permitting",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "original",
        "whipsaw_seq": 1,
        "communication": "executive_order",
        "source": "Federal Register"
    },
    {
        "date": "2017-03-28",
        "description": "Executive order to review and roll back Clean Power Plan and climate regulations",
        "phase": "trump1_early",
        "domain": "drilling_permitting",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "executive_order",
        "source": "Federal Register"
    },
    {
        "date": "2017-04-28",
        "description": "Executive order to expand offshore drilling, review Obama-era offshore bans",
        "phase": "trump1_early",
        "domain": "drilling_permitting",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "executive_order",
        "source": "Federal Register"
    },
    {
        "date": "2017-10-13",
        "description": "Trump decertifies Iran nuclear deal but does not withdraw",
        "phase": "trump1_iran",
        "domain": "iran_military",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "original",
        "whipsaw_seq": 1,
        "communication": "official_statement",
        "source": "Reuters"
    },
    {
        "date": "2018-01-12",
        "description": "Trump waives Iran sanctions again, signals last time",
        "phase": "trump1_iran",
        "domain": "sanctions",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "reversal",
        "whipsaw_seq": 2,
        "communication": "official_statement",
        "source": "Reuters"
    },
    {
        "date": "2018-05-08",
        "description": "Trump withdraws from JCPOA, reinstates Iran sanctions",
        "phase": "trump1_iran",
        "domain": "sanctions",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "re_reversal",
        "whipsaw_seq": 3,
        "communication": "official_statement",
        "source": "Reuters"
    },
    {
        "date": "2018-11-05",
        "description": "Iran oil sanctions take effect but 8 countries granted waivers",
        "phase": "trump1_iran",
        "domain": "sanctions",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "reversal",
        "whipsaw_seq": 4,
        "communication": "official_statement",
        "source": "Reuters"
    },
    {
        "date": "2019-04-22",
        "description": "Trump ends Iran oil sanction waivers, demands zero exports",
        "phase": "trump1_iran",
        "domain": "sanctions",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "re_reversal",
        "whipsaw_seq": 5,
        "communication": "official_statement",
        "source": "Reuters"
    },
    {
        "date": "2019-06-20",
        "description": "Iran shoots down US drone; Trump orders then cancels retaliatory strike",
        "phase": "trump1_iran",
        "domain": "iran_military",
        "direction": "ambiguous",
        "expected_sign": 1,
        "whipsaw_flag": "original",
        "whipsaw_seq": 1,
        "communication": "twitter",
        "source": "Reuters"
    },
    {
        "date": "2020-01-03",
        "description": "US kills Qasem Soleimani in Baghdad airstrike",
        "phase": "trump1_iran",
        "domain": "iran_military",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "original",
        "whipsaw_seq": 1,
        "communication": "military_action",
        "source": "Reuters"
    },
    {
        "date": "2020-01-08",
        "description": "Iran retaliates with missile strikes on US bases; Trump signals de-escalation",
        "phase": "trump1_iran",
        "domain": "iran_military",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "reversal",
        "whipsaw_seq": 2,
        "communication": "press_briefing",
        "source": "Reuters"
    },
    {
        "date": "2020-03-09",
        "description": "Saudi-Russia price war erupts; oil crashes 25%",
        "phase": "trump1_covid",
        "domain": "opec_diplomacy",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "original",
        "whipsaw_seq": 1,
        "communication": "official_statement",
        "source": "Reuters"
    },
    {
        "date": "2020-04-02",
        "description": "Trump brokers Saudi-Russia OPEC+ deal to cut production",
        "phase": "trump1_covid",
        "domain": "opec_diplomacy",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "reversal",
        "whipsaw_seq": 2,
        "communication": "twitter",
        "source": "Reuters"
    },

    # ── TRUMP 2.0: 2025-Present ──────────────────────────────────────────
    # All Trump 2.0 dates verified against primary sources (see docs/event_verification.csv).
    {
        "date": "2025-01-20",
        "description": "Inauguration Day: Drill Baby Drill executive orders, Paris Agreement withdrawal, and EO 14156 declaring a national energy emergency (all signed same day)",
        "phase": "trump2_early",
        "domain": "drilling_permitting",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "original",
        "whipsaw_seq": 1,
        "communication": "executive_order",
        "source": "https://www.whitehouse.gov/presidential-actions/2025/01/declaring-a-national-energy-emergency/"
    },
    {
        "date": "2025-01-23",
        "description": "Trump tells Davos he will demand Saudi Arabia and OPEC bring oil prices down",
        "phase": "trump2_opec",
        "domain": "opec_diplomacy",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "original",
        "whipsaw_seq": 1,
        "communication": "press_briefing",
        "source": "https://www.cnbc.com/2025/01/23/oil-turns-lower-after-trump-says-hell-ask-saudi-arabia-and-opec-to-bring-the-price-down.html"
    },
    {
        "date": "2025-02-03",
        "description": "OPEC+ JMMC meeting maintains existing production cuts despite Trump pressure",
        "phase": "trump2_opec",
        "domain": "opec_diplomacy",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "reversal",
        "whipsaw_seq": 2,
        "communication": "official_statement",
        "source": "https://www.bloomberg.com/news/articles/2025-02-03/opec-sticks-to-supply-plan-even-as-trump-seeks-oil-price-cut"
    },
    {
        "date": "2025-02-04",
        "description": "NSPM-2 reimposes maximum pressure sanctions on Iran with stated goal of driving Iranian oil exports to zero",
        "phase": "trump2_iran",
        "domain": "sanctions",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "original",
        "whipsaw_seq": 1,
        "communication": "executive_order",
        "source": "https://www.whitehouse.gov/fact-sheets/2025/02/fact-sheet-president-donald-j-trump-restores-maximum-pressure-on-iran/"
    },
    {
        "date": "2025-03-07",
        "description": "Trump sends letter to Ayatollah Khamenei seeking nuclear negotiations, signals willingness to deal",
        "phase": "trump2_iran",
        "domain": "iran_military",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "reversal",
        "whipsaw_seq": 2,
        "communication": "official_statement",
        "source": "https://www.washingtonpost.com/politics/2025/03/07/trump-iran-nuclear-day/"
    },
    {
        "date": "2025-03-24",
        "description": "EO 14245 imposes 25% secondary tariffs on countries importing Venezuelan oil",
        "phase": "trump2_opec",
        "domain": "sanctions",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "executive_order",
        "source": "https://www.whitehouse.gov/presidential-actions/2025/03/imposing-tariffs-on-countries-importing-venezuelan-oil/"
    },
    {
        "date": "2025-04-03",
        "description": "OPEC+ unexpectedly accelerates output restoration, adding 411k bpd in May (three monthly increments at once)",
        "phase": "trump2_opec",
        "domain": "opec_diplomacy",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "re_reversal",
        "whipsaw_seq": 3,
        "communication": "official_statement",
        "source": "https://www.opec.org/pr-detail/557-03-april-2025.html"
    },
    {
        "date": "2025-06-13",
        "description": "Israel launches surprise strikes on Iran beginning the Twelve-Day War",
        "phase": "trump2_iran_war",
        "domain": "iran_military",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "re_reversal",
        "whipsaw_seq": 3,
        "communication": "military_action",
        "source": "https://en.wikipedia.org/wiki/Twelve-Day_War"
    },
    {
        "date": "2025-06-22",
        "description": "US Operation Midnight Hammer strikes Iranian nuclear facilities at Fordow, Natanz, and Isfahan",
        "phase": "trump2_iran_war",
        "domain": "iran_military",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "military_action",
        "source": "https://en.wikipedia.org/wiki/United_States_strikes_on_Iranian_nuclear_sites"
    },
    {
        "date": "2025-06-24",
        "description": "Twelve-Day War ceasefire announced by Trump, brokered with Qatar; war ends",
        "phase": "trump2_iran_war",
        "domain": "iran_military",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "reversal",
        "whipsaw_seq": 4,
        "communication": "press_briefing",
        "source": "https://en.wikipedia.org/wiki/Twelve-Day_War_ceasefire"
    },
]


def get_event_catalog(verified_only=False, verification_path=None):
    """Return the event catalog as a DataFrame.

    Args:
        verified_only: If True, only return events that have been verified
            against primary sources (Reuters, WSJ, Federal Register).
        verification_path: Path to event_verification.csv.  Defaults to
            docs/event_verification.csv in the project root.
    """
    # Suppress pandas 2.x Copy-on-Write FutureWarnings (false positives
    # on column assignment to a DataFrame we own via .copy()).
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', FutureWarning)

        df = pd.DataFrame(EVENTS).copy()
        df['date'] = pd.to_datetime(df['date'])
        df['is_whipsaw'] = df['whipsaw_flag'].isin(['reversal', 're_reversal'])

        # ── Load verification status ──
        if verification_path is None:
            verification_path = (Path(__file__).parent.parent
                                 / 'docs' / 'event_verification.csv')

        df['verified'] = False
        if verification_path.exists():
            verif = pd.read_csv(verification_path).copy()
            verif['actual_event_date'] = pd.to_datetime(
                verif['actual_event_date'], errors='coerce')
            verified_dates = set()
            for _, row in verif.iterrows():
                if row['status'] in ('VERIFIED', 'FIX_DATE',
                                     'FIX_DATE_AND_DESCRIPTION'):
                    date = (row['actual_event_date']
                            if pd.notna(row['actual_event_date'])
                            else pd.to_datetime(row['original_date']))
                    verified_dates.add(date)
            df['verified'] = df['date'].isin(verified_dates)

        if verified_only:
            n_before = len(df)
            df = df[df['verified']].copy().reset_index(drop=True)
            n_dropped = n_before - len(df)
            if n_dropped > 0:
                print(f"  Dropped {n_dropped} unverified events "
                      f"(verified_only=True)")

        # Calculate cumulative whipsaw count (for credibility decay variable)
        df = df.sort_values('date').reset_index(drop=True)
        df['cumulative_whipsaw_count'] = df['is_whipsaw'].cumsum()

        # Days since prior reversal
        reversal_dates = df.loc[df['is_whipsaw'], 'date']
        df['days_since_prior_reversal'] = None
        for idx, row in df.iterrows():
            prior = reversal_dates[reversal_dates < row['date']]
            if len(prior) > 0:
                df.at[idx, 'days_since_prior_reversal'] = (
                    row['date'] - prior.iloc[-1]).days

    return df


if __name__ == "__main__":
    catalog = get_event_catalog()
    print(f"Total events: {len(catalog)}")
    print(f"Whipsaw events: {catalog['is_whipsaw'].sum()}")
    print(f"Original events: {(catalog['whipsaw_flag'] == 'original').sum()}")
    if 'verified' in catalog.columns:
        print(f"Verified events: {catalog['verified'].sum()}/{len(catalog)}")
    print(f"\nPhase breakdown:")
    print(catalog['phase'].value_counts().to_string())
    print(f"\nDomain breakdown:")
    print(catalog['domain'].value_counts().to_string())
    print(f"\nEvents:")
    for _, e in catalog.iterrows():
        flag = f" [{e['whipsaw_flag'].upper()}]" if e['whipsaw_flag'] != 'none' else ''
        v = ' [VERIFIED]' if e.get('verified', False) else ''
        print(f"  {e['date'].strftime('%Y-%m-%d')} | {e['direction']:12s} | {e['description'][:60]}{flag}{v}")
