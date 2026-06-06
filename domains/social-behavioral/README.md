# Social & Behavioral Domain

Predictions about interpersonal relationships, behavioral health, social trajectories, and the human factors that shape quality of life.

## Domain Goals

- Help individuals understand behavioral risk factors before crises develop
- Support relationship health through predictive insights
- Identify social mobility barriers and opportunities early
- Approach sensitive behavioral predictions with rigor and care

## Projects

| Project | Prediction Focus | Status |
|---------|-----------------|--------|
| [relationship-compatibility](projects/relationship-compatibility/) | Long-term relationship stability and compatibility prediction | scaffold |
| [addiction-risk](projects/addiction-risk/) | Substance use disorder onset and relapse risk prediction | scaffold |
| [social-mobility](projects/social-mobility/) | Probability of upward economic and social mobility | scaffold |
| [mental-health-episodes](projects/mental-health-episodes/) | Prediction of acute mental health episodes (crisis events) | scaffold |

## Research Focus

See [research/](research/) for:
- Longitudinal behavioral studies and outcome datasets
- Relationship science research (Gottman, attachment theory, etc.)
- Addiction neuroscience and risk factor literature
- Social mobility research (Chetty et al., OECD mobility data)
- Ethical framework for sensitive behavioral predictions

## Development Focus

See [development/](development/) for:
- Survey and self-report data collection frameworks
- Behavioral sequence modeling approaches
- Crisis prediction model implementations
- Privacy-preserving ML techniques for sensitive behavioral data

## Data Sources (Catalog)

- Add Health (National Longitudinal Study of Adolescent to Adult Health)
- NLSY (National Longitudinal Survey of Youth)
- SAMHSA (Substance Abuse and Mental Health Services Administration) data
- Opportunity Insights mobility data
- General Social Survey (GSS)
- World Values Survey
- NSDUH (National Survey on Drug Use and Health)

## Ethical Considerations

This is the highest-sensitivity domain in the project:

- **Relationship predictions** must never be used coercively; they are advisory only
- **Addiction risk** predictions must be coupled with support resources, never used for punishment or exclusion
- **Mental health episode** predictions carry life-safety implications — false positives and negatives both have serious consequences; human review protocols must be defined
- **Social mobility** predictions must distinguish between individual factors and structural barriers — never imply that low mobility probability is a personal failing
- Behavioral predictions are among the most prone to encoding racial, class, and cultural bias — all models require demographic fairness audits

## Refresh Frequency

| Prediction Type | Suggested Refresh |
|-----------------|------------------|
| Relationship compatibility | On relationship milestones or annually |
| Addiction risk | Monthly for at-risk individuals |
| Social mobility | Annually |
| Mental health episodes | Weekly for at-risk individuals |

## Aggregation

Social & Behavioral predictions feed into:
- [Health](../health/) — behavioral factors are major health determinants
- [Finance](../finance/) — social mobility directly affects economic outcomes
- [Collective Intelligence](../../collective-intelligence/)
