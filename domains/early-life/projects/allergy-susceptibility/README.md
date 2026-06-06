# Allergy Susceptibility

**Domain:** Early Life
**Status:** scaffold
**Prediction type:** Risk prediction for food, environmental, and drug allergies in infants and children, to guide preventive exposure strategies and early testing.

## What This Predicts

- Risk of developing specific food allergies (peanut, tree nut, milk, egg, wheat, soy, fish, shellfish)
- Risk of environmental allergies (pollen, dust mite, pet dander, mold)
- Risk of drug hypersensitivity reactions
- Likelihood of outgrowing childhood food allergies

## Why This Matters

Food allergy incidence has doubled in 20 years. For conditions like peanut allergy, early tolerance introduction (guided by risk stratification) dramatically reduces allergy development. Most parents have no way to know their infant's risk before introduction.

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Parental allergy history | self-report | yes |
| Sibling allergy history | self-report | yes |
| Infant eczema severity | parent report | yes |
| Breastfeeding status | self-report | optional |
| Genetic data (HLA alleles, filaggrin variants) | genetic test | optional |
| Cord blood IgE (if available) | clinical | optional |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Food allergy risk (per allergen) | low/medium/high | |
| Recommended introduction strategy | text | based on LEAP trial evidence |
| Environmental allergy risk | low/medium/high | |
| Allergy testing recommendation | binary + type | whether and what to test |

## Data Sources

- LEAP trial data (Learning Early About Peanut Allergy)
- EAT trial data (Enquiring About Tolerance)
- CHILD Cohort Study (allergy development)
- DBPCFC (double-blind placebo-controlled food challenge) research data
- Published filaggrin / HLA allergy genetics studies
- NIAID food allergy guidelines

## Self-Correction

- **Accuracy metric:** Sensitivity and specificity for allergy development prediction vs. confirmed challenge outcomes
- **Ground truth:** oral food challenge results; allergy testing in high-risk infants
- **Retraining trigger:** sensitivity < 0.75 for high-risk allergens

## Refresh Frequency

- Initial assessment: at birth / in first weeks of life
- Reassessment: at 4 months and 6 months (key introduction windows)
- Annually through age 5 for environmental allergies

## Ethical Considerations

- Introduction recommendations have medical implications — must direct families to their pediatrician for high-risk profiles
- Must not create excessive anxiety that leads parents to unnecessarily delay allergen introduction (which itself increases allergy risk)
- Genetic testing access varies globally — the model must be useful without genetic data
