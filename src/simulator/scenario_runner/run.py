from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from core.config.loaders import load_scenario_contract
from core.contracts import ScenarioContract

from data.io.parquet_store import write_tables_to_parquet
from simulator.generators._shared import (
    build_filter_payload,
    build_target_population_rule,
)
from simulator.generators.assignments import generate_fact_assignments
from simulator.generators.exposures import generate_fact_exposures
from simulator.generators.opportunities import generate_fact_opportunities
from simulator.generators.user_day import generate_fact_user_day
from simulator.generators.user_outcomes import generate_fact_user_outcomes
from simulator.generators.users import generate_dim_users
from simulator.truth.build_truth import build_fact_validation_truth


@dataclass(slots=True)
class ScenarioRunResult:
    scenario: ScenarioContract
    tables: dict[str, pd.DataFrame]


def _build_dim_experiments(scenario: ScenarioContract) -> pd.DataFrame:
    experiment = scenario.experiment
    control_weight = next(variant.weight for variant in experiment.variants if variant.is_control)
    treatment_share_target = 1.0 - control_weight
    segment_policy_mode = (
        "pre_registered_segments_only" if experiment.pre_registered_groupby_columns else "global_only"
    )
    return pd.DataFrame(
        {
            "experiment_id": [experiment.experiment_id],
            "experiment_name": [experiment.experiment_name],
            "experiment_type": [experiment.experiment_type],
            "start_date": [experiment.assignment_start_ts_utc.date()],
            "end_date": [experiment.observation_end_ts_utc.date()],
            "primary_metric": [experiment.primary_metric],
            "analysis_mode": [experiment.analysis_mode.value],
            "primary_estimand": [experiment.primary_estimand.value],
            "target_population_rule": [build_target_population_rule(experiment.target_population_filters)],
            "randomization_unit": [experiment.randomization_unit.value],
            "treatment_share_target": [treatment_share_target],
            "decision_policy_id": [experiment.decision_policy_id],
            "segment_policy_mode": [segment_policy_mode],
            "pre_registered_groupby_columns": [list(experiment.pre_registered_groupby_columns)],
            "pre_registered_filters": [build_filter_payload(experiment.pre_registered_filters)],
            "secondary_metrics": [list(experiment.secondary_metrics)],
            "guardrail_metrics": [list(experiment.guardrail_metrics)],
            "notes": [experiment.notes],
        }
    )


def run_scenario(scenario_path: str | Path, output_dir: str | Path) -> ScenarioRunResult:
    scenario = load_scenario_contract(scenario_path)

    rng = np.random.default_rng(scenario.random_seed)

    tables: dict[str, pd.DataFrame] = {}
    tables["dim_experiments"] = _build_dim_experiments(scenario)
    tables["dim_users"] = generate_dim_users(scenario, rng)
    tables["fact_assignments"] = generate_fact_assignments(scenario, tables["dim_users"], rng)
    opportunity_state = generate_fact_opportunities(scenario, tables["dim_users"], tables["fact_assignments"], rng)
    tables["fact_opportunities"] = opportunity_state.table
    exposure_state = generate_fact_exposures(scenario, tables["fact_assignments"], opportunity_state, rng)
    tables["fact_exposures"] = exposure_state.table
    user_day_state = generate_fact_user_day(
        scenario,
        tables["dim_users"],
        tables["fact_assignments"],
        opportunity_state,
        exposure_state,
        rng,
    )
    tables["fact_user_day"] = user_day_state.table
    tables["fact_user_outcomes"] = generate_fact_user_outcomes(
        scenario,
        tables["dim_users"],
        tables["fact_assignments"],
        opportunity_state,
        exposure_state,
        user_day_state,
    )
    tables["fact_validation_truth"] = build_fact_validation_truth(scenario)

    write_tables_to_parquet(output_dir, tables)
    return ScenarioRunResult(scenario=scenario, tables=tables)
