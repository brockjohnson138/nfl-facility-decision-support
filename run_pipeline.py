"""Run acquisition, preparation, descriptive analysis, modeling, finance, and scenarios."""
from pathlib import Path
import json
import pandas as pd
from src.acquire import main as acquire
from src.prepare import prepare
from src.analysis import analyze
from src.modeling import run_models
from src.finance import prepare_finance
from src.decision import Scenario, evaluate, simulate, sensitivity_grid

ROOT = Path(__file__).resolve().parent

def main():
    acquire()
    prepare()
    findings = analyze()
    model_card = run_models()
    finance = prepare_finance()
    scenario = Scenario()
    out = ROOT / "outputs"
    (out / "scenario_baseline.json").write_text(json.dumps(evaluate(scenario), indent=2))
    sensitivity_grid(scenario).to_csv(out / "decision_sensitivity.csv", index=False)
    simulate(scenario, n=20000).to_csv(out / "decision_simulation.csv", index=False)
    print(json.dumps({"findings": findings, "selected_model": model_card["selected_model"], "finance_rows": len(finance), "scenario": evaluate(scenario)}, indent=2))

if __name__ == "__main__":
    main()
