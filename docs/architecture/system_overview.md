# GrowthLab System Overview

GrowthLab is organized as a strict pipeline:

1. YAML contracts define the experiment, metrics, policy, and scenario.
2. The simulator converts the scenario into canonical parquet tables.
3. The analysis engine estimates the configured metric effects.
4. The trust layer validates the read before policy logic runs.
5. The decision engine applies policy stages in order.
6. Reporting exports compact artifacts for UI and review.
7. Streamlit reads those artifacts locally for demo and exploration.

## Artifact flow
```mermaid
flowchart LR
    subgraph Config["Config layer"]
        E["Experiment YAML"]
        M["Metric YAMLs"]
        P["Policy YAML"]
        S["Scenario YAML"]
    end

    subgraph Sim["Simulator"]
        G["Scenario runner"]
        T1["dim_experiments"]
        T2["dim_users"]
        F1["fact_assignments"]
        F2["fact_opportunities"]
        F3["fact_exposures"]
        F4["fact_user_day"]
        F5["fact_user_outcomes"]
        F6["fact_validation_truth"]
    end

    subgraph Analysis["Analysis engine"]
        A["Metric inference"]
        R["Compact analysis summary"]
    end

    subgraph Trust["Trust layer"]
        V["SRM / missingness / maturity / evaluability"]
        V2["Validation summary"]
    end

    subgraph Decision["Decision engine"]
        D["Guardrail / primary / business value / segment"]
        D2["Decision summary"]
    end

    subgraph Reporting["Reporting and UI"]
        X["JSON / CSV / Markdown bundles"]
        U["Streamlit UI"]
    end

    E --> G
    M --> G
    P --> G
    S --> G
    G --> T1 --> A
    G --> T2 --> A
    G --> F1 --> A
    G --> F2 --> A
    G --> F3 --> A
    G --> F4 --> A
    G --> F5 --> A
    G --> F6 --> A
    A --> R --> V
    F6 --> V
    V --> V2 --> D
    R --> D
    D --> D2 --> X --> U
```

## Design notes
- The simulator writes all canonical tables in the same order expected by the contracts.
- The analysis engine only consumes parquet and the metric registry.
- Trust checks are reusable by the validation harness and policy engine.
- The decision engine is config-driven and does not need to recompute statistics.
- The UI is a viewer over prepared artifacts, not a hidden source of business logic.

