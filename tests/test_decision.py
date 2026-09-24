import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.decision import Scenario, evaluate, sensitivity_grid


def test_zero_hazard_prefers_stay_under_baseline_costs():
    result = evaluate(replace(Scenario(), hazard_probability=0.0))
    assert result["preferred_action"] == "Stay"
    assert result["state_move_npv_m"]["no_hazard"] < 0


def test_sensitivity_grid_has_complete_square():
    grid = sensitivity_grid(Scenario())
    assert len(grid) == 21 * 21
    assert grid[["hazard_probability", "attributable_fraction"]].drop_duplicates().shape[0] == 441


def test_invalid_probabilities_are_rejected():
    with pytest.raises(ValueError):
        evaluate(replace(Scenario(), hazard_probability=1.1))


def test_perfect_information_is_nonnegative():
    result = evaluate(Scenario())
    assert result["perfect_information_value_m"] >= 0
    assert np.isfinite(result["break_even_probability_times_fraction"])
