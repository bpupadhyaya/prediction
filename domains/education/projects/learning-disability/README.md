# Learning Disability Detection

**Domain:** Education
**Status:** scaffold
**Prediction type:** Early detection of learning differences and disabilities (dyslexia, ADHD, dyscalculia, dysgraphia, auditory processing disorder) to enable timely support.

## What This Predicts

Probability that an individual shows patterns consistent with specific learning disabilities, flagging for professional evaluation. This is a screening tool — not a diagnosis.

## Why This Matters

Average time from first signs to formal diagnosis of dyslexia: 2.5 years. During that time, children often internalize a narrative of "being bad at school" rather than "having a specific learning difference that can be supported." Early detection changes life trajectories.

## Target Conditions

- Dyslexia (reading/phonological processing)
- ADHD (attention and executive function)
- Dyscalculia (numerical processing)
- Dysgraphia (writing and motor coordination)
- Auditory Processing Disorder

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Reading fluency score | assessment | yes |
| Phonological awareness score | assessment | yes |
| Math fluency score | assessment | yes |
| Age / grade level | self-report | yes |
| Attention and focus observations | parent/teacher report | yes |
| Writing sample quality | assessment | optional |
| Family history of learning disability | self-report | optional |
| Vision and hearing screening results | clinical | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Screen positive / negative | binary | refers for professional evaluation |
| Probability per condition | 0.0–1.0 | screening confidence |
| Recommended evaluation type | text | e.g., neuropsychological testing |
| Suggested accommodations | list | interim support while awaiting evaluation |

## Data Sources

- ABCD Study (neurodevelopmental data)
- NIH Toolbox (cognitive assessment data)
- Dyslexia research consortium datasets
- ADHD longitudinal studies
- IDA (International Dyslexia Association) assessment norms

## Self-Correction

- **Accuracy metric:** Sensitivity and specificity vs. formal neuropsychological diagnosis
- **Ground truth:** formal evaluation outcomes for referred individuals
- **Retraining trigger:** sensitivity < 0.80 for any condition

## Refresh Frequency

- Screening: annually through primary school; on teacher or parent concern at any time
- Model retraining: annually with new outcome data

## Ethical Considerations

- This is a screening tool — must never be presented as a diagnosis
- A positive screen is a referral recommendation, not a label
- Schools must not use screening results to reduce resources or track students
- Socioeconomic factors that mimic learning disability symptoms (inadequate schooling, language barriers) must be explicitly considered
- Results belong to the child / family — not to schools or insurers
