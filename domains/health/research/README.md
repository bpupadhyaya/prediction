# Health Domain — Research

## Purpose

This folder contains all research artifacts for the health domain: literature reviews, data source evaluations, ethical analyses, and accuracy benchmarks. Research here informs and justifies development decisions in [../development/](../development/).

## Active Research Areas

### Literature Reviews
- [ ] Systematic review of disease risk prediction models (Framingham, QRISK, PCE)
- [ ] Mental health onset prediction — state of the art
- [ ] Pharmacogenomics clinical utility evidence
- [ ] Life expectancy model accuracy across demographics

### Data Source Evaluation
- [ ] NIH All of Us — access requirements, coverage, update frequency
- [ ] UK Biobank — available phenotypes, genetic data access
- [ ] CDC BRFSS — geographic coverage, survey methodology
- [ ] OpenSNP — data quality assessment

### Ethical Analysis
- [ ] Genetic discrimination legal frameworks (GINA, EU regulations)
- [ ] Mental health prediction and stigma
- [ ] Algorithmic fairness in clinical risk tools
- [ ] Privacy-preserving approaches for health data (federated learning, differential privacy)

### Accuracy Benchmarks
- [ ] Calibration of existing cardiovascular risk tools
- [ ] Mental health prediction accuracy in literature
- [ ] Comparison of mortality prediction models

## Key References

*To be populated as literature reviews are completed.*

## Research Questions Driving This Domain

1. Can we build disease risk prediction that is as accurate as clinical tools, using only freely available data?
2. How much accuracy is lost when moving from genetic data to lifestyle + demographic proxies?
3. What is the minimum data requirement for a useful mental health risk prediction?
4. How do existing risk tools perform across different ethnicities and geographies?
5. What are the most important unmet prediction needs in global health?

## Contributing

Add literature reviews as markdown files in this folder. Use the naming convention `review_<topic>.md`. Document the scope, methodology, key findings, and implications for our development work.
