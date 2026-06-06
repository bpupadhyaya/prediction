# Cognitive Indicators

**Domain:** Early Life
**Status:** scaffold
**Prediction type:** Early cognitive development indicators to support optimal learning environment design — not IQ labeling, but identification of cognitive strengths and areas needing enrichment.

## What This Predicts

- Cognitive domain strengths and developmental pace (language, spatial, working memory, processing speed)
- Learning style indicators (visual, auditory, kinesthetic, reading/writing)
- Risk of later academic difficulty without additional support
- Optimal enrichment areas given current developmental profile

## Critical Scope Constraint

This project explicitly does NOT:
- Predict or report IQ or intelligence as a fixed number
- Label children as "gifted" or "slow" in ways that create expectations
- Make predictions intended for anything other than enrichment and support

The goal is: *what does this child need right now to develop well?* Not: *how smart will this child be?*

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Age | self-report | yes |
| Language development milestones | parent report | yes |
| Play patterns (how child engages with objects, others) | parent report | yes |
| Memory and attention observations | parent report | yes |
| Problem-solving approach observations | parent report | optional |
| Formal cognitive screening (e.g., Bayley, Mullen) | clinical | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Cognitive domain profile | radar chart | strengths by domain |
| Learning environment recommendations | list | specific enrichment activities |
| Development pace (per domain) | categorical | typical/accelerated/needs support |
| Recommended early intervention | binary | whether EI referral is warranted |

## Data Sources

- Bayley Scales normative data
- Mullen Scales normative data
- NICHD Study of Early Child Care (cognitive outcomes)
- ABCD Study (early cognitive development)
- Perry Preschool Project (longitudinal)
- Head Start Impact Study

## Self-Correction

- **Accuracy metric:** Correlation of early cognitive profile with age-8 academic readiness
- **Ground truth:** longitudinal academic outcome tracking
- **Retraining trigger:** cross-domain profile correlation with outcomes < 0.40
- **Note:** long feedback loop — initial validation will take years

## Refresh Frequency

- Every 3 months in first 3 years
- Every 6 months from ages 3–8

## Ethical Considerations

- This is the highest ethics-sensitivity project in the Early Life domain
- Under no circumstances should outputs be used to reduce investment in a child's education
- Must be explicitly framed as a support tool, not an evaluation tool
- Access to cognitive enrichment activities is deeply unequal — predictions must acknowledge this and point to low-cost options
- Cultural bias in cognitive assessments is well-documented — normative data and tools must be culturally adapted
- Results belong to parents and child — must never be shared with schools, insurers, or government without explicit consent
