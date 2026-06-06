# College Admission

**Domain:** Education
**Status:** scaffold
**Prediction type:** Probability of admission to specific colleges and programs, and predicted fit between student profile and institutional characteristics.

## What This Predicts

- Admission probability by institution (safety / match / reach classification with actual probabilities)
- Financial aid probability and estimated award ranges
- Predicted academic fit (will the student thrive academically at this institution?)
- Predicted social fit (values, culture, environment alignment)

## Why This Matters

College admissions processes are opaque. Wealthy families pay thousands for private counselors who have institutional knowledge that should be universally accessible. This project democratizes that information.

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| GPA (weighted / unweighted) | self-report | yes |
| Course rigor (AP, IB, honors) | self-report | yes |
| Standardized test scores (SAT/ACT) | test records | yes (if applicable) |
| Extracurricular activities | self-report | yes |
| State of residence | self-report | yes |
| First-generation college student status | self-report | optional |
| Intended major | self-report | optional |
| Demonstrated interest indicators | self-report | optional |
| Legacy status | self-report | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Admission probability | percentage | per institution |
| Financial need probability | percentage | likelihood of need-based aid |
| Academic fit score | 0.0–1.0 | rigor match |
| Similar student outcomes | aggregate | what students like this typically achieve |
| Application strategy | text | which schools to prioritize and why |

## Data Sources

- IPEDS (Integrated Postsecondary Education Data System)
- Common Data Sets (published by institutions)
- College Board historical admission data
- NCES (National Center for Education Statistics)
- College Scorecard (graduation rates, earnings outcomes)

## Self-Correction

- **Accuracy metric:** Predicted vs. actual admission outcomes; calibration by institution
- **Ground truth:** user-reported admission decisions
- **Retraining trigger:** calibration error > 0.10 for major institution categories

## Refresh Frequency

- Institution data: annually (Common Data Sets published each fall)
- Individual prediction: on academic record updates

## Ethical Considerations

- Must not encode institutional bias against first-generation, low-income, or underrepresented students
- Transparency about what the model does and does not know (e.g., essays cannot be modeled)
- Should highlight financial aid opportunities, not just prestige-ranked outcomes
- Must not be used to discourage students from applying to reach schools
