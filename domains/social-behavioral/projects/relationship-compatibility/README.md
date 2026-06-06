# Relationship Compatibility

**Domain:** Social & Behavioral
**Status:** scaffold
**Prediction type:** Long-term relationship stability and satisfaction prediction, based on compatibility dimensions validated by relationship science.

## What This Predicts

- Predicted relationship stability (probability of lasting 5+ years)
- Compatibility score across key dimensions (values, personality, communication style)
- Predicted sources of conflict based on profile differences
- Predicted relationship satisfaction trajectory

## Why This Matters

Relationship dissolution is among the highest-impact life events affecting health, finance, and wellbeing. Research shows several compatibility dimensions have strong predictive validity that people rarely assess systematically.

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Big Five personality scores (both partners) | assessment | yes |
| Core values alignment | assessment | yes |
| Communication style | assessment | yes |
| Conflict resolution style | assessment | yes |
| Relationship goals (children, geography, lifestyle) | self-report | yes |
| Attachment style | assessment | optional |
| Gottman Four Horsemen indicators | assessment | optional |
| Relationship length and history | self-report | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Compatibility score | 0.0–1.0 | overall compatibility |
| Dimension breakdown | radar chart | strengths and gaps |
| 5-year stability probability | percentage | |
| Predicted conflict areas | list | specific dimensions |
| Growth areas | list | where investment has highest return |

## Data Sources

- Gottman Institute research data
- NLSY (relationship and marriage outcomes)
- Add Health (longitudinal relationship data)
- Relationship science literature (meta-analyses)

## Self-Correction

- **Accuracy metric:** Predicted vs. actual relationship stability at 5-year follow-up; calibration
- **Ground truth:** longitudinal relationship outcome surveys
- **Retraining trigger:** AUC < 0.65 for stability prediction

## Refresh Frequency

- Initial assessment: before or early in a relationship
- Reassessment: annually or after major relationship events

## Ethical Considerations

- Results are advisory — never tell a couple they "should" or "shouldn't" stay together
- Predictions are probabilistic, not deterministic — many low-scoring couples thrive; many high-scoring couples don't
- Must not be used in legal proceedings (divorce, custody)
- Cultural variation in what constitutes healthy relationships must be respected and modeled
- LGBTQ+ relationships must be fully supported without heteronormative assumptions
