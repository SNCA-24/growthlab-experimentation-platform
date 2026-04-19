from __future__ import annotations

import pandas as pd

from core.contracts import ScenarioContract

from ..generators._shared import serialize_json_value


def build_fact_validation_truth(scenario: ScenarioContract) -> pd.DataFrame:
    truth = scenario.validation_truth
    return pd.DataFrame(
        {
            "scenario_id": [scenario.scenario_id],
            "experiment_id": [scenario.experiment.experiment_id],
            "primary_metric_name": [truth.primary_metric_name],
            "true_primary_effect_value": [truth.true_primary_effect_value],
            "true_primary_effect_scale": [truth.true_primary_effect_scale.value],
            "primary_metric_direction": [truth.primary_metric_direction.value],
            "true_effect_by_segment_json": [serialize_json_value(truth.true_effect_by_segment_json)],
            "true_guardrail_impact_json": [serialize_json_value(truth.true_guardrail_impact_json)],
            "expected_srm_flag": [truth.expected_srm_flag],
            "expected_missing_exposure_pattern": [truth.expected_missing_exposure_pattern],
            "expected_peeking_risk": [truth.expected_peeking_risk],
            "expected_recommendation": [truth.expected_recommendation.value],
        }
    )
