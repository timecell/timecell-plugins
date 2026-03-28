"""Unit tests for scripts/hedge-engine.py"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts to path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# Import with module name matching the filename (hedge-engine.py -> hedge_engine)
import importlib
hedge_engine = importlib.import_module("hedge-engine")

_classify_layer = hedge_engine._classify_layer
_exit_recommendation = hedge_engine._exit_recommendation
calculate_hedge_budget = hedge_engine.calculate_hedge_budget
calculate_layer_exits = hedge_engine.calculate_layer_exits
calculate_geometric_mean_cagr = hedge_engine.calculate_geometric_mean_cagr
calculate_hedge_coverage = hedge_engine.calculate_hedge_coverage
calculate_collar_recommendation = hedge_engine.calculate_collar_recommendation
calculate_cagr_sensitivity = hedge_engine.calculate_cagr_sensitivity
calculate_hedge_ratio = hedge_engine.calculate_hedge_ratio
calculate_geometric_breakeven = hedge_engine.calculate_geometric_breakeven


# ---------------------------------------------------------------------------
# _classify_layer (internal helper)
# ---------------------------------------------------------------------------

class TestClassifyLayer:
    def test_none_delta_defaults_core(self):
        assert _classify_layer(None) == "core"

    def test_buffer_high_delta(self):
        assert _classify_layer(-0.05) == "buffer"
        assert _classify_layer(0.04) == "buffer"

    def test_core_mid_delta(self):
        assert _classify_layer(-0.02) == "core"
        assert _classify_layer(0.03) == "core"

    def test_disaster_low_delta(self):
        assert _classify_layer(-0.01) == "disaster"
        assert _classify_layer(0.005) == "disaster"

    def test_boundary_004(self):
        assert _classify_layer(0.04) == "buffer"

    def test_boundary_0015(self):
        assert _classify_layer(0.015) == "core"


# ---------------------------------------------------------------------------
# _exit_recommendation (internal helper)
# ---------------------------------------------------------------------------

class TestExitRecommendation:
    # Buffer layer
    def test_buffer_3x_full_exit(self):
        rec, pct, _ = _exit_recommendation("buffer", 3.0)
        assert rec == "full_exit" and pct == 100

    def test_buffer_2x_partial(self):
        rec, pct, _ = _exit_recommendation("buffer", 2.5)
        assert rec == "partial_exit_50" and pct == 50

    def test_buffer_below_threshold(self):
        rec, pct, _ = _exit_recommendation("buffer", 1.5)
        assert rec == "hold" and pct == 0

    # Core layer
    def test_core_8x_full_exit(self):
        rec, pct, _ = _exit_recommendation("core", 8.0)
        assert rec == "full_exit" and pct == 100

    def test_core_5x_partial_50(self):
        rec, pct, _ = _exit_recommendation("core", 5.0)
        assert rec == "partial_exit_50" and pct == 50

    def test_core_3x_partial_25(self):
        rec, pct, _ = _exit_recommendation("core", 3.5)
        assert rec == "partial_exit_25" and pct == 25

    def test_core_below_threshold(self):
        rec, pct, _ = _exit_recommendation("core", 2.0)
        assert rec == "hold" and pct == 0

    # Disaster layer
    def test_disaster_20x_majority(self):
        rec, pct, _ = _exit_recommendation("disaster", 25.0)
        assert rec == "partial_exit_majority" and pct == 75

    def test_disaster_10x_partial_25(self):
        rec, pct, _ = _exit_recommendation("disaster", 12.0)
        assert rec == "partial_exit_25" and pct == 25

    def test_disaster_5x_recycle(self):
        rec, pct, _ = _exit_recommendation("disaster", 7.0)
        assert rec == "recycle_premium" and pct == 0

    def test_disaster_below_threshold(self):
        rec, pct, _ = _exit_recommendation("disaster", 3.0)
        assert rec == "hold" and pct == 0


# ---------------------------------------------------------------------------
# calculate_hedge_budget
# ---------------------------------------------------------------------------

class TestCalculateHedgeBudget:
    def test_accumulation_phase(self):
        result = calculate_hedge_budget({"temperature": 20, "portfolio_value_usd": 10_000_000})
        assert result["cycle_phase"] == "accumulation"
        assert result["target_pct"] == 0.75
        assert result["target_usd"] == 75_000
        assert result["floor_pct"] == 0.75

    def test_mid_cycle_phase(self):
        result = calculate_hedge_budget({"temperature": 50, "portfolio_value_usd": 10_000_000})
        assert result["cycle_phase"] == "mid_cycle"
        assert result["target_pct"] == 1.25

    def test_late_cycle_phase(self):
        result = calculate_hedge_budget({"temperature": 70, "portfolio_value_usd": 10_000_000})
        assert result["cycle_phase"] == "late_cycle"
        assert result["target_pct"] == 1.75

    def test_overheated_phase(self):
        result = calculate_hedge_budget({"temperature": 80, "portfolio_value_usd": 10_000_000})
        assert result["cycle_phase"] == "overheated"
        assert result["target_pct"] == 2.25

    def test_credit_impulse_both_decelerating(self):
        result = calculate_hedge_budget({
            "temperature": 50,
            "portfolio_value_usd": 10_000_000,
            "credit_impulse": {"us": -0.5, "cn": -0.5},
        })
        assert result["credit_modifier"] is not None
        assert result["credit_modifier"]["multiplier"] == 1.5
        assert result["credit_modifier"]["label"] == "both_decelerating"

    def test_credit_impulse_one_decelerating(self):
        result = calculate_hedge_budget({
            "temperature": 50,
            "portfolio_value_usd": 10_000_000,
            "credit_impulse": {"us": -0.5, "cn": 0.1},
        })
        assert result["credit_modifier"]["multiplier"] == 1.25
        assert result["credit_modifier"]["label"] == "one_decelerating"

    def test_credit_impulse_capped_at_ceiling(self):
        # Accumulation: target=0.75, ceiling=1.25, both_decel multiplier=1.5
        # 0.75 * 1.5 = 1.125 which is under ceiling 1.25
        result = calculate_hedge_budget({
            "temperature": 20,
            "portfolio_value_usd": 10_000_000,
            "credit_impulse": {"us": -0.5, "cn": -0.5},
        })
        assert result["target_pct"] <= result["ceiling_pct"]

    def test_missing_fields(self):
        result = calculate_hedge_budget({})
        assert "error" in result

    def test_non_numeric(self):
        result = calculate_hedge_budget({"temperature": "hot", "portfolio_value_usd": 10_000_000})
        assert "error" in result

    def test_floor_invariant_always_075(self):
        for temp in [10, 40, 65, 90]:
            result = calculate_hedge_budget({"temperature": temp, "portfolio_value_usd": 1_000_000})
            assert result["floor_pct"] == 0.75, f"Floor violated at temp={temp}"


# ---------------------------------------------------------------------------
# calculate_layer_exits
# ---------------------------------------------------------------------------

class TestCalculateLayerExits:
    @pytest.fixture
    def sample_positions(self):
        return [
            {
                "contract": "BTC-28MAR25-60000-P",
                "total_cost_usd": 5000,
                "quantity_btc": 10,
                "current_bid_btc": 0.02,
                "delta": -0.05,
            },
            {
                "contract": "BTC-28MAR25-40000-P",
                "total_cost_usd": 2000,
                "quantity_btc": 5,
                "current_bid_btc": 0.005,
                "delta": -0.01,
            },
        ]

    def test_happy_path(self, sample_positions):
        result = calculate_layer_exits({"positions": sample_positions, "btc_price": 95000})
        assert len(result["positions"]) == 2
        assert "summary" in result
        assert result["summary"]["total_value_usd"] > 0

    def test_layer_classification(self, sample_positions):
        result = calculate_layer_exits({"positions": sample_positions, "btc_price": 95000})
        assert result["positions"][0]["layer"] == "buffer"   # delta -0.05
        assert result["positions"][1]["layer"] == "disaster"  # delta -0.01

    def test_empty_positions(self):
        result = calculate_layer_exits({"positions": [], "btc_price": 95000})
        assert result["positions"] == []
        assert result["summary"]["total_value_usd"] == 0

    def test_missing_fields(self):
        result = calculate_layer_exits({})
        assert "error" in result

    def test_invalid_btc_price(self):
        result = calculate_layer_exits({"positions": [], "btc_price": -100})
        assert "error" in result

    def test_zero_cost_position(self):
        positions = [{
            "contract": "TEST",
            "total_cost_usd": 0,
            "quantity_btc": 1,
            "current_bid_btc": 0.01,
            "delta": -0.03,
        }]
        result = calculate_layer_exits({"positions": positions, "btc_price": 95000})
        assert result["positions"][0]["profit_multiple"] == 0


# ---------------------------------------------------------------------------
# calculate_geometric_mean_cagr
# ---------------------------------------------------------------------------

class TestCalculateGeometricMeanCAGR:
    def test_happy_path(self):
        result = calculate_geometric_mean_cagr({
            "normal_return": 0.15,
            "annual_cost": 0.02,
            "crash_magnitude": 0.50,
            "recovery_of_loss": 0.60,
            "cycle_length": 4,
        })
        assert "error" not in result
        assert result["hedged_cagr"] > result["unhedged_cagr"]
        assert result["is_positive_ev"] is True

    def test_zero_cost_no_benefit(self):
        result = calculate_geometric_mean_cagr({
            "normal_return": 0.15,
            "annual_cost": 0.0,
            "crash_magnitude": 0.50,
            "recovery_of_loss": 0.0,
            "cycle_length": 4,
        })
        # With zero cost and zero recovery, hedged == unhedged
        assert result["hedged_cagr"] == result["unhedged_cagr"]

    def test_cycle_length_less_than_1(self):
        result = calculate_geometric_mean_cagr({
            "normal_return": 0.15,
            "annual_cost": 0.02,
            "crash_magnitude": 0.50,
            "recovery_of_loss": 0.60,
            "cycle_length": 0,
        })
        assert "error" in result

    def test_missing_fields(self):
        result = calculate_geometric_mean_cagr({"normal_return": 0.15})
        assert "error" in result

    def test_non_numeric(self):
        result = calculate_geometric_mean_cagr({
            "normal_return": "high",
            "annual_cost": 0.02,
            "crash_magnitude": 0.50,
            "recovery_of_loss": 0.60,
            "cycle_length": 4,
        })
        assert "error" in result

    def test_improvement_field(self):
        result = calculate_geometric_mean_cagr({
            "normal_return": 0.15,
            "annual_cost": 0.02,
            "crash_magnitude": 0.50,
            "recovery_of_loss": 0.60,
            "cycle_length": 4,
        })
        expected_improvement = result["hedged_cagr"] - result["unhedged_cagr"]
        assert result["improvement"] == pytest.approx(expected_improvement, abs=1e-6)

    def test_assumptions_echoed(self):
        result = calculate_geometric_mean_cagr({
            "normal_return": 0.15,
            "annual_cost": 0.02,
            "crash_magnitude": 0.50,
            "recovery_of_loss": 0.60,
            "cycle_length": 4,
        })
        assert result["assumptions"]["normal_return"] == 0.15
        assert result["assumptions"]["cycle_length"] == 4


# ---------------------------------------------------------------------------
# calculate_hedge_coverage
# ---------------------------------------------------------------------------

class TestCalculateHedgeCoverage:
    @pytest.fixture
    def sample_coverage_input(self):
        return {
            "positions": [
                {
                    "quantity_btc": 10,
                    "total_cost_usd": 15000,
                    "strike_usd": 50000,
                    "expiry_date": "2026-06-30",
                },
                {
                    "quantity_btc": 5,
                    "total_cost_usd": 5000,
                    "strike_usd": 40000,
                    "expiry_date": "2026-09-30",
                },
            ],
            "total_btc_holdings": 35,
            "btc_price": 95000,
        }

    def test_happy_path(self, sample_coverage_input):
        result = calculate_hedge_coverage(sample_coverage_input)
        assert "error" not in result
        assert result["total_btc_hedged"] == 15
        assert result["coverage_pct"] == pytest.approx(42.86, abs=0.01)
        assert result["position_count"] == 2

    def test_health_score_range(self, sample_coverage_input):
        result = calculate_hedge_coverage(sample_coverage_input)
        assert 0 <= result["health_score"] <= 100

    def test_crash_payoff_calculation(self, sample_coverage_input):
        result = calculate_hedge_coverage(sample_coverage_input)
        # At 50% crash (price=47500): strike 50000 > 47500, payoff = (50000-47500)*10 = 25000
        # Strike 40000 < 47500, payoff = 0
        assert result["crash_payoff_at_50pct"] == 25000.0

    def test_missing_fields(self):
        result = calculate_hedge_coverage({})
        assert "error" in result

    def test_zero_btc_holdings(self):
        result = calculate_hedge_coverage({
            "positions": [],
            "total_btc_holdings": 0,
            "btc_price": 95000,
        })
        assert "error" in result

    @patch.object(hedge_engine, "datetime")
    def test_expiry_tracking(self, mock_dt, sample_coverage_input):
        mock_dt.now.return_value = datetime(2026, 3, 18, tzinfo=timezone.utc)
        mock_dt.strptime = datetime.strptime
        result = calculate_hedge_coverage(sample_coverage_input)
        assert result["nearest_expiry"] == "2026-06-30"
        assert result["days_to_nearest_expiry"] == 104

    def test_no_expiry_dates(self):
        result = calculate_hedge_coverage({
            "positions": [{"quantity_btc": 10, "total_cost_usd": 5000, "strike_usd": 50000}],
            "total_btc_holdings": 35,
            "btc_price": 95000,
        })
        assert result["days_to_nearest_expiry"] is None


# ---------------------------------------------------------------------------
# calculate_collar_recommendation
# ---------------------------------------------------------------------------

class TestCalculateCollarRecommendation:
    def test_no_trigger(self):
        result = calculate_collar_recommendation({
            "budget_status": "within_budget",
            "annualized_cost_pct": 1.5,
            "ceiling_pct": 2.25,
            "temperature": 60,
        })
        assert result["should_use_collar"] is False
        assert result["trigger"] == "none"

    def test_budget_breach_trigger(self):
        result = calculate_collar_recommendation({
            "budget_status": "over_budget",
            "annualized_cost_pct": 3.0,
            "ceiling_pct": 2.25,
            "temperature": 60,
        })
        assert result["should_use_collar"] is True
        assert result["trigger"] == "budget_breach"
        assert result["warning"] is not None

    def test_hot_market_trigger(self):
        result = calculate_collar_recommendation({
            "budget_status": "within_budget",
            "annualized_cost_pct": 1.0,
            "ceiling_pct": 2.25,
            "temperature": 85,
            "realized_vol": 50,
            "implied_vol": 80,
        })
        assert result["should_use_collar"] is True
        assert result["trigger"] == "hot_market"

    def test_hot_market_overrides_budget_breach(self):
        result = calculate_collar_recommendation({
            "budget_status": "over_budget",
            "annualized_cost_pct": 3.0,
            "ceiling_pct": 2.25,
            "temperature": 85,
            "realized_vol": 50,
            "implied_vol": 80,
        })
        # hot_market overrides budget_breach
        assert result["trigger"] == "hot_market"

    def test_missing_fields(self):
        result = calculate_collar_recommendation({})
        assert "error" in result

    def test_call_strike_guidance_temperature_tiers(self):
        # temp > 95
        r = calculate_collar_recommendation({
            "budget_status": "ok", "annualized_cost_pct": 1, "ceiling_pct": 2, "temperature": 96
        })
        assert r["call_strike_guidance"]["target_delta"] == 25

        # temp > 80
        r = calculate_collar_recommendation({
            "budget_status": "ok", "annualized_cost_pct": 1, "ceiling_pct": 2, "temperature": 85
        })
        assert r["call_strike_guidance"]["target_delta"] == 15

        # temp <= 80
        r = calculate_collar_recommendation({
            "budget_status": "ok", "annualized_cost_pct": 1, "ceiling_pct": 2, "temperature": 50
        })
        assert r["call_strike_guidance"]["target_delta"] == 10


# ---------------------------------------------------------------------------
# calculate_cagr_sensitivity
# ---------------------------------------------------------------------------

class TestCalculateCAGRSensitivity:
    def test_happy_path(self):
        result = calculate_cagr_sensitivity({
            "annual_cost": 0.02,
            "recovery_of_loss": 0.60,
        })
        assert "rows" in result
        # Default: 4 frequencies x 3 returns = 12 scenarios
        assert result["total_scenarios"] == 12

    def test_custom_frequencies(self):
        result = calculate_cagr_sensitivity({
            "annual_cost": 0.02,
            "recovery_of_loss": 0.60,
            "crash_frequencies": [3, 5],
            "normal_returns": [0.10, 0.20],
        })
        assert result["total_scenarios"] == 4

    def test_missing_fields(self):
        result = calculate_cagr_sensitivity({})
        assert "error" in result

    def test_positive_ev_count(self):
        result = calculate_cagr_sensitivity({
            "annual_cost": 0.02,
            "recovery_of_loss": 0.60,
        })
        assert result["positive_ev_count"] >= 0
        assert result["positive_ev_count"] <= result["total_scenarios"]


# ---------------------------------------------------------------------------
# calculate_hedge_ratio
# ---------------------------------------------------------------------------

class TestCalculateHedgeRatio:
    def test_extreme_fear(self):
        result = calculate_hedge_ratio({"temperature": 20})
        assert result["recommended_ratio"] == 1.0
        assert result["temperature_zone"] == "Extreme Fear"

    def test_fear(self):
        result = calculate_hedge_ratio({"temperature": 40})
        assert result["recommended_ratio"] == 0.85

    def test_neutral(self):
        result = calculate_hedge_ratio({"temperature": 55})
        assert result["recommended_ratio"] == 0.70

    def test_caution(self):
        result = calculate_hedge_ratio({"temperature": 70})
        assert result["recommended_ratio"] == 0.50

    def test_extreme_greed(self):
        result = calculate_hedge_ratio({"temperature": 90})
        assert result["recommended_ratio"] == 0.35
        assert result["temperature_zone"] == "Extreme Greed"

    def test_action_increase(self):
        result = calculate_hedge_ratio({"temperature": 20, "current_hedge_ratio": 0.50})
        assert result["action"] == "increase"

    def test_action_decrease(self):
        result = calculate_hedge_ratio({"temperature": 90, "current_hedge_ratio": 0.80})
        assert result["action"] == "decrease"

    def test_action_maintain(self):
        result = calculate_hedge_ratio({"temperature": 55, "current_hedge_ratio": 0.68})
        assert result["action"] == "maintain"

    def test_action_review_no_current(self):
        result = calculate_hedge_ratio({"temperature": 50})
        assert result["action"] == "review"

    def test_missing_temperature(self):
        result = calculate_hedge_ratio({})
        assert "error" in result

    def test_non_numeric(self):
        result = calculate_hedge_ratio({"temperature": "warm"})
        assert "error" in result


# ---------------------------------------------------------------------------
# calculate_geometric_breakeven
# ---------------------------------------------------------------------------

class TestCalculateGeometricBreakeven:
    def test_happy_path(self):
        result = calculate_geometric_breakeven({
            "annual_cost": 0.02,
            "recovery_of_loss": 0.60,
        })
        assert result["break_even_years"] is not None
        assert result["break_even_years"] > 0
        assert result["annual_probability"] is not None

    def test_zero_cost(self):
        result = calculate_geometric_breakeven({
            "annual_cost": 0,
            "recovery_of_loss": 0.60,
        })
        assert result["break_even_years"] == 1
        assert result["annual_probability"] == 100.0

    def test_missing_fields(self):
        result = calculate_geometric_breakeven({})
        assert "error" in result

    def test_custom_crash_magnitude(self):
        result = calculate_geometric_breakeven({
            "annual_cost": 0.02,
            "recovery_of_loss": 0.60,
            "crash_magnitude": 0.75,
            "normal_return": 0.20,
        })
        assert result["break_even_years"] is not None
