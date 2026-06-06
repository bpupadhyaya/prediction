# Addiction Risk

**Domain:** Social & Behavioral
**Status:** scaffold
**Prediction type:** Substance use disorder onset risk and relapse probability for individuals in recovery.

## What This Predicts

Two use cases:
1. **Onset risk** — probability of developing substance use disorder (alcohol, opioids, stimulants, cannabis)
2. **Relapse risk** — probability of relapse within 30/90 days for individuals in recovery

## Why This Matters

Addiction affects 1 in 8 adults globally. Risk factors are well-characterized; identifying high-risk individuals before disorder onset enables preventive intervention. For those in recovery, relapse prediction enables proactive support at the right moment.

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Family history of substance use disorder | self-report | yes |
| Current substance use patterns | self-report | yes |
| Stress level and life events | self-report | yes |
| Mental health status (depression, anxiety, PTSD) | self-report | yes |
| Age of first substance use | self-report | yes |
| Social environment (peers, household) | self-report | optional |
| Trauma history | self-report | optional |
| Genetic risk markers (ADH1B, ALDH2, etc.) | genetic test | optional |
| Recovery duration (for relapse model) | self-report | if applicable |
| Cravings intensity (for relapse model) | self-report | if applicable |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Onset risk score | 0.0–1.0 | per substance class |
| Relapse probability (30-day) | percentage | for recovery model |
| Risk tier | categorical | low/medium/high |
| Key risk factors | ranked list | modifiable factors first |
| Support resources | list | treatment, hotlines, peer support |

## Data Sources

- NSDUH (National Survey on Drug Use and Health)
- NESARC-III (alcohol and drug use disorders survey)
- ABCD Study (adolescent substance use)
- SAMHSA treatment data
- Genetic addiction risk research (ADH1B, OPRM1 variants)

## Self-Correction

- **Accuracy metric:** AUC for disorder onset; sensitivity for relapse prediction
- **Ground truth:** longitudinal survey follow-up; treatment program outcomes
- **Retraining trigger:** AUC < 0.70 for onset; sensitivity < 0.75 for relapse

## Refresh Frequency

- Onset risk: quarterly for medium/high-risk individuals
- Relapse risk: weekly or daily during high-risk periods in recovery

## Ethical Considerations

- Results must always be accompanied by treatment and support resources
- Must never be used in legal or criminal justice settings
- Must not be used by employers or insurers
- Recovery is a non-linear process — relapse prediction must be framed as a support tool, not a failure assessment
- All results are confidential — privacy by design is non-negotiable
