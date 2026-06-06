# Collective Intelligence

The Collective Intelligence layer synthesizes predictions from all eight domains into an integrated, holistic model of human life. It is the bridge between individual prediction projects and the AGI framework.

## What It Does

Each domain produces its own predictions. Collective Intelligence does three things that individual domains cannot:

1. **Cross-domain synthesis** — health predictions inform financial ones; early-life predictions inform aging ones; social predictions inform health ones. The interactions between domains are where the most valuable insights emerge.

2. **Holistic life modeling** — a single integrated view of an individual's predicted trajectory across all domains simultaneously, to reveal compounding effects and cascading risks.

3. **Gap identification** — surfaces areas of human life not yet covered by any project, driving the roadmap for new projects.

## Architecture

```
Domain Outputs
    ↓
┌───────────────────────────────────┐
│     Cross-Domain Feature Layer    │
│  (align temporal windows, units,  │
│   confidence intervals)           │
└───────────────┬───────────────────┘
                ↓
┌───────────────────────────────────┐
│   Interaction Modeling Layer      │
│  (health ↔ finance, social ↔      │
│   health, education ↔ finance)    │
└───────────────┬───────────────────┘
                ↓
┌───────────────────────────────────┐
│   Holistic Life Model             │
│  (integrated trajectory,          │
│   cascading risk identification)  │
└───────────────┬───────────────────┘
                ↓
┌───────────────────────────────────┐
│   AGI Framework Input             │
└───────────────────────────────────┘
```

## Known Domain Interactions (Initial Research Questions)

| Domain A | Domain B | Known Interaction |
|----------|----------|------------------|
| Health | Finance | Financial stress → worse health outcomes; poor health → financial distress |
| Education | Finance | Educational attainment → income trajectory |
| Social/Behavioral | Health | Addiction, mental health → chronic disease risk |
| Early Life | Aging | Early-life genetic risk → aging disease risk |
| Macro/Population | Finance | Recession → individual financial distress |
| Safety/Environment | Health | Pollution, disaster → disease burden |
| Social/Behavioral | Finance | Social mobility → income trajectory |
| Mental Health | All | Mental health underlies function across every domain |

## Research Focus

See [research/](research/) for:
- Cross-domain interaction research literature
- Multi-output prediction model architectures
- Temporal alignment across domains with different refresh frequencies
- Collective prediction accuracy vs. single-domain accuracy studies

## Development Focus

See [development/](development/) for:
- Domain output normalization layer
- Cross-domain feature engineering
- Integrated trajectory modeling
- Holistic life dashboard specification

## Status

Collective Intelligence cannot be built until sufficient domain-level predictions are operational. Current milestone: at least 2 projects in each domain reaching "evaluation" status.

## Contributing

Collective Intelligence is the highest-leverage contribution point — it multiplies the value of all domain-level work. Priority contributions:
- Research on cross-domain interaction literature
- Architecture proposals for multi-domain synthesis
- Development of the feature alignment layer
