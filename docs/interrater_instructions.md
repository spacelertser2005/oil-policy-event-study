# Inter-Rater Reliability Coding Instructions

**Project:** Presidential Oil Policy Event Study (ECON 401, University of Oregon)
**Researcher:** Matthew Lertsmitivanta
**Advisor:** Prof. Bruce Blonigen

---

## What This Project Is About

This study examines how presidential actions on oil policy (executive orders, tweets, sanctions, military decisions) affect crude oil prices. We are especially interested in "whipsaw" events -- cases where the president reverses a previous policy in the same area, flip-flopping back and forth. Your job is to independently code 12 events so we can measure how consistently two people apply the same coding rules (a statistic called Cohen's Kappa). This is a standard reliability check in event study research.

**Important: Code each event on your own.** Do not look at anyone else's coding or discuss the events with other coders before submitting your sheet. Use only the source URL provided (and the event description) to inform your decisions.

**Estimated time: ~30 minutes.**

---

## What You Need to Code

For each event in the coding sheet (`interrater_coding_sheet.csv`), fill in these 5 fields:

| # | Field | What It Means |
|---|-------|---------------|
| 1 | `direction` | What does this event do to global oil *supply*? |
| 2 | `expected_sign` | What should happen to oil *prices* as a result? |
| 3 | `whipsaw_flag` | Is this event part of a policy flip-flop chain? |
| 4 | `whipsaw_seq` | If yes, where does it sit in the chain? |
| 5 | `domain` | Which policy area does this event belong to? |

You can also add free-text notes in the `coder_notes` column if something is unclear or you want to explain your reasoning.

---

## Field Definitions and Allowed Values

### 1. `direction`

This captures the expected effect on **global oil supply** (not price).

| Value | Meaning | Example |
|-------|---------|---------|
| `pro_supply` | The event increases (or is expected to increase) oil supply, or reduces geopolitical risk to supply | Lifting sanctions on a producer country; ordering more drilling; pressuring OPEC to pump more |
| `anti_supply` | The event decreases (or is expected to decrease) oil supply, or raises geopolitical risk to supply | Imposing sanctions on a producer; military strikes near oil infrastructure; OPEC cutting production |
| `ambiguous` | The net supply effect is genuinely unclear | A military strike is ordered then cancelled the same day; a policy has offsetting provisions |

**Tip:** Ask yourself, "Does this event put more oil on the market or less?" If more, it is `pro_supply`. If less, `anti_supply`. If you genuinely cannot tell, use `ambiguous`.

### 2. `expected_sign`

This captures the expected effect on **oil prices** (not supply). It is the mirror of `direction` in most cases:

| Value | Meaning | Typical Direction Pairing |
|-------|---------|--------------------------|
| `+1` | Oil price expected to go UP | Usually paired with `anti_supply` (less supply = higher price) or geopolitical risk events |
| `-1` | Oil price expected to go DOWN | Usually paired with `pro_supply` (more supply = lower price) |

**Note:** In almost all cases, `pro_supply` pairs with `-1` and `anti_supply` pairs with `+1`. The exception is `ambiguous` direction, where you still need to make a judgment call about the most likely price impact. Use `+1` if the dominant effect is uncertainty or risk, `-1` if the dominant effect is supply relief.

### 3. `whipsaw_flag`

This captures whether the event is part of a chain of policy reversals **within the same policy domain**.

| Value | Meaning | When to Use |
|-------|---------|-------------|
| `none` | Standalone event, not part of a flip-flop chain | The event does not reverse any prior event in the same domain |
| `original` | First event that establishes a policy direction in a domain | This is the starting point of a potential chain |
| `reversal` | A policy that reverses the original | Same domain as the original, but direction flips (e.g., `pro_supply` after `anti_supply`) |
| `re_reversal` | A further flip-flop continuing the chain | Same domain, direction flips yet again |

**Critical rule:** A reversal must target the **same policy domain** as the original. An event about Iran sanctions cannot be a reversal of a drilling/permitting event, even if both affect supply in the same direction.

### 4. `whipsaw_seq`

This is a number that tracks position within a whipsaw chain:

| Value | Meaning |
|-------|---------|
| `0` | Not part of a chain (use when `whipsaw_flag` = `none`) |
| `1` | First event in the chain (use when `whipsaw_flag` = `original`) |
| `2` | First reversal |
| `3` | First re-reversal |
| `4+` | Continues incrementing with each subsequent flip |

**Pattern check:** Odd-numbered positions (1, 3, 5...) should share one direction, and even-numbered positions (2, 4...) should share the opposite direction. If this pattern breaks, reconsider whether the events really belong in the same chain.

### 5. `domain`

This identifies the policy area. Use one of these values:

| Value | Covers |
|-------|--------|
| `drilling_permitting` | Executive orders on drilling, pipeline approvals, offshore leasing, energy regulation rollbacks |
| `sanctions` | Economic sanctions on oil-producing countries (Iran, Venezuela, Russia) -- both imposing and lifting |
| `iran_military` | Military actions, threats, or de-escalation involving Iran and its proxies |
| `opec_diplomacy` | Presidential pressure on OPEC, OPEC production decisions responding to that pressure, Saudi/Gulf diplomacy |
| `spr` | Strategic Petroleum Reserve releases or fills |
| `tariffs` | Trade tariffs that affect oil demand or global trade flows |

**If none of the above fit**, write the domain you think is most appropriate in the `coder_notes` column.

---

## Understanding Whipsaw Chains: A Simple Example

Imagine the president takes these three actions, all in the `sanctions` domain:

1. **January:** Imposes sanctions on Country X (cuts their oil exports)
   - direction: `anti_supply`, whipsaw_flag: `original`, whipsaw_seq: `1`

2. **March:** Grants waivers that let most countries keep buying Country X's oil
   - direction: `pro_supply`, whipsaw_flag: `reversal`, whipsaw_seq: `2`

3. **June:** Revokes all waivers and demands zero exports from Country X
   - direction: `anti_supply`, whipsaw_flag: `re_reversal`, whipsaw_seq: `3`

This is a whipsaw chain because the same president flip-flopped on the **same policy** (sanctions on Country X) three times. Each step reverses the previous one. The sequence number increments each time. The direction alternates: anti, pro, anti.

A separate executive order about domestic drilling would **not** be part of this chain, even if it also affects oil supply, because it is in a different domain (`drilling_permitting`).

---

## How to Code Each Event

For each row in the coding sheet:

1. **Read the description** to understand what happened.
2. **Open the source URL** in your browser. Skim the article to confirm what the event was and when it happened.
3. **Code `direction`:** Does this event increase or decrease oil supply?
4. **Code `expected_sign`:** Should oil prices go up (+1) or down (-1)?
5. **Code `domain`:** Which policy area is this?
6. **Code `whipsaw_flag` and `whipsaw_seq`:** Look at the other events in the sheet. Is this event a reversal of a prior event *in the same domain*? If so, what position is it in the chain? (Note: not all events in a given chain may be present in your 12-event subset. Code based on what you know from the descriptions and sources provided.)
7. **Add notes** if anything is ambiguous or if you want to explain your reasoning.

---

## Submitting Your Coding

Fill in the five blank columns in `interrater_coding_sheet.csv` and return the completed file to Matt. You can use Excel, Google Sheets, or any text editor -- just keep the CSV format intact.

Thank you for helping with this project.
