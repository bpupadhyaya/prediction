# Infrastructure — Research

## Purpose

Research the technical approaches for building scalable, privacy-preserving infrastructure for a globally distributed prediction project.

## Active Research Areas

### Privacy-Preserving ML
- [ ] Federated learning survey — can we train domain models without centralizing data?
- [ ] Differential privacy practical applications — what privacy budgets are appropriate?
- [ ] Secure multi-party computation for sensitive health predictions
- [ ] Synthetic data generation for training without real PII

### Scalability
- [ ] Distributed data collection at global scale
- [ ] Open source model serving options (cost, latency, scalability)
- [ ] Edge deployment for predictions without internet connectivity

### Data Quality
- [ ] Automated data quality monitoring approaches
- [ ] Cross-source validation (how to detect when sources disagree)
- [ ] Missing data imputation at scale

### Contribution Infrastructure
- [ ] How do open-source ML projects handle model contribution and integration?
- [ ] Version control systems for ML models and datasets (DVC, MLflow, etc.)
- [ ] CI/CD pipelines for ML systems

## Key Research Questions

1. Can we build a prediction system that never needs to see raw user data?
2. What is the minimum infrastructure needed for a single contributor to add a new project?
3. How do we ensure data source reliability at global scale?
4. What are the compute cost implications of global-scale prediction serving?
