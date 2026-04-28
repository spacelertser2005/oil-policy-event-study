# Whipsaw Chain Coding Protocol

**Project:** Presidential Oil Policy Whipsaw Event Study (ECON 401)
**Author:** Matthew Lertsmitivanta
**Purpose:** Reference guide for all event coders, including second coders for inter-rater reliability testing (target Cohen's Kappa > 0.75)

---

## 1. Event Identification Rules

**Include** an event if ALL of the following are true:

- It is a presidential action, statement, or executive order (not a market rumor or analyst speculation).
- It plausibly shifts oil supply expectations -- either by changing production policy, imposing/lifting sanctions on a producer nation, or altering geopolitical risk to supply infrastructure.
- It can be dated to a specific calendar day using a primary source (Reuters, WSJ, or the Federal Register).

**Exclude** the following:

- Routine OPEC meetings with no policy surprise (unless the meeting outcome directly responds to documented presidential pressure).
- Macroeconomic announcements (Fed rate decisions, GDP releases, jobs reports) even if they move oil prices.
- Congressional legislation unless the president signs it or issues a veto.
- Pure market-driven price movements with no identifiable presidential trigger.
- Analyst or media commentary about what the president *might* do.

**Gray area -- OPEC responding to Trump pressure:** Code the presidential statement demanding OPEC action as the event (domain = `opec_diplomacy`). If OPEC later responds, code the OPEC response as a separate event only if the response itself constitutes a policy surprise. Do not double-count the same policy impulse.

---

## 2. Whipsaw Chain Logic

A whipsaw chain tracks successive policy reversals within the **same policy domain**. The chain captures how many times the president has flip-flopped on a given policy area.

### Coding `whipsaw_flag` and `whipsaw_seq`

| Flag | Seq | Definition | Decision Rule |
|------|-----|------------|---------------|
| `none` | 0 | Standalone event, not part of a chain | The event does not reverse or continue a prior event in the same domain. |
| `original` | 1 | First event establishing a policy direction within a domain | No prior event in this domain exists, OR this begins a new distinct chain. |
| `reversal` | 2 | Policy that reverses the original | Must target the **same domain** as the original AND push the `direction` the opposite way (e.g., `anti_supply` after `pro_supply`). |
| `re_reversal` | 3+ | Further flip-flops continuing the chain | Same domain, direction flips again. Increment `whipsaw_seq` by 1 each time. |

**Critical rule:** A reversal must target the SAME policy domain as the original. An `iran_military` event cannot be a reversal of a `drilling_permitting` event, even if both affect supply in the same direction.

**Chain continuation:** Odd-numbered `whipsaw_seq` values (1, 3, 5, ...) should share one direction (e.g., `anti_supply`), and even-numbered values (2, 4, ...) should share the opposite direction (e.g., `pro_supply`). If this pattern breaks, re-examine whether the events truly belong in the same chain.

**Starting a new chain:** If a significant policy shift in a domain occurs after a long gap (judgment call, but roughly > 2 years or a new presidential term), it may warrant starting a fresh chain at `seq = 1` rather than continuing the old one. Document the reasoning.

---

## 3. Ambiguous Cases -- Decision Rules

| Situation | Rule |
|-----------|------|
| OPEC responds to Trump pressure | Code the Trump statement as one event (`opec_diplomacy`). Code the OPEC response as a separate event only if it is a genuine policy surprise. |
| Market event triggered indirectly | Only code if there is a clear, documented presidential action or statement. Market moves alone do not qualify. |
| Multiple presidential actions on the same day | Merge into a single event. Use the most consequential action for the description. Note the others in the source field. |
| Presidential tweet/post vs. formal policy | Code the earliest market-moving communication. If a Truth Social post precedes a formal EO by days, code the post date. If both land the same day, code as one event with `communication` set to the formal channel. |
| Sanctions with partial waivers | The direction depends on the net effect. Full sanctions = `anti_supply`. Sanctions with generous waivers = `pro_supply` (because waivers soften the original restriction). Use judgment and document in the source field. |
| Military action ordered then cancelled | Code as `ambiguous` direction. The market impact reflects both the threat and the stand-down. |
| Event falls on a weekend or holiday | Use the date of the action itself (the actual calendar day). The event study pipeline will map it to the next trading day automatically. |

---

## 4. Full Coding Schema

Every event in `src/event_catalog.py` must include these fields:

| Field | Type | Allowed Values | Notes |
|-------|------|----------------|-------|
| `date` | String | `YYYY-MM-DD` | Must match the date in the primary source. |
| `description` | String | Free text | Brief and factual. No editorializing. |
| `phase` | String | `trump1_early`, `trump1_iran`, `trump1_covid`, `trump2_early`, `trump2_iran`, `trump2_iran_war`, `trump2_opec` | Analytical grouping by time period. |
| `domain` | String | `iran_military`, `drilling_permitting`, `sanctions`, `spr`, `opec_diplomacy` | Policy area. Add new domains only if none of the existing five fit. |
| `direction` | String | `pro_supply`, `anti_supply`, `ambiguous` | Expected effect on global oil supply. |
| `expected_sign` | Integer | `+1` or `-1` | Expected effect on oil **price**. `+1` = price up (supply contraction or geopolitical risk). `-1` = price down (supply expansion). |
| `whipsaw_flag` | String | `original`, `reversal`, `re_reversal`, `none` | Position in whipsaw chain. See Section 2. |
| `whipsaw_seq` | Integer | `0` = none, `1` = original, `2`+ = chain position | See Section 2. |
| `communication` | String | `executive_order`, `twitter` (Trump 1.0), `truth_social` (Trump 2.0), `press_briefing`, `military_action`, `official_statement` | Channel of the announcement. Use `twitter` for pre-2021 social media posts, `truth_social` for 2025+. |
| `source` | String | Citation or URL | Must be a primary source: Reuters, WSJ, Federal Register, or official White House page. Wikipedia is acceptable only for well-documented military events with inline citations. |

**Computed fields** (generated automatically by `get_event_catalog()` -- do not code manually):
- `is_whipsaw`: True if `whipsaw_flag` is `reversal` or `re_reversal`.
- `cumulative_whipsaw_count`: Running total of whipsaw events up to this date.
- `days_since_prior_reversal`: Calendar days since the most recent prior reversal.

---

## 5. Worked Example: Iran Sanctions Whipsaw Chain

This chain spans the `sanctions` domain (with the initiating event in `iran_military`) across Trump 1.0 and into Trump 2.0. It illustrates how the direction alternates with each step:

| # | Date | Description | Domain | Direction | Flag | Seq |
|---|------|-------------|--------|-----------|------|-----|
| 1 | 2017-10-13 | Decertifies JCPOA but does not withdraw | iran_military | anti_supply | original | 1 |
| 2 | 2018-01-12 | Waives Iran sanctions again, signals "last time" | sanctions | pro_supply | reversal | 2 |
| 3 | 2018-05-08 | Withdraws from JCPOA, reinstates sanctions | sanctions | anti_supply | re_reversal | 3 |
| 4 | 2018-11-05 | Sanctions take effect but 8 countries get waivers | sanctions | pro_supply | reversal | 4 |
| 5 | 2019-04-22 | Ends all waivers, demands zero Iranian exports | sanctions | anti_supply | re_reversal | 5 |

**Why this is a single chain:** Every event after the original targets the same fundamental policy question -- how aggressively the US restricts Iranian oil exports. The direction alternates between tightening (`anti_supply`) and loosening (`pro_supply`), which is precisely the whipsaw pattern this study measures.

**Why the domain shifts from `iran_military` to `sanctions`:** The initiating event (JCPOA decertification) is a diplomatic/military posture, but the subsequent events are sanctions actions. This is acceptable because they belong to the same policy chain. The domain field captures the specific policy instrument; the chain captures the logical sequence.

---

## 6. Source Verification

Every event date must be verified against at least one primary source before being marked as confirmed.

**Acceptable primary sources (in order of preference):**
1. Federal Register (for executive orders and proclamations)
2. Reuters or AP wire reports (timestamped)
3. Wall Street Journal reporting
4. Official White House fact sheets or press releases (whitehouse.gov)
5. Bloomberg (for OPEC-related events)

**Verification process:**
1. Look up the event in the primary source.
2. Confirm the date matches. If the source says the action happened on a different date, update the catalog.
3. Record the source URL or citation in the `source` field.
4. Log the verification in `docs/event_verification.csv` with columns: `date`, `description`, `source_url`, `verified_by`, `verification_date`.

**If the date cannot be verified:** Flag it in the verification CSV with `verified = FALSE` and a note explaining the discrepancy. Do not include unverified events in the final analysis.
