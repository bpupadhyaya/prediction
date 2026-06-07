# Health Domain

Predictions across the full spectrum of physical and mental health, from individual disease risk to population-level health outcomes.

## Domain Goals

- Provide individuals with personalized risk predictions for major diseases and conditions
- Enable early intervention by predicting health events before they occur
- Bridge the gap between clinical research and public access
- Operate without requiring expensive diagnostics or clinical visits

## Projects

| Project | Prediction Focus | Status |
|---------|-----------------|--------|
| [disease-risk](projects/disease-risk/) | Risk of developing major diseases (cancer, diabetes, cardiovascular, etc.) | scaffold |
| [life-expectancy](projects/life-expectancy/) | Estimated lifespan based on lifestyle, genetics, and environment | scaffold |
| [genetic-risk](projects/genetic-risk/) | Heritable disease and trait risk from genetic markers | scaffold |
| [mental-health](projects/mental-health/) | Depression, anxiety, PTSD, bipolar, schizophrenia onset risk | scaffold |
| [pharmacogenomics](projects/pharmacogenomics/) | Drug response and adverse reaction prediction by genetic profile | scaffold |
| [fertility](projects/fertility/) | Reproductive health and fertility outcome prediction | scaffold |

## Data Sources (Catalog)

- NIH All of Us Research Program
- UK Biobank
- WHO Global Health Observatory
- CDC BRFSS (Behavioral Risk Factor Surveillance System)
- OpenSNP (genetic data)
- PubMed / bioRxiv (research literature)
- ClinVar (genetic variant database)
- PharmGKB (pharmacogenomics)

## Ethical Considerations

Health predictions carry significant responsibility:
- Predictions are probabilistic, not deterministic — must be communicated as risk, not fate
- Genetic predictions must address implications for family members who did not consent
- No prediction should be used to deny insurance, employment, or services
- Mental health predictions are particularly sensitive — stigma and self-fulfilling effects must be considered
- Geographic and demographic bias in training data must be documented and addressed

## Refresh Frequency

| Prediction Type | Suggested Refresh |
|-----------------|------------------|
| Disease risk (lifestyle-based) | Quarterly or on lifestyle change |
| Genetic risk | Once (genetics don't change) |
| Mental health risk | Monthly |
| Life expectancy | Annually |
| Pharmacogenomics | Once per drug introduction |
| Fertility | Monthly |

AI agents in each project will adjust these based on observed accuracy drift.

## Aggregation

Health domain predictions feed into:
- [Collective Intelligence](../../collective-intelligence/) — combined with finance/social for holistic life modeling
- [AGI Framework](../../agi-framework/) — as a core reasoning domain
