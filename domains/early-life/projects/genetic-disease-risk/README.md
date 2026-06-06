# Genetic Disease Risk (Early Life)

**Domain:** Early Life
**Status:** scaffold
**Prediction type:** Risk assessment for heritable and de novo genetic conditions present from birth, derived from newborn screening and parental genetic data.

## What This Predicts

- Risk of autosomal recessive conditions (based on carrier status of both parents)
- Detection support for conditions included in newborn screening panels
- De novo variant flagging in whole-genome newborn sequencing
- Childhood-onset disease risk (versus adult-onset, which is covered in [health/genetic-risk](../../health/projects/genetic-risk/))

## Target Conditions

- Cystic fibrosis, SMA, PKU (classic newborn screening conditions)
- Sickle cell disease and hemoglobinopathies
- SCID (severe combined immunodeficiency)
- Hearing loss (GJB2, GJB6 variants)
- Congenital hypothyroidism
- Fragile X syndrome
- Childhood cancer predisposition syndromes (TP53, RB1, APC)

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Parental carrier screening results | genetic test | optimal |
| Newborn screening results | clinical (Guthrie card) | if available |
| Newborn whole genome / exome sequence | genetic test | optimal |
| Parental ethnicity | self-report | yes (prior probability) |
| Family history of genetic conditions | self-report | yes |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Condition risk (per condition) | categorical | at-risk / carrier / not at risk |
| Carrier status (per condition, per parent) | binary | |
| De novo variant flags | list | pathogenic/likely pathogenic variants |
| Recommended specialist referrals | list | based on findings |
| Genetic counseling recommendation | binary | yes/no based on findings |

## Data Sources

- ClinVar — variant classifications
- OMIM (Online Mendelian Inheritance in Man)
- gnomAD — population carrier frequencies
- ACMG newborn screening uniform panel
- Published newborn sequencing study data

## Self-Correction

- **Accuracy metric:** Concordance with clinical genetic diagnosis; false negative rate for actionable variants
- **Ground truth:** clinical genetic testing outcomes for flagged individuals
- **Retraining trigger:** false negative rate for actionable variants > 2%

## Refresh Frequency

- Genetic data: one-time assessment at birth
- ClinVar / variant classification updates: quarterly (new classifications may change risk)

## Ethical Considerations

- Genetic counseling must be offered alongside any significant finding
- Variants of Uncertain Significance (VUS) must be clearly differentiated from pathogenic variants
- Incidental findings policy must be established and disclosed before testing
- Carrier status has implications for extended family members — counseling support needed
- Children cannot consent — parental decision framework must be clear
