# Evidence register and acquisition gaps

Research snapshot: September 23, 2026. The analytical window is 2016–2025 (ten completed seasons). The downloaded 2015 injury file is an archival supplement, not included in comparisons or models. No 2026 partial-season extrapolation.

## Observed public football records

- [nflverse injury reports](https://nflreadr.nflverse.com/reference/load_injuries.html), [field definitions](https://nflreadr.nflverse.com/articles/dictionary_injuries.html): player-week reporting snapshots. An Out designation is a report status, not a new injury or total absence measure. Injury dates, mechanisms, diagnoses, and individual exposure histories are unavailable.
- [Weekly roster source](https://github.com/nflverse/nflreadr/blob/main/R/load_rosters_weekly.R), [roster statuses](https://nflreadr.nflverse.com/articles/dictionary_roster_status.html): age and broad reserve-list context. RES is broader than injured reserve. Do not relabel the project's reserve counts as IR counts.
- [Schedules](https://github.com/nflverse/nfldata/blob/master/data/games.csv): completed regular-season games, scores, rest, and teams. Canceled/unplayed games are excluded by requiring scores. Bye weeks are not games. Normalize relocated franchise abbreviations.
- [OverTheCap via nflverse](https://nflreadr.nflverse.com/reference/load_contracts.html), [contract definitions](https://nflreadr.nflverse.com/articles/dictionary_contracts.html): nested season-level compensation values are in USD millions. Join by GSIS ID, year, and team; collapse identical season values; exclude conflicting values. Current historical snapshots are not guaranteed to reproduce information available at the original date.
- [2016 reporting change](https://www.nfl.com/_amp/competition-committee-approves-revisions-to-injury-report-0ap3000000688693): reporting categories changed in 2016. The main analysis begins that year.

Raw downloads are retained. `data/source_manifest.json` records URLs, retrieval time, bytes, and SHA-256 hashes. `data/processed/quality_audit.json` records exclusions. These are public records; no private medical records are used.

## Environmental hypothesis

[WHO overview](https://www.who.int/news-room/questions-and-answers/item/radiation-electromagnetic-fields) and [WHO extremely-low-frequency assessment](https://www.who.int/publications/b/31501) provide scientific background. Frequency and dose matter. A nearby power facility is not an exposure measurement, and there is no validated facility-specific exposure-to-ligament-injury function available to this project. This is a focused background review, not a systematic literature review or a medical safety assessment.

[March 29, 2026 reporting of John Lynch's statement](https://www.nbcbayarea.com/news/national-international/john-lynch-electrical-substation-theory-scientist/4060035/) describes a scientist's assessment that the site was safe. The underlying measurement dataset, sampling plan, instruments, and full report have not been acquired. A reported statement is not entered as measured exposure data or converted to a numerical hazard probability.

**Status: no exposure dataset. No causal estimate. No empirically estimated probability that the substation causes injuries.** Scenario probabilities are user assumptions, including zero, and are not updated using injury outlier status.

## Financial reference points

`data/context_sources.csv` contains manually transcribed numerical facts with exact URLs and reference periods. Forbes estimates place the 49ers at $8.6 billion enterprise value in 2025 and report $723 million revenue and $115 million operating income for the 2024 season. These are publisher estimates, not audited 49ers statements. Value is a stock, revenue is a flow; neither is a direct estimate of injury cost.

The Jaguars published a $120 million project cost for their 2023 training facility. The Chargers engineering project profile reports $250 million. They illustrate scope; they are not comparable bids, adjusted Bay Area costs, or estimates for merely renting a field. No inflation/location conversion is applied automatically.

[Packers financial discussion](https://www.packers.com/news/packers-finances-remain-strong-amidst-changing-nfl-landscape-2026) illustrates why shared national revenue and local performance-sensitive revenue differ. Do not multiply all franchise revenue by losses or wins.

## Inputs not available from these public data

1. Independent repeated field measurements with calibration, frequency, location, load, duration, and individual time-at-site histories.
2. Consent-governed clinical injury records, exact onset, contact/noncontact mechanism, training workload and treatment.
3. A complete consistent ten-year injury-attributable games-missed series. Out reports and broad reserve status are separate partial proxies, not a replacement for one.
4. Internal contribution margins per win, injury-attributable replacement/medical expenses, revenue elasticity, and brand/recruitment effects.
5. Bay Area site bids, land/lease costs, build-out schedule, insurance, financing, operating changes, and disposal/residual values.
6. A validated study design with sensitivity/specificity for establishing the causal hazard. EMF measurement alone is not such a test.

These gaps are surfaced in the app. No absent measurements are replaced with synthetic observations. Simulations are explicitly hypothetical.

## Attribution and reuse

nflverse data repository lists CC-BY-4.0; underlying NFL and OverTheCap data remain subject to their respective terms. Attribute nflverse and OverTheCap and review upstream terms before republishing raw data. This local research package preserves provenance; it grants no additional rights to third-party data. The portfolio's code license covers only original code.
