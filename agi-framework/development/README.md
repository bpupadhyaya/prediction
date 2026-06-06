# AGI Framework — Development

## Purpose

Implement the AGI framework incrementally, starting from components that can be validated against real prediction tasks long before full AGI capability is achieved.

## Development Philosophy

Build incrementally — each component should be useful even before the full system is complete:

1. **Natural language query interface** (earliest) — even without causal reasoning, a natural language interface to existing predictions has value
2. **Cross-domain explanation** — explain why predictions correlate across domains (correlation first, causation later)
3. **Novel prediction synthesis** — generate predictions for unlisted types using the existing model
4. **Causal reasoning** — graduate from correlation to mechanistic reasoning
5. **World model** — fully integrated, continuously updating individual model

## Planned Components

### `src/nl_interface/`
Natural language query interface to the prediction stack. Takes free-text questions, maps them to structured prediction queries, returns natural language answers with uncertainty.

**Milestone 1:** "What is my biggest health risk?" → synthesized health domain answer

### `src/cross_domain_explanation/`
Given two predictions from different domains, explain the known relationship between them.

**Milestone 1:** "How does my financial stress relate to my health predictions?" → explained with evidence

### `src/novel_prediction/`
Given a prediction request not covered by any project, generate a best-effort prediction with clearly stated reasoning and uncertainty.

**Milestone 1:** Correctly identifies that a novel query is adjacent to an existing project and routes accordingly

### `src/causal_engine/`
Causal graph over all domain variables. Supports counterfactual queries ("what would my life expectancy be if I quit smoking?").

**Milestone 1:** Single-domain counterfactual reasoning in health domain

### `src/world_model/`
The integrated, continuously updating individual model.

**Milestone 1:** Static snapshot that combines all domain predictions into a unified individual profile

## Status

All components planned. Implementation begins when Collective Intelligence has a working interface to consume.

## Evaluation

Each component will be evaluated against:
- Correctness (does it produce accurate answers?)
- Calibration (does it know what it doesn't know?)
- Usefulness (do real users find the output actionable?)
- Consistency (does it give consistent answers to equivalent questions?)
