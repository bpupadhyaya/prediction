# Career Aptitude

**Domain:** Education
**Status:** scaffold
**Prediction type:** Career paths most aligned with an individual's measured strengths, interests, and values — with realistic outcome predictions for each path.

## What This Predicts

- Top career paths ranked by predicted fit (interest + ability + values alignment)
- Expected job market demand for each path (5–10 year horizon)
- Income range for each path by geography and education level
- Required education and skill development for each path
- Probability of career satisfaction for each path

## Why This Matters

Career mismatch is one of the largest sources of adult dissatisfaction. Many people choose careers based on family pressure, prestige, or limited information. Objective aptitude prediction, combined with realistic outcome data, can dramatically improve career decision quality.

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Interest inventory (Holland types) | assessment | yes |
| Cognitive ability profile | assessment | yes |
| Values assessment (income vs. meaning vs. flexibility) | assessment | yes |
| Academic strengths by subject | grades / self-report | yes |
| Personality traits (Big Five) | assessment | optional |
| Preferred work environment | self-report | optional |
| Geographic preferences | self-report | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Top 10 career matches | ranked list | with fit scores |
| For each career: job market outlook | categorical | growing/stable/declining |
| For each career: income range | dollar range | by geography and experience level |
| For each career: education pathway | text | recommended route |
| Skills gap analysis | list | what to develop for top matches |

## Data Sources

- O*NET (Occupational Information Network) — skills, tasks, values by occupation
- BLS Occupational Outlook Handbook — demand and salary data
- RIASEC (Holland) assessment research
- ACT and College Board career interest research
- LinkedIn Economic Graph (aggregated, where available)

## Self-Correction

- **Accuracy metric:** Career satisfaction correlation at 5-year follow-up; job retention rate
- **Ground truth:** longitudinal career outcome surveys
- **Retraining trigger:** predicted satisfaction vs. reported satisfaction correlation < 0.40
- **Note:** long feedback loop — initial accuracy assessments will take years

## Refresh Frequency

- Individual assessment: annually through secondary school; on major career transition
- Labor market data: annually
- Salary data: quarterly

## Ethical Considerations

- Must not encode gender, racial, or socioeconomic stereotypes in career matching
- Must explicitly surface paths that match aptitude regardless of historical demographic representation
- Income predictions must account for documented wage gaps for the same role
- Predictions must present ranges and uncertainty, not point estimates presented as certainty
