"""
Event catalog for the oil policy whipsaw study.

Each event is coded with:
- date: event date (YYYY-MM-DD)
- description: brief description
- phase: which phase of Trump presidency
- domain: policy domain (iran_military, drilling_permitting, sanctions,
         spr, opec_diplomacy, tariffs)
- direction: pro_supply, anti_supply, or ambiguous
- expected_sign: expected effect on oil prices (+1 = price increase, -1 = price decrease)
- whipsaw_flag: original, reversal, re_reversal, or none
- whipsaw_seq: sequence number within a whipsaw chain
    0 = none, 1 = original, 2 = first reversal, 3 = re_reversal, 4+ = subsequent reversals
- communication: executive_order, twitter (Trump 1.0), truth_social (Trump 2.0),
                 press_briefing, military_action, official_statement
- source: primary source for the event
"""

import pandas as pd
from pathlib import Path
import warnings

EVENTS = [
    # ══════════════════════════════════════════════════════════════════════
    # TRUMP 1.0: 2017-2021
    # ══════════════════════════════════════════════════════════════════════

    # ── Early energy policy ───────────────────────────────────────────────
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
        "date": "2017-08-25",
        "description": "EO 13808 imposes financial sanctions on Venezuela/PDVSA, restricting US debt market access",
        "phase": "trump1_early",
        "domain": "sanctions",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "original",
        "whipsaw_seq": 1,
        "communication": "executive_order",
        "source": "https://www.federalregister.gov/documents/2017/08/29/2017-18468/imposing-additional-sanctions-with-respect-to-the-situation-in-venezuela"
    },

    # ── Iran / JCPOA chain ────────────────────────────────────────────────
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
        "date": "2017-12-22",
        "description": "Tax Cuts and Jobs Act signed; opens ANWR to oil and gas drilling for the first time",
        "phase": "trump1_early",
        "domain": "drilling_permitting",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "official_statement",
        "source": "https://trumpwhitehouse.archives.gov/briefings-statements/remarks-president-trump-signing-h-r-1-tax-cuts-jobs-bill-act-h-r-1370/"
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
        "date": "2018-04-20",
        "description": "Trump tweets 'Oil prices are artificially Very High!' blaming OPEC",
        "phase": "trump1_early",
        "domain": "opec_diplomacy",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "twitter",
        "source": "https://www.cnbc.com/2018/04/20/trump-accused-opec-of-jacking-up-oil-prices-heres-what-he-means.html"
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
        "date": "2018-06-22",
        "description": "OPEC agrees to increase oil production at Vienna meeting, partially unwinding 2016 cuts",
        "phase": "trump1_iran",
        "domain": "opec_diplomacy",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "official_statement",
        "source": "https://www.cnbc.com/2018/06/22/opec-ministers-strike-deal-on-oil-production-levels.html"
    },
    {
        "date": "2018-07-05",
        "description": "Trump tweets at OPEC: prices are up and they are doing little to help, REDUCE PRICING NOW (tweet sent Jul 4; markets closed for holiday)",
        "phase": "trump1_iran",
        "domain": "opec_diplomacy",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "twitter",
        "source": "https://www.cbsnews.com/news/donald-trump-opec-is-doing-little-to-help-with-gas-prices/"
    },
    {
        "date": "2018-09-20",
        "description": "Trump tweets 'The OPEC monopoly must get prices down now!' threatening Middle East security",
        "phase": "trump1_iran",
        "domain": "opec_diplomacy",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "twitter",
        "source": "https://www.cnn.com/2018/09/20/politics/opec-oil-trump-monopoly"
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
        "date": "2018-11-21",
        "description": "Trump tweets 'Thank you to Saudi Arabia' for lower oil prices amid Khashoggi fallout",
        "phase": "trump1_iran",
        "domain": "opec_diplomacy",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "twitter",
        "source": "https://www.cnbc.com/2018/11/21/trump-thanks-saudis-for-lower-oil-prices-amid-khashoggi-criticism.html"
    },
    {
        "date": "2018-12-07",
        "description": "OPEC+ agrees to cut production by 1.2 million bpd despite Trump opposition",
        "phase": "trump1_iran",
        "domain": "opec_diplomacy",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "official_statement",
        "source": "https://www.cnbc.com/2018/12/07/opec-meeting-saudi-arabia-and-russia-look-to-impose-production-cuts.html"
    },
    {
        "date": "2019-01-28",
        "description": "Treasury designates PDVSA under EO 13850, blocking $7B in assets and oil export revenues",
        "phase": "trump1_iran",
        "domain": "sanctions",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "official_statement",
        "source": "https://home.treasury.gov/news/press-releases/sm594"
    },
    {
        "date": "2019-02-25",
        "description": "Trump tweets 'Oil prices getting too high. OPEC, please relax and take it easy'; oil drops 3%",
        "phase": "trump1_iran",
        "domain": "opec_diplomacy",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "twitter",
        "source": "https://www.cnbc.com/2019/02/25/oil-falls-after-trump-says-prices-are-too-high-and-tells-opec-the-world-cannot-take-a-price-hike.html"
    },
    {
        "date": "2019-04-10",
        "description": "EOs 13867/13868 streamline pipeline permitting and energy infrastructure approvals",
        "phase": "trump1_iran",
        "domain": "drilling_permitting",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "executive_order",
        "source": "https://www.presidency.ucsb.edu/documents/executive-order-13868-promoting-energy-infrastructure-and-economic-growth"
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
        "date": "2019-08-05",
        "description": "EO 13884 blocks all property of Venezuelan government, full economic embargo",
        "phase": "trump1_iran",
        "domain": "sanctions",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "executive_order",
        "source": "https://www.wilmerhale.com/en/insights/client-alerts/20190807-president-trump-signs-executive-order-blocking-the-property-of-the-venezuelan-government"
    },
    {
        "date": "2019-09-16",
        "description": "Markets open after Abqaiq-Khurais drone attack (Sep 14); oil surges ~15%, largest spike in decades",
        "phase": "trump1_iran",
        "domain": "iran_military",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "military_action",
        "source": "https://www.npr.org/2019/09/16/761118726/oil-prices-jump-following-drone-attack-on-saudi-oil-facility"
    },

    # ── COVID / OPEC crisis ───────────────────────────────────────────────
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
        "date": "2020-03-13",
        "description": "Trump declares COVID-19 national emergency; directs DOE to fill SPR to maximum capacity",
        "phase": "trump1_covid",
        "domain": "spr",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "press_briefing",
        "source": "https://www.energy.gov/articles/department-energy-executes-direction-president-trump-announces-solicitation-purchase-crude"
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

    # ══════════════════════════════════════════════════════════════════════
    # TRUMP 2.0: 2025-Present
    # ══════════════════════════════════════════════════════════════════════
    # Trump 2.0 dates through June 2025 verified against primary sources
    # (see docs/event_verification.csv). Later dates need verification.

    # ── Early energy policy ───────────────────────────────────────────────
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

    # ── Liberation Day tariffs ────────────────────────────────────────────
    {
        "date": "2025-04-02",
        "description": "Liberation Day: Trump announces 10% baseline reciprocal tariffs on all countries, triggering global market selloff and oil crash",
        "phase": "trump2_early",
        "domain": "tariffs",
        "direction": "ambiguous",
        "expected_sign": -1,
        "whipsaw_flag": "original",
        "whipsaw_seq": 1,
        "communication": "executive_order",
        "source": "https://www.npr.org/2025/04/02/nx-s1-5345802/trump-tariffs-liberation-day"
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
        "date": "2025-04-09",
        "description": "Trump pauses reciprocal tariffs above 10% for 90 days for all countries except China",
        "phase": "trump2_early",
        "domain": "tariffs",
        "direction": "ambiguous",
        "expected_sign": 1,
        "whipsaw_flag": "reversal",
        "whipsaw_seq": 2,
        "communication": "truth_social",
        "source": "https://www.cnbc.com/2025/04/09/us-crude-oil-tumbles-as-china-imposes-retaliatory-tariffs.html"
    },

    # ── OPEC+ output unwinding ────────────────────────────────────────────
    {
        "date": "2025-05-03",
        "description": "OPEC+ announces second consecutive accelerated 411k bpd output hike for June",
        "phase": "trump2_opec",
        "domain": "opec_diplomacy",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "official_statement",
        "source": "https://www.cnbc.com/2025/05/03/opec-agrees-another-accelerated-oil-output-hike-for-june-sources-say.html"
    },
    {
        "date": "2025-05-13",
        "description": "Trump Gulf tour; Saudi Arabia announces $600B investment commitment including energy fund",
        "phase": "trump2_opec",
        "domain": "opec_diplomacy",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "press_briefing",
        "source": "https://www.whitehouse.gov/fact-sheets/2025/05/fact-sheet-president-donald-j-trump-secures-historic-600-billion-investment-commitment-in-saudi-arabia/"
    },
    {
        "date": "2025-05-31",
        "description": "OPEC+ agrees to third consecutive 411k bpd accelerated output hike for July",
        "phase": "trump2_opec",
        "domain": "opec_diplomacy",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "official_statement",
        "source": "https://www.cnbc.com/2025/05/31/opec-july-oil-output.html"
    },

    # ── Twelve-Day War ────────────────────────────────────────────────────
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

    # ── Post-war OPEC+ and sanctions (July-Dec 2025) ──────────────────────
    {
        "date": "2025-07-05",
        "description": "OPEC+ accelerates output unwinding, approving 548k bpd increase for August",
        "phase": "trump2_opec",
        "domain": "opec_diplomacy",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "official_statement",
        "source": "https://www.agbi.com/oil-and-gas/2025/07/opec-accelerates-oil-output-to-548000-bpd-in-august/"
    },
    {
        "date": "2025-08-03",
        "description": "OPEC+ agrees to 547k bpd output increase for September",
        "phase": "trump2_opec",
        "domain": "opec_diplomacy",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "official_statement",
        "source": "https://www.thenationalnews.com/business/energy/2025/08/03/opec-agrees-to-raise-oil-output-for-september/"
    },
    {
        "date": "2025-09-07",
        "description": "OPEC+ slows pace of output increases to 137k bpd for October as glut fears build",
        "phase": "trump2_opec",
        "domain": "opec_diplomacy",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "official_statement",
        "source": "https://energynow.com/2025/09/eight-opec-members-agree-to-raise-oil-production-by-137000-bpd-in-october/"
    },
    {
        "date": "2025-10-09",
        "description": "Treasury sanctions 50+ entities in Iran oil network including Chinese teapot refineries and shadow fleet",
        "phase": "trump2_iran",
        "domain": "sanctions",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "official_statement",
        "source": "https://www.state.gov/releases/office-of-the-spokesperson/2025/10/sweeping-sanctions-on-irans-energy-exports"
    },
    {
        "date": "2025-11-02",
        "description": "OPEC+ pauses output hikes for Q1 2026 due to demand weakness, reversing unwinding trend",
        "phase": "trump2_opec",
        "domain": "opec_diplomacy",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "reversal",
        "whipsaw_seq": 4,
        "communication": "official_statement",
        "source": "https://www.opec.org/pr-detail/579-02-november-2025.html"
    },
    {
        "date": "2025-11-24",
        "description": "Interior Dept proposes massive 2026-2031 offshore leasing program: 34 sales across 1.27 billion acres",
        "phase": "trump2_early",
        "domain": "drilling_permitting",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "official_statement",
        "source": "https://www.doi.gov/pressreleases/interior-launches-expansive-11th-national-offshore-leasing-program-advance-us-energy"
    },
    {
        "date": "2025-11-30",
        "description": "OPEC+ reaffirms Q1 2026 output pause and extends group-wide cuts through end of 2026",
        "phase": "trump2_opec",
        "domain": "opec_diplomacy",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "official_statement",
        "source": "https://www.opec.org/pr-detail/243582-30-november-2025.html"
    },

    # ── 2026 Iran War / Hormuz Crisis ─────────────────────────────────────
    {
        "date": "2026-02-26",
        "description": "Third round of US-Iran nuclear talks in Geneva ends without deal; Trump 'not thrilled'",
        "phase": "trump2_iran",
        "domain": "iran_military",
        "direction": "ambiguous",
        "expected_sign": 1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "official_statement",
        "source": "https://www.cnbc.com/2026/02/27/us-iran-nuclear-talks-oil-middle-east.html"
    },
    {
        "date": "2026-02-28",
        "description": "Operation Epic Fury: US-Israel air campaign against Iran; Khamenei killed; Iran retaliates, closes Strait of Hormuz",
        "phase": "trump2_iran_war",
        "domain": "iran_military",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "re_reversal",
        "whipsaw_seq": 5,
        "communication": "military_action",
        "source": "https://en.wikipedia.org/wiki/2026_Iran_war"
    },
    {
        "date": "2026-03-01",
        "description": "OPEC+ emergency meeting agrees to 206k bpd increase amid Strait of Hormuz closure",
        "phase": "trump2_opec",
        "domain": "opec_diplomacy",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "official_statement",
        "source": "https://www.cnbc.com/2026/03/01/opec-to-raise-oil-output-slightly-even-as-iran-war-disrupts-shipments.html"
    },
    {
        "date": "2026-03-11",
        "description": "Trump authorizes 172M barrel SPR emergency release; IEA coordinates 400M barrel global drawdown",
        "phase": "trump2_iran_war",
        "domain": "spr",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "official_statement",
        "source": "https://www.cnbc.com/2026/03/11/iran-war-trump-oil-strategic-petroleum-reserve.html"
    },
    {
        "date": "2026-03-12",
        "description": "Treasury eases sanctions on Russian oil (GL-134): 30-day waiver suspending price cap",
        "phase": "trump2_iran_war",
        "domain": "sanctions",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "official_statement",
        "source": "https://www.washingtonpost.com/business/2026/03/12/russian-oil-sanctions-lifted-iran/"
    },
    {
        "date": "2026-03-20",
        "description": "Treasury lifts sanctions on 140M barrels of Iranian crude on vessels (30-day waiver) to ease oil crisis",
        "phase": "trump2_iran_war",
        "domain": "sanctions",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "reversal",
        "whipsaw_seq": 2,
        "communication": "official_statement",
        "source": "https://www.washingtonpost.com/business/2026/03/20/iran-oil-sanctions-trump/"
    },
    {
        "date": "2026-04-01",
        "description": "Trump primetime address threatens to bomb Iran 'back to the Stone Ages'; oil spikes above $105",
        "phase": "trump2_iran_war",
        "domain": "iran_military",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "press_briefing",
        "source": "https://www.axios.com/2026/04/02/trump-bomb-iran-stone-ages-power-plants"
    },
    {
        "date": "2026-04-07",
        "description": "Trump announces Pakistan-mediated ceasefire with Iran after threatening escalation hours earlier",
        "phase": "trump2_iran_war",
        "domain": "iran_military",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "reversal",
        "whipsaw_seq": 6,
        "communication": "truth_social",
        "source": "https://www.npr.org/2026/04/07/nx-s1-5776377/iran-war-updates"
    },
    {
        "date": "2026-04-21",
        "description": "Trump indefinitely extends Iran ceasefire; maintains naval blockade",
        "phase": "trump2_iran_war",
        "domain": "iran_military",
        "direction": "pro_supply",
        "expected_sign": -1,
        "whipsaw_flag": "none",
        "whipsaw_seq": 0,
        "communication": "official_statement",
        "source": "https://www.cnbc.com/2026/04/21/trump-iran-war-ceasefire.html"
    },
    {
        "date": "2026-04-24",
        "description": "Treasury sanctions Chinese teapot refinery Hengli and ~40 Iranian oil shipping companies",
        "phase": "trump2_iran_war",
        "domain": "sanctions",
        "direction": "anti_supply",
        "expected_sign": 1,
        "whipsaw_flag": "re_reversal",
        "whipsaw_seq": 3,
        "communication": "official_statement",
        "source": "https://fortune.com/2026/04/24/trump-oil-sanctions-china-iran-war-xi-jinping/"
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
