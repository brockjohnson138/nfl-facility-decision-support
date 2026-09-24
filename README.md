# NFL Facility Decision Support

This project investigates whether the 49ers' player-availability history is unusual and what evidence would justify staying, commissioning further study, or relocating a practice facility. It is a decision-support portfolio project, not a medical study and not a claim that electromagnetic fields cause injuries.

## What it does

1. Downloads public nflverse injury-report, weekly-roster, schedule, and contract snapshots.
2. Builds an auditable team-game panel. The primary outcome is the number of players designated **Out** on an observed weekly report. That is a reporting measure, not injury incidence, games missed, or injured-reserve burden.
3. Benchmarks San Francisco against other teams and runs sensitivity definitions.
4. Trains temporally evaluated Poisson, gradient-boosting, and random-forest models to predict reported Out counts.
5. Estimates descriptive compensation allocation around Out designations without calling it avoidable injury cost.
6. Evaluates stay, investigate, and relocate under explicit hypothetical hazard and financial assumptions.

## Run it

From this directory:

```bash
python -m pip install -r requirements.txt
python run_pipeline.py
```

The script writes processed data and model outputs to `data/processed/` and `outputs/`. Existing downloads are reused; provenance and SHA-256 hashes are in `data/source_manifest.json`.

## Interpretation guardrails

The project deliberately does not estimate an electromagnetic causal effect from team injury reports. A nearby substation is not an exposure measurement, and no validated exposure-to-ligament-injury function is available. Scenario probabilities are user-entered assumptions. See `docs/EVIDENCE.md` for sources, limitations, and acquisition gaps.

The most decision-relevant output is the break-even surface: how large the probability of a real hazard and the attributable reduction in reported injury burden would need to be before relocation pays for itself. Results are hypothetical until facility measurements, medical records, exposure histories, and site-specific costs are obtained.
