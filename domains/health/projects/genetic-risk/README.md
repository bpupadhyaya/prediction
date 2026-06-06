# Genetic Risk

**Domain:** Health
**Status:** scaffold
**Prediction type:** Disease and trait risk derived from genetic markers, including polygenic risk scores for complex diseases and monogenic variant identification.

## What This Predicts

Two classes of genetic predictions:
1. **Monogenic risk** — high-penetrance single-gene variants (BRCA1/2 for breast cancer, APOE4 for Alzheimer's, etc.)
2. **Polygenic risk scores (PRS)** — combined effect of thousands of common variants on complex disease risk

## Why This Matters

Genetic risk is present at birth and unchangeable — but knowing it enables targeted surveillance, preventive action, and informed reproductive decisions. Most people have never had genetic risk assessment.

## Key Inputs

| Input | Source | Required |
|-------|--------|----------|
| Genome or SNP array data | genetic test (23andMe, AncestryDNA, WGS) | yes |
| Ethnicity / ancestry | genetic inference or self-report | yes |
| Family history | self-report | optional (validates genetic findings) |

## Output

| Output | Type | Interpretation |
|--------|------|---------------|
| Polygenic risk score per disease | percentile | relative risk vs. population |
| Monogenic variant flags | categorical | pathogenic / likely pathogenic / VUS / benign |
| Ancestral PRS calibration | note | accuracy varies by ancestry |
| Recommended action | text | surveillance, specialist referral, etc. |

## Target Conditions

- Cardiovascular disease (CAD PRS)
- Type 2 diabetes
- Breast and ovarian cancer (BRCA1/2)
- Colorectal cancer
- Alzheimer's disease (APOE, GWAS PRS)
- Schizophrenia and bipolar disorder
- Celiac disease
- Hereditary hemochromatosis

## Data Sources

- ClinVar — variant pathogenicity classifications
- gnomAD — population allele frequencies
- PGS Catalog — published polygenic risk scores
- OpenSNP — user-contributed genotype data
- GWAS Catalog — genome-wide association study results
- UK Biobank — phenotype-genotype associations

## Self-Correction

- **Accuracy metric:** Odds ratio validation in independent cohorts; calibration by ancestry group
- **Ground truth:** disease incidence in follow-up cohorts stratified by PRS
- **Retraining trigger:** calibration slope deviates > 0.1 from 1.0 for any ancestry group
- **Note:** genetic data itself doesn't change, but PRS weights improve as new GWAS studies are published

## Refresh Frequency

- Monogenic variant calls: once (variants don't change; ClinVar classifications updated annually)
- PRS models: annually as new GWAS studies improve score weights
- Ancestry-specific calibration: as new reference populations become available

## Ethical Considerations

- **Ancestry bias:** most GWAS studies are in European populations — PRS accuracy is substantially lower for African, Asian, and other ancestries; this must be prominently disclosed
- Genetic counseling resources must accompany any high-risk result
- Implications for biological relatives who did not consent
- Legal protections against genetic discrimination vary by country — users must be informed
- Raw genetic data is among the most sensitive personal data that exists — security standards are paramount
