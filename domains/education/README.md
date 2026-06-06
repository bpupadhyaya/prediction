# Education Domain

Predictions about learning trajectories, academic outcomes, and the educational paths most likely to lead to individual fulfillment and career success.

## Domain Goals

- Identify learning needs and disabilities early, enabling timely intervention
- Predict academic trajectories to help students and families make informed decisions
- Match individuals to educational paths aligned with their strengths
- Reduce inequality in access to educational guidance

## Projects

| Project | Prediction Focus | Status |
|---------|-----------------|--------|
| [academic-performance](projects/academic-performance/) | Future grades, graduation probability, academic trajectory | scaffold |
| [learning-disability](projects/learning-disability/) | Early detection of dyslexia, ADHD, dyscalculia, and other learning differences | scaffold |
| [career-aptitude](projects/career-aptitude/) | Career paths most aligned with individual strengths and interests | scaffold |
| [college-admission](projects/college-admission/) | College admission probability by institution and program | scaffold |

## Research Focus

See [research/](research/) for:
- Literature on educational outcome prediction
- Open educational datasets (PISA, NAEP, longitudinal studies)
- Ethical analysis of algorithmic college admissions and tracking
- Accuracy benchmarks vs. counselor assessments and standardized testing

## Development Focus

See [development/](development/) for:
- Educational data collection and anonymization pipelines
- Early-warning model implementations
- Skill and aptitude assessment frameworks
- Integration with learning management system APIs

## Data Sources (Catalog)

- PISA (Programme for International Student Assessment)
- NAEP (National Assessment of Educational Progress)
- IPEDS (U.S. postsecondary education data)
- OECD Education at a Glance
- National Longitudinal Survey of Youth
- Common Core alignment datasets
- O*NET (occupational data for career aptitude)

## Ethical Considerations

- Educational predictions can become self-fulfilling — labeling a child as "low potential" affects teacher behavior and student self-image
- Predictions must be used to open doors, not close them
- Algorithmic sorting by academic potential has a history of encoding racial and socioeconomic bias
- All models must be tested for disparate impact across demographic groups
- Learning disability detection must lead to support, never to exclusion or reduced expectations

## Refresh Frequency

| Prediction Type | Suggested Refresh |
|-----------------|------------------|
| Academic performance | Per semester |
| Learning disability risk | Annually in early years; on-demand later |
| Career aptitude | Annually through secondary school |
| College admission | Annually in secondary school |

## Aggregation

Education domain predictions feed into:
- [Finance](../finance/) — educational path affects income trajectory
- [Social & Behavioral](../social-behavioral/) — educational outcomes affect social mobility
- [Collective Intelligence](../../collective-intelligence/)
