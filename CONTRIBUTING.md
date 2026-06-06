# Contributing

Welcome. This project is built by the world, for the world. Anyone can contribute — no geography, affiliation, credential, or experience level required.

## What You Can Contribute

### Research Contributions
- Literature reviews for a domain or project
- Data source identification (public datasets, APIs, open research databases)
- Ethical analysis of prediction approaches (bias, privacy, misuse potential)
- Comparative accuracy benchmarks against existing tools
- Domain expertise (medical, educational, financial, environmental knowledge)

### Development Contributions
- Data collection pipelines
- ML model implementations
- Prediction APIs
- Evaluation and accuracy-tracking frameworks
- Visualization and reporting tools
- Documentation

### New Projects
If you see a prediction type not yet covered, propose it as a new project under the relevant domain. Use the project template at [templates/PROJECT_TEMPLATE.md](templates/PROJECT_TEMPLATE.md).

### New Domains
If an entire prediction domain is missing, propose it as a new domain. Use the domain template at [templates/DOMAIN_TEMPLATE.md](templates/DOMAIN_TEMPLATE.md).

## Getting Started

1. Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the structure
2. Find a domain or project that interests you
3. Read the domain README and any relevant project READMEs
4. Check the research/ folder — is there a literature review needed?
5. Check the development/ folder — is there a data pipeline or model stub to build out?
6. Open an issue or submit a PR

## Standards

### For All Contributions
- Document your sources
- Note geographic and demographic coverage (who does this apply to? who is excluded?)
- Flag potential biases explicitly
- Do not fabricate data or results

### For Predictions
- Always report confidence intervals or uncertainty estimates
- Never claim higher accuracy than you can verify
- Document the populations your model was trained on
- Flag when a model should not be applied to certain groups

### For Data
- Only use data with clear licensing (open data, public domain, or explicit permission)
- Document data provenance (source, collection date, update frequency)
- Never include personally identifiable information (PII) in training data without explicit consent frameworks

### For Code
- Write readable code with clear interfaces
- Include tests for data pipeline and model evaluation steps
- Document how to reproduce your results

## Project Status Tags

Each project README uses a status tag:

| Status | Meaning |
|--------|---------|
| `scaffold` | Structure defined, no implementation yet |
| `research` | Active literature review and data source identification |
| `development` | Active software development |
| `evaluation` | Model trained, running accuracy evaluation |
| `production` | Deployed, generating predictions, in self-correction loop |

## On Proprietary Products

You may build proprietary products using this project's outputs. Attribution is appreciated but not required. You may not:
- Close-source the baseline prediction models developed here
- Prevent free access to the open prediction layer

The open layer stays open. What you build on top is yours.

## Community

This is a global project. Be respectful. Communicate clearly. Assume good faith. Predictions affect people's lives — take the work seriously and treat fellow contributors with the same seriousness.
