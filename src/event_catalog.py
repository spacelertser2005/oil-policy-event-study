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
        "communication": "truth_social",
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
        "communication": "truth_social",
        "source": "Reuters"
    },

    # ── TRUMP 2.0: 2025-Present ──────────────────────────────────────────
    {
        "date": "2025-01-20",
        "description": "Inauguration Day: 'Drill Baby Drill' executive orders, withdraws from Paris Agreement",
        "phase": "trump2_early",
        "domain": "drilling_permitting",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "original",
        "whipsaw_seq": 1,
        "communication": "executive_order",
        "source": "Federal Register"
    },
    {
        "date": "2025-01-23",
        "description": "National energy emergency declaration to fast-track permitting",
        "phase": "trump2_early",
        "domain": "drilling_permitting",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "executive_order",
        "source": "Federal Register"
    },
    {
        "date": "2025-01-30",
        "description": "Trump demands OPEC increase production to lower prices",
        "phase": "trump2_opec",
        "domain": "opec_diplomacy",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "original",
        "whipsaw_seq": 1,
        "communication": "truth_social",
        "source": "Truth Social"
    },
    {
        "date": "2025-02-04",
        "description": "Maximum pressure sanctions on Iran oil exports reinstated",
        "phase": "trump2_iran",
        "domain": "sanctions",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "original",
        "whipsaw_seq": 1,
        "communication": "executive_order",
        "source": "Reuters"
    },
    {
        "date": "2025-02-15",
        "description": "OPEC+ rejects Trump demand, reaffirms production cuts",
        "phase": "trump2_opec",
        "domain": "opec_diplomacy",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "reversal",
        "whipsaw_seq": 2,
        "communication": "official_statement",
        "source": "Reuters"
    },
    {
        "date": "2025-02-28",
        "description": "US-Israel joint military operations against Iran begin",
        "phase": "trump2_iran_war",
        "domain": "iran_military",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "original",
        "whipsaw_seq": 1,
        "communication": "military_action",
        "source": "Reuters"
    },
    {
        "date": "2025-03-05",
        "description": "Trump threatens to 'bomb Iran back to the stone age'",
        "phase": "trump2_iran_war",
        "domain": "iran_military",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "truth_social",
        "source": "Truth Social"
    },
    {
        "date": "2025-03-10",
        "description": "Trump signals willingness to negotiate with Iran",
        "phase": "trump2_iran_war",
        "domain": "iran_military",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "reversal",
        "whipsaw_seq": 2,
        "communication": "press_briefing",
        "source": "Reuters"
    },
    {
        "date": "2025-03-15",
        "description": "US strikes Iranian nuclear facility; escalation resumes",
        "phase": "trump2_iran_war",
        "domain": "iran_military",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "re_reversal",
        "whipsaw_seq": 3,
        "communication": "military_action",
        "source": "Reuters"
    },
    {
        "date": "2025-03-20",
        "description": "Trump threatens tariffs on OPEC nations if they don't boost output",
        "phase": "trump2_opec",
        "domain": "opec_diplomacy",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "re_reversal",
        "whipsaw_seq": 3,
        "communication": "truth_social",
        "source": "Truth Social"
    },
    {
        "date": "2025-03-23",
        "description": "Trump announces war will be over 'very soon'; oil drops sharply",
        "phase": "trump2_iran_war",
        "domain": "iran_military",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "reversal",
        "whipsaw_seq": 4,
        "communication": "press_briefing",
        "source": "Reuters"
    },
    {
        "date": "2025-03-28",
        "description": "Iran retaliates with Strait of Hormuz disruption threat",
        "phase": "trump2_iran_war",
        "domain": "iran_military",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "re_reversal",
        "whipsaw_seq": 5,
        "communication": "official_statement",
        "source": "Reuters"
    },
    {
        "date": "2025-04-05",
        "description": "Trump says US will increase domestic production to offset war impact",
        "phase": "trump2_iran_war",
        "domain": "drilling_permitting",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "reversal",
        "whipsaw_seq": 6,
        "communication": "press_briefing",
        "source": "Reuters"
    },
]


def get_event_catalog():
    """Return the event catalog as a DataFrame."""
    df = pd.DataFrame(EVENTS)
    df['date'] = pd.to_datetime(df['date'])
    df['is_whipsaw'] = df['whipsaw_flag'].isin(['reversal', 're_reversal'])

    # Calculate cumulative whipsaw count (for credibility decay variable)
    df = df.sort_values('date').reset_index(drop=True)
    df['cumulative_whipsaw_count'] = df['is_whipsaw'].cumsum()

    # Days since prior reversal
    reversal_dates = df.loc[df['is_whipsaw'], 'date']
    df['days_since_prior_reversal'] = None
    for idx, row in df.iterrows():
        prior = reversal_dates[reversal_dates < row['date']]
        if len(prior) > 0:
            df.at[idx, 'days_since_prior_reversal'] = (row['date'] - prior.iloc[-1]).days

    return df


if __name__ == "__main__":
    catalog = get_event_catalog()
    print(f"Total events: {len(catalog)}")
    print(f"Whipsaw events: {catalog['is_whipsaw'].sum()}")
    print(f"Original events: {(catalog['whipsaw_flag'] == 'original').sum()}")
    print(f"\nPhase breakdown:")
    print(catalog['phase'].value_counts().to_string())
    print(f"\nDomain breakdown:")
    print(catalog['domain'].value_counts().to_string())
    print(f"\nEvents:")
    for _, e in catalog.iterrows():
        flag = f" [{e['whipsaw_flag'].upper()}]" if e['whipsaw_flag'] != 'none' else ''
        print(f"  {e['date'].strftime('%Y-%m-%d')} | {e['direction']:12s} | {e['description'][:70]}{flag}")
