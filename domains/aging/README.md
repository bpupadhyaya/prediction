# Aging Domain

Predictions about the trajectory of aging — physical, cognitive, and social — to enable dignified planning and early intervention in the later stages of human life.

## Domain Goals

- Enable individuals and families to plan for aging before crises force reactive decisions
- Predict cognitive and physical decline trajectories to inform care planning
- Reduce the burden of unanticipated late-life care costs
- Support aging in place by predicting when additional support will be needed

## Projects

| Project | Prediction Focus | Status |
|---------|-----------------|--------|
| [cognitive-decline](projects/cognitive-decline/) | Alzheimer's, dementia, and general cognitive decline trajectory | scaffold |
| [mobility-loss](projects/mobility-loss/) | Physical mobility decline and fall risk prediction | scaffold |
| [caregiver-dependency](projects/caregiver-dependency/) | Timeline to needing assisted living or caregiver support | scaffold |
| [end-of-life-costs](projects/end-of-life-costs/) | Estimated medical and care costs in final years of life | scaffold |

## Data Sources (Catalog)

- Health and Retirement Study (HRS) — University of Michigan
- ELSA (English Longitudinal Study of Ageing)
- SHARE (Survey of Health, Ageing and Retirement in Europe)
- ADNI (Alzheimer's Disease Neuroimaging Initiative)
- UK Biobank (aging-related phenotypes)
- CMS Medicare claims data (public use files)
- CDC Healthy Aging data
- BRFSS (Behavioral Risk Factor Surveillance System)

## Ethical Considerations

- Cognitive decline predictions are deeply personal — delivery must be handled with care and accompanied by counseling resources
- Predictions about dependency timelines must be used to support planning, never to pressure individuals into care arrangements against their will
- End-of-life cost predictions must be presented as planning tools, not as judgments about the value of extending care
- Aging predictions often reflect existing health disparities — racial and socioeconomic factors must be accounted for and explained
- Individuals have the right not to know their aging trajectory — opt-in only

## Refresh Frequency

| Prediction Type | Suggested Refresh |
|-----------------|------------------|
| Cognitive decline | Annually after age 60; semi-annually after 70 |
| Mobility loss | Annually; after any fall or injury |
| Caregiver dependency | Annually |
| End-of-life costs | Biannually |

## Aggregation

Aging domain predictions feed into:
- [Health](../health/) — aging is the primary driver of chronic disease
- [Finance](../finance/) — care costs are a major retirement financial risk
- [Collective Intelligence](../../collective-intelligence/)
