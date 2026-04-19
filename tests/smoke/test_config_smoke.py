from core.config.loaders import load_experiment_registry, load_metric_registry, load_policy_registry, load_scenario_registry


def test_config_registries_validate() -> None:
    metrics = load_metric_registry("configs/metrics")
    policies = load_policy_registry("configs/policies")
    experiments = load_experiment_registry(
        "configs/experiments",
        metric_registry=metrics,
        policy_registry=policies,
    )

    assert len(metrics) == 8
    assert len(policies) == 1
    assert len(experiments) == 1


def test_scenario_registry_validate() -> None:
    scenarios = load_scenario_registry("configs/scenarios")

    assert len(scenarios) == 7

