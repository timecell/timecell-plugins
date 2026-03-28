#!/usr/bin/env python3
"""
Hedge Engine — timecell-bitcoin plugin

Pure Python engine functions for downside insurance computation.
Ports battle-tested hedge logic from fo-web TypeScript engine.

All functions: stateless, JSON-in JSON-out, no database access, no API calls.

Usage:
    python3 scripts/hedge-engine.py calculateHedgeBudget '{"temperature": 72, "portfolio_value_usd": 9500000}'
    python3 scripts/hedge-engine.py calculateLayerExits '{"positions": [...], "btc_price": 95000}'
"""

import json
import math
import sys
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Tier 1 — Essential
# ---------------------------------------------------------------------------

def calculate_hedge_budget(input_data: dict) -> dict:
    """Cycle-based premium budget target from temperature + portfolio size."""
    temperature = input_data.get("temperature")
    portfolio_value_usd = input_data.get("portfolio_value_usd")

    if temperature is None or portfolio_value_usd is None:
        return {"error": "Missing required fields: temperature, portfolio_value_usd"}

    if not isinstance(temperature, (int, float)) or not isinstance(portfolio_value_usd, (int, float)):
        return {"error": "temperature and portfolio_value_usd must be numbers"}

    credit_impulse = input_data.get("credit_impulse")

    # Temperature thresholds (validated against 11 of 15 BTC crash months 2013-2024)
    if temperature < 35:
        cycle_phase = "accumulation"
        target_pct = 0.75
        ceiling_pct = 1.25
        otm_min, otm_max = 50, 60
        tenor_min, tenor_max = 180, 365
    elif temperature < 60:
        cycle_phase = "mid_cycle"
        target_pct = 1.25
        ceiling_pct = 1.75
        otm_min, otm_max = 45, 50
        tenor_min, tenor_max = 90, 180
    elif temperature < 75:
        cycle_phase = "late_cycle"
        target_pct = 1.75
        ceiling_pct = 2.25
        otm_min, otm_max = 30, 40
        tenor_min, tenor_max = 60, 180
    else:
        cycle_phase = "overheated"
        target_pct = 2.25
        ceiling_pct = 2.25
        otm_min, otm_max = 20, 30
        tenor_min, tenor_max = 30, 90

    # Credit impulse modifier
    credit_modifier = None
    if credit_impulse and isinstance(credit_impulse, dict):
        us_val = credit_impulse.get("us")
        cn_val = credit_impulse.get("cn")

        us_decel = isinstance(us_val, (int, float)) and us_val < -0.3
        cn_decel = isinstance(cn_val, (int, float)) and cn_val < -0.3
        us_accel = isinstance(us_val, (int, float)) and us_val > 0.3
        cn_accel = isinstance(cn_val, (int, float)) and cn_val > 0.3

        if us_decel and cn_decel:
            multiplier = 1.5
            label = "both_decelerating"
        elif us_decel or cn_decel:
            multiplier = 1.25
            label = "one_decelerating"
        elif us_accel and cn_accel:
            multiplier = 1.0
            label = "both_accelerating"
        else:
            multiplier = 1.0
            label = "neutral"

        if multiplier != 1.0:
            adjusted = target_pct * multiplier
            target_pct = min(adjusted, ceiling_pct)
            credit_modifier = {
                "multiplier": multiplier,
                "label": label,
                "adjusted_target": target_pct,
            }

    # CRITICAL INVARIANT: floor can NEVER be below 0.75%
    floor_pct = 0.75

    target_usd = target_pct * portfolio_value_usd / 100

    return {
        "cycle_phase": cycle_phase,
        "target_pct": target_pct,
        "floor_pct": floor_pct,
        "ceiling_pct": ceiling_pct,
        "target_usd": target_usd,
        "recommended_otm": {"min": otm_min, "max": otm_max},
        "recommended_tenor_days": {"min": tenor_min, "max": tenor_max},
        "credit_modifier": credit_modifier,
    }


def _classify_layer(delta: float | None) -> str:
    """Classify a position into buffer/core/disaster by delta."""
    if delta is None:
        return "core"  # Default when delta unknown
    abs_delta = abs(delta)
    if abs_delta >= 0.04:
        return "buffer"
    elif abs_delta >= 0.015:
        return "core"
    else:
        return "disaster"


def _exit_recommendation(layer: str, profit_multiple: float) -> tuple:
    """Return (recommendation, exit_pct, reasoning) for a position."""
    if layer == "buffer":
        if profit_multiple >= 3:
            return "full_exit", 100, "Buffer layer at 3x+ — full exit, recycle to fund program"
        elif profit_multiple >= 2:
            return "partial_exit_50", 50, "Buffer layer at 2x — sell 50%, let rest ride"
        else:
            return "hold", 0, "Buffer layer below exit threshold"
    elif layer == "core":
        if profit_multiple >= 8:
            return "full_exit", 100, "Core layer at 8x+ — full exit"
        elif profit_multiple >= 5:
            return "partial_exit_50", 50, "Core layer at 5x — sell 50%"
        elif profit_multiple >= 3:
            return "partial_exit_25", 25, "Core layer at 3x — take 25% profits"
        else:
            return "hold", 0, "Core layer below exit threshold"
    else:  # disaster
        if profit_multiple >= 20:
            return "partial_exit_majority", 75, "Disaster layer at 20x+ — exit 75%, redeploy to buy BTC"
        elif profit_multiple >= 10:
            return "partial_exit_25", 25, "Disaster layer at 10x — sell 25%, preserve explosive upside"
        elif profit_multiple >= 5:
            return "recycle_premium", 0, "Disaster layer at 5x — recycle original premium only"
        else:
            return "hold", 0, "Disaster layer below exit threshold"


def calculate_layer_exits(input_data: dict) -> dict:
    """Layer-specific exit guidance for each hedge position."""
    positions = input_data.get("positions")
    btc_price = input_data.get("btc_price")

    if positions is None or btc_price is None:
        return {"error": "Missing required fields: positions, btc_price"}

    if not isinstance(positions, list):
        return {"error": "positions must be a list"}

    if not isinstance(btc_price, (int, float)) or btc_price <= 0:
        return {"error": "btc_price must be a positive number"}

    result_positions = []
    total_value_usd = 0
    total_pnl_usd = 0
    positions_with_action = 0

    for pos in positions:
        contract = pos.get("contract", "unknown")
        total_cost_usd = pos.get("total_cost_usd", 0)
        quantity_btc = pos.get("quantity_btc", 0)
        current_bid_btc = pos.get("current_bid_btc")
        delta = pos.get("delta")

        layer = _classify_layer(delta)

        if current_bid_btc is not None and total_cost_usd > 0:
            current_value = quantity_btc * current_bid_btc * btc_price
            profit_multiple = current_value / total_cost_usd
            profit_loss_usd = current_value - total_cost_usd
        else:
            current_value = 0
            profit_multiple = 0
            profit_loss_usd = 0

        recommendation, exit_pct, reasoning = _exit_recommendation(layer, profit_multiple)

        if recommendation != "hold":
            positions_with_action += 1

        total_value_usd += current_value
        total_pnl_usd += profit_loss_usd

        result_positions.append({
            "contract": contract,
            "layer": layer,
            "profit_multiple": round(profit_multiple, 2),
            "profit_loss_usd": round(profit_loss_usd, 2),
            "recommendation": recommendation,
            "exit_pct": exit_pct,
            "reasoning": reasoning,
        })

    return {
        "positions": result_positions,
        "summary": {
            "total_value_usd": round(total_value_usd, 2),
            "total_pnl_usd": round(total_pnl_usd, 2),
            "positions_with_action": positions_with_action,
        },
    }


def calculate_geometric_mean_cagr(input_data: dict) -> dict:
    """Compare hedged vs unhedged CAGR over a crash cycle.

    Formula: CAGR = ((1 + r - c)^(n-1) * (1 - crash + recovery))^(1/n) - 1
    Must match fo-web calculateGeometricMeanCAGR exactly.
    """
    normal_return = input_data.get("normal_return")
    annual_cost = input_data.get("annual_cost")
    crash_magnitude = input_data.get("crash_magnitude")
    recovery_of_loss = input_data.get("recovery_of_loss")
    cycle_length = input_data.get("cycle_length")

    if any(v is None for v in [normal_return, annual_cost, crash_magnitude, recovery_of_loss, cycle_length]):
        return {"error": "Missing required fields: normal_return, annual_cost, crash_magnitude, recovery_of_loss, cycle_length"}

    for name, val in [("normal_return", normal_return), ("annual_cost", annual_cost),
                      ("crash_magnitude", crash_magnitude), ("recovery_of_loss", recovery_of_loss),
                      ("cycle_length", cycle_length)]:
        if not isinstance(val, (int, float)):
            return {"error": f"{name} must be a number"}

    if cycle_length < 1:
        return {"error": "cycle_length must be >= 1"}

    recovery_value = recovery_of_loss * crash_magnitude

    # Unhedged: (n-1) normal years then one crash year
    unhedged_growth = (1 + normal_return) ** (cycle_length - 1) * (1 - crash_magnitude)
    if unhedged_growth <= 0:
        return {"error": "Unhedged growth is non-positive — check inputs"}
    unhedged_cagr = unhedged_growth ** (1 / cycle_length) - 1

    # Hedged: (n-1) normal years minus cost, then crash year with recovery
    hedged_growth = (1 + normal_return - annual_cost) ** (cycle_length - 1) * (1 - crash_magnitude + recovery_value)
    if hedged_growth <= 0:
        return {"error": "Hedged growth is non-positive — check inputs"}
    hedged_cagr = hedged_growth ** (1 / cycle_length) - 1

    if math.isnan(unhedged_cagr) or math.isnan(hedged_cagr):
        return {"error": "CAGR calculation produced NaN — verify position data"}

    improvement = hedged_cagr - unhedged_cagr

    return {
        "unhedged_cagr": round(unhedged_cagr, 6),
        "hedged_cagr": round(hedged_cagr, 6),
        "improvement": round(improvement, 6),
        "is_positive_ev": improvement > 0,
        "assumptions": {
            "normal_return": normal_return,
            "crash_magnitude": crash_magnitude,
            "cycle_length": int(cycle_length),
            "annual_cost": annual_cost,
            "recovery_pct": recovery_of_loss,
        },
    }


def calculate_hedge_coverage(input_data: dict) -> dict:
    """Coverage metrics and health score from active hedge positions."""
    positions = input_data.get("positions")
    total_btc_holdings = input_data.get("total_btc_holdings")
    btc_price = input_data.get("btc_price")

    if positions is None or total_btc_holdings is None or btc_price is None:
        return {"error": "Missing required fields: positions, total_btc_holdings, btc_price"}

    if not isinstance(positions, list):
        return {"error": "positions must be a list"}

    if total_btc_holdings <= 0:
        return {"error": "total_btc_holdings must be positive"}

    total_btc_hedged = 0
    total_premium_spent_usd = 0
    weighted_strike_sum = 0
    position_count = 0
    nearest_expiry = None
    days_to_nearest_expiry = None
    crash_payoff_at_50pct = 0

    now = datetime.now(timezone.utc)

    for pos in positions:
        qty = pos.get("quantity_btc", 0)
        cost = pos.get("total_cost_usd", 0)
        strike = pos.get("strike_usd", 0)
        expiry_str = pos.get("expiry_date")

        total_btc_hedged += qty
        total_premium_spent_usd += cost
        weighted_strike_sum += strike * qty
        position_count += 1

        if expiry_str:
            try:
                expiry_dt = datetime.strptime(expiry_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                days_to_exp = (expiry_dt - now).days
                if days_to_nearest_expiry is None or days_to_exp < days_to_nearest_expiry:
                    days_to_nearest_expiry = days_to_exp
                    nearest_expiry = expiry_str
            except ValueError:
                pass

        # Crash payoff at 50%: if BTC drops 50%, how much does the put pay?
        crash_price = btc_price * 0.5
        if strike > crash_price:
            payoff = (strike - crash_price) * qty
            crash_payoff_at_50pct += payoff

    coverage_pct = (total_btc_hedged / total_btc_holdings) * 100

    avg_strike_usd = weighted_strike_sum / total_btc_hedged if total_btc_hedged > 0 else 0
    avg_strike_pct_of_spot = (avg_strike_usd / btc_price * 100) if btc_price > 0 else 0

    # Recovery of loss at 50% crash
    portfolio_loss = total_btc_holdings * btc_price * 0.5
    recovery_of_loss = crash_payoff_at_50pct / portfolio_loss if portfolio_loss > 0 else 0

    # Health score (0-100)
    # Coverage weight 40%
    if coverage_pct >= 60:
        coverage_score = 40
    elif coverage_pct >= 50:
        coverage_score = 35
    elif coverage_pct >= 40:
        coverage_score = 25
    elif coverage_pct >= 25:
        coverage_score = 15
    else:
        coverage_score = 5

    # Expiry weight 35%
    if days_to_nearest_expiry is not None:
        if days_to_nearest_expiry >= 90:
            expiry_score = 35
        elif days_to_nearest_expiry >= 60:
            expiry_score = 30
        elif days_to_nearest_expiry >= 30:
            expiry_score = 20
        elif days_to_nearest_expiry >= 14:
            expiry_score = 10
        else:
            expiry_score = 0
    else:
        expiry_score = 0

    # Strike weight 25%: optimal is 40-65% of spot
    if avg_strike_pct_of_spot > 0:
        if 40 <= avg_strike_pct_of_spot <= 65:
            strike_score = 25
        elif 30 <= avg_strike_pct_of_spot <= 75:
            strike_score = 20
        else:
            strike_score = 10
    else:
        strike_score = 10

    health_score = coverage_score + expiry_score + strike_score

    # Health factors
    health_factors = []
    if coverage_pct < 25:
        health_factors.append("Low coverage — under 25% of holdings hedged")
    if days_to_nearest_expiry is not None and days_to_nearest_expiry < 30:
        health_factors.append(f"Nearest expiry in {days_to_nearest_expiry} days — consider rolling")
    if avg_strike_pct_of_spot > 75:
        health_factors.append("Average strike near spot — may not provide tail protection")
    if coverage_pct >= 50:
        health_factors.append("Good coverage level")
    if days_to_nearest_expiry is not None and days_to_nearest_expiry >= 90:
        health_factors.append("Healthy time to expiry")

    return {
        "total_btc_hedged": round(total_btc_hedged, 8),
        "coverage_pct": round(coverage_pct, 2),
        "total_premium_spent_usd": round(total_premium_spent_usd, 2),
        "avg_strike_usd": round(avg_strike_usd, 2),
        "avg_strike_pct_of_spot": round(avg_strike_pct_of_spot, 2),
        "position_count": position_count,
        "nearest_expiry": nearest_expiry,
        "days_to_nearest_expiry": days_to_nearest_expiry,
        "health_score": health_score,
        "health_factors": health_factors,
        "crash_payoff_at_50pct": round(crash_payoff_at_50pct, 2),
        "recovery_of_loss": round(recovery_of_loss, 6),
    }


# ---------------------------------------------------------------------------
# Tier 2 — Important
# ---------------------------------------------------------------------------

def calculate_collar_recommendation(input_data: dict) -> dict:
    """Whether to use collar strategy to finance put premium."""
    budget_status = input_data.get("budget_status")
    annualized_cost_pct = input_data.get("annualized_cost_pct")
    ceiling_pct = input_data.get("ceiling_pct")
    temperature = input_data.get("temperature")

    if any(v is None for v in [budget_status, annualized_cost_pct, ceiling_pct, temperature]):
        return {"error": "Missing required fields: budget_status, annualized_cost_pct, ceiling_pct, temperature"}

    realized_vol = input_data.get("realized_vol")
    implied_vol = input_data.get("implied_vol")

    should_use_collar = False
    trigger = "none"
    reasoning = "Default is outright puts — no collar needed."
    warning = None

    # Trigger 1: Budget breach
    if annualized_cost_pct > ceiling_pct:
        should_use_collar = True
        trigger = "budget_breach"
        reasoning = f"Annual cost {annualized_cost_pct}% exceeds ceiling {ceiling_pct}% — collar recommended to offset premium."
        warning = "Collar caps BTC upside. Only use when premium cost is unsustainable."

    # Trigger 2: Hot market (overrides budget breach if both apply)
    if temperature > 80 and realized_vol is not None and implied_vol is not None and implied_vol > 0:
        rv_iv_ratio = realized_vol / implied_vol
        if rv_iv_ratio < 0.75:
            should_use_collar = True
            trigger = "hot_market"
            reasoning = (
                f"Temperature {temperature} > 80 and RV/IV ratio {rv_iv_ratio:.2f} < 0.75 — "
                "implied vol premium is rich, sell calls to finance puts."
            )
            warning = "Collar caps BTC upside. Acceptable in overheated conditions where upside is limited."

    # Call strike guidance by temperature
    if temperature > 95:
        target_delta = 25
        target_otm = {"min": 30, "max": 50}
    elif temperature > 80:
        target_delta = 15  # midpoint of 15-20
        target_otm = {"min": 50, "max": 75}
    else:
        target_delta = 10
        target_otm = {"min": 70, "max": 100}

    return {
        "should_use_collar": should_use_collar,
        "trigger": trigger,
        "reasoning": reasoning,
        "call_strike_guidance": {
            "target_delta": target_delta,
            "target_otm": target_otm,
        },
        "warning": warning,
    }


def calculate_cagr_sensitivity(input_data: dict) -> dict:
    """Sensitivity matrix varying crash frequency and normal return."""
    annual_cost = input_data.get("annual_cost")
    recovery_of_loss = input_data.get("recovery_of_loss")

    if annual_cost is None or recovery_of_loss is None:
        return {"error": "Missing required fields: annual_cost, recovery_of_loss"}

    crash_magnitude = input_data.get("crash_magnitude", 0.50)
    crash_frequencies = input_data.get("crash_frequencies", [3, 4, 5, 6])
    normal_returns = input_data.get("normal_returns", [0.10, 0.15, 0.25])

    rows = []
    positive_ev_count = 0

    for freq in crash_frequencies:
        for ret in normal_returns:
            cagr_result = calculate_geometric_mean_cagr({
                "normal_return": ret,
                "annual_cost": annual_cost,
                "crash_magnitude": crash_magnitude,
                "recovery_of_loss": recovery_of_loss,
                "cycle_length": freq,
            })

            if "error" in cagr_result:
                continue

            improvement = cagr_result["improvement"]
            if improvement > 0:
                positive_ev_count += 1

            rows.append({
                "crash_frequency": freq,
                "normal_return": ret,
                "unhedged_cagr": cagr_result["unhedged_cagr"],
                "hedged_cagr": cagr_result["hedged_cagr"],
                "improvement": improvement,
            })

    return {
        "rows": rows,
        "positive_ev_count": positive_ev_count,
        "total_scenarios": len(rows),
        "current_recovery": recovery_of_loss,
        "current_cost": annual_cost,
    }


# ---------------------------------------------------------------------------
# Tier 3 — Nice-to-have
# ---------------------------------------------------------------------------

def calculate_hedge_ratio(input_data: dict) -> dict:
    """Recommended hedge ratio based on temperature zone."""
    temperature = input_data.get("temperature")

    if temperature is None:
        return {"error": "Missing required field: temperature"}

    if not isinstance(temperature, (int, float)):
        return {"error": "temperature must be a number"}

    current_hedge_ratio = input_data.get("current_hedge_ratio")

    # Temperature -> ratio mapping
    if temperature < 30:
        recommended = 1.0
        zone = "Extreme Fear"
    elif temperature < 50:
        recommended = 0.85
        zone = "Fear"
    elif temperature < 65:
        recommended = 0.70
        zone = "Neutral"
    elif temperature < 80:
        recommended = 0.50
        zone = "Caution"
    else:
        recommended = 0.35
        zone = "Extreme Greed"

    # Determine action
    if current_hedge_ratio is not None:
        diff = recommended - current_hedge_ratio
        if abs(diff) < 0.05:
            action = "maintain"
        elif diff > 0:
            action = "increase"
        else:
            action = "decrease"
    else:
        action = "review"

    label = f"{int(recommended * 100)}%"

    reasoning = f"Temperature {temperature}/100 ({zone}). Framework recommends {label} hedge ratio."
    if action == "increase":
        reasoning += " Current ratio below target — consider adding protection."
    elif action == "decrease":
        reasoning += " Current ratio above target — consider reducing or exiting."
    elif action == "maintain":
        reasoning += " Current ratio aligned with target."

    return {
        "recommended_ratio": recommended,
        "ratio_label": label,
        "temperature_zone": zone,
        "action": action,
        "reasoning": reasoning,
    }


def calculate_geometric_breakeven(input_data: dict) -> dict:
    """Max cycle length where hedge still improves CAGR."""
    annual_cost = input_data.get("annual_cost")
    recovery_of_loss = input_data.get("recovery_of_loss")

    if annual_cost is None or recovery_of_loss is None:
        return {"error": "Missing required fields: annual_cost, recovery_of_loss"}

    crash_magnitude = input_data.get("crash_magnitude", 0.50)
    normal_return = input_data.get("normal_return", 0.15)

    if annual_cost <= 0:
        return {"break_even_years": 1, "annual_probability": 100.0}

    # Binary search: positive at short cycles, negative at long
    lo = 2.0
    hi = 200.0

    at_min = calculate_geometric_mean_cagr({
        "normal_return": normal_return,
        "annual_cost": annual_cost,
        "crash_magnitude": crash_magnitude,
        "recovery_of_loss": recovery_of_loss,
        "cycle_length": lo,
    })
    if "error" in at_min or at_min["improvement"] <= 0:
        return {"break_even_years": None, "annual_probability": None}

    at_max = calculate_geometric_mean_cagr({
        "normal_return": normal_return,
        "annual_cost": annual_cost,
        "crash_magnitude": crash_magnitude,
        "recovery_of_loss": recovery_of_loss,
        "cycle_length": hi,
    })
    if "error" not in at_max and at_max["improvement"] > 0:
        return {"break_even_years": 200, "annual_probability": 0.5}

    for _ in range(50):
        mid = (lo + hi) / 2
        result = calculate_geometric_mean_cagr({
            "normal_return": normal_return,
            "annual_cost": annual_cost,
            "crash_magnitude": crash_magnitude,
            "recovery_of_loss": recovery_of_loss,
            "cycle_length": mid,
        })
        if "error" in result:
            hi = mid
            continue
        if result["improvement"] > 0:
            lo = mid
        else:
            hi = mid

    break_even_years = round(lo)
    annual_probability = (1 / break_even_years) * 100 if break_even_years > 0 else None

    return {
        "break_even_years": break_even_years,
        "annual_probability": round(annual_probability, 2) if annual_probability is not None else None,
    }


# ---------------------------------------------------------------------------
# CLI dispatch map
# ---------------------------------------------------------------------------

FUNCTIONS = {
    "calculateHedgeBudget": calculate_hedge_budget,
    "calculateLayerExits": calculate_layer_exits,
    "calculateGeometricMeanCAGR": calculate_geometric_mean_cagr,
    "calculateHedgeCoverage": calculate_hedge_coverage,
    "calculateCollarRecommendation": calculate_collar_recommendation,
    "calculateCAGRSensitivity": calculate_cagr_sensitivity,
    "calculateHedgeRatio": calculate_hedge_ratio,
    "calculateGeometricBreakeven": calculate_geometric_breakeven,
}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": f"Usage: python3 hedge-engine.py <function> '<json_args>'. Available: {', '.join(FUNCTIONS.keys())}"}))
        sys.exit(1)

    func_name = sys.argv[1]
    args_json = sys.argv[2]

    if func_name not in FUNCTIONS:
        print(json.dumps({"error": f"Unknown function '{func_name}'. Available: {', '.join(FUNCTIONS.keys())}"}))
        sys.exit(1)

    try:
        input_data = json.loads(args_json)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    result = FUNCTIONS[func_name](input_data)
    print(json.dumps(result, indent=2))
