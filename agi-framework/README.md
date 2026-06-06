# AGI Framework

The AGI Framework is the top tier of the Prediction project architecture. It takes the outputs of the Collective Intelligence layer and builds the reasoning, generalization, and synthesis capabilities that constitute Artificial General Intelligence grounded in human life modeling.

## The Hypothesis

AGI will not emerge from scaling a single objective on text. It will emerge from a system that can:

1. **Reason across domains** — understand how a health prediction changes financial predictions, how an early-life prediction affects aging predictions, how macro events cascade to individual outcomes
2. **Generalize to novel prediction types** — when asked about a prediction type not explicitly modeled, reason from the full picture of what it knows about this person's life
3. **Model causal mechanisms** — not just correlate features with outcomes, but understand *why* certain patterns predict certain outcomes
4. **Update continuously** — incorporate new information from all domains simultaneously, updating its model of the person and the world
5. **Communicate uncertainty** — know what it doesn't know, and say so

This is the architecture we are building toward.

## Relationship to Collective Intelligence

```
Collective Intelligence provides:          AGI Framework adds:
- Domain-specific predictions              - Cross-domain causal reasoning
- Interaction modeling                     - Novel prediction generalization  
- Integrated trajectory                    - Natural language interface
- Accuracy tracking                        - Uncertainty quantification
                                           - Continuous world model update
```

## Architecture Vision

### Layer 1: World Model
A continuously updated model of the individual and the world they live in. Incorporates all domain predictions, macro context, and individual history. Not a static snapshot — a live, updating representation.

### Layer 2: Causal Reasoning Engine
Goes beyond correlation to model causal mechanisms. When a new data point arrives, it propagates implications across the world model. When asked a question, it traces causal pathways rather than pattern-matching.

### Layer 3: Generalization Engine
Given a novel prediction request not covered by any existing project, generates a prediction by reasoning from the world model. Documents its reasoning and uncertainty.

### Layer 4: Natural Language Interface
All of the above is accessible through natural language. A person can ask "what is my biggest risk in the next 10 years?" and receive a synthesized, explained, uncertain-aware answer drawing from all domains.

## Research Focus

See [research/](research/) for:
- AGI architecture literature (causal models, world models, continual learning)
- Natural language interfaces to structured prediction systems
- Uncertainty representation and communication
- Evaluation frameworks for AGI-level systems

## Development Focus

See [development/](development/) for:
- World model architecture specification
- Causal reasoning engine design
- Natural language interface prototype
- Continuous learning framework

## Status

The AGI framework is the long-horizon goal. Current milestone: establish theoretical architecture. Implementation begins when Collective Intelligence is operational.

## Why This Matters

Most AGI efforts are working on abstract benchmarks. We are working on something grounded: a system that understands human life well enough to reason about it holistically. We believe this is the right path — not because it is easier, but because it is more likely to produce intelligence that is genuinely aligned with human flourishing.
