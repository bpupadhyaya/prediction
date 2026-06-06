# [Project Name]

**Domain:** [parent domain]
**Status:** scaffold | research | development | evaluation | production
**Prediction type:** [one sentence describing what this project predicts]

---

## What This Predicts

[2-3 sentences describing the specific prediction. What is the output? What inputs does it use? Who is the intended beneficiary?]

## Why This Matters

[1-2 sentences on the real-world impact of having this prediction available.]

## Inputs

| Input | Type | Source | Required |
|-------|------|--------|----------|
| Age | numeric | self-report | yes |
| ... | ... | ... | ... |

## Output

| Output | Type | Range | Interpretation |
|--------|------|-------|---------------|
| Risk score | float | 0.0–1.0 | probability of event within window |
| Confidence interval | range | — | 95% CI |
| Risk tier | categorical | low/medium/high | actionable grouping |
| Prediction window | duration | — | e.g., "within 10 years" |

## Data Sources

- [Source 1] — [what it provides, license, update frequency]
- [Source 2] — [what it provides, license, update frequency]

## Research Questions

1. [Key open question this project needs to answer before building]
2. [What existing models are most relevant?]
3. [What are the known accuracy limitations?]

See [research/](research/) for literature reviews and data source evaluations.

## Development Approach

[Brief description of planned model type and implementation approach]

See [development/](development/) for implementation details.

## Self-Correction Mechanism

- **Accuracy metric:** [e.g., AUC-ROC, Brier score, calibration error]
- **Ground truth source:** [how will we know if the prediction was correct?]
- **Retraining trigger:** [e.g., AUC drops below 0.75 on validation set]
- **Accuracy history:** stored in `development/accuracy_log.json`

## Refresh Frequency

- **Initial estimate:** [e.g., quarterly]
- **AI-determined adjustment:** the project's monitoring agent adjusts this based on accuracy drift and data source update rates

## Ethical Considerations

- [Key ethical risk 1]
- [Key ethical risk 2]
- [How predictions should and should not be used]

## Status Log

| Date | Status | Notes |
|------|--------|-------|
| YYYY-MM-DD | scaffold | initial setup |

## Contributing

See [../../CONTRIBUTING.md](../../CONTRIBUTING.md). For this project specifically:
- [Any specific contribution guidance]
