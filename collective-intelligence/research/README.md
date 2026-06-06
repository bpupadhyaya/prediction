# Collective Intelligence — Research

## Purpose

Research the theoretical and empirical foundations for cross-domain prediction synthesis. This work informs the architecture of the collective intelligence layer.

## Active Research Areas

### Cross-Domain Interaction Literature
- [ ] Systematic review: health-finance interaction (financial stress → health outcomes)
- [ ] Systematic review: social determinants of health (all social domains → health)
- [ ] Literature on multi-output prediction models
- [ ] Research on cascading risk prediction

### Architecture Research
- [ ] Survey of multi-task learning approaches for correlated prediction targets
- [ ] Temporal alignment methods for predictions with different time horizons
- [ ] Ensemble approaches for aggregating predictions with different confidence levels
- [ ] Causal inference approaches for modeling domain interactions (not just correlation)

### Evaluation Framework
- [ ] How do we measure the value added by collective intelligence vs. individual domains?
- [ ] What accuracy metric applies to holistic life trajectory prediction?
- [ ] How do we validate a 20-year life trajectory prediction?

## Key Research Questions

1. Which domain interactions have the strongest empirical evidence?
2. What is the right temporal resolution for cross-domain synthesis?
3. How do we handle predictions with very different accuracy levels without the least-accurate domain degrading overall collective accuracy?
4. What are the privacy implications of combining health + finance + behavioral predictions for a single individual?

## Contributing

Add literature reviews as `review_<topic>.md` files. Follow the format in [../../../templates/](../../../templates/).
