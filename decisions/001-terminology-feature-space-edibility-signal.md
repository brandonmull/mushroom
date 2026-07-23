# 001 — Adopt "feature space" and "edibility signal" as terminology

## Decision

Use **feature space** for a combination of feature names and **edibility signal** for a specific combination of feature values.

| Term | Definition | Example |
|---|---|---|
| **feature space** | A combination of two (or more) feature names, defining the dimensions to search within. | "odor and gill-color form a feature space" |
| **edibility signal** | A specific combination of feature values within a feature space that indicates edibility or poisonousness. | "the edibility signal `odor=p, gill-color=w` is exclusive to edible mushrooms" |

## Context

The project analyzes feature pairs (two features at a time) to find combinations of values that indicate edibility. The phrase "feature pair" was ambiguous — it could refer to either:

- A pair of feature **names** (e.g., odor and gill-color)
- A pair of feature **values** (e.g., odor=p and gill-color=w)

Longer phrasings like "feature name pair" and "feature value pair" were verbose and awkward.

## Alternatives considered

### Name-level concept (replacing "feature name pair")

| Term | Verdict | Reason |
|---|---|---|
| **cross** | Rejected | Doesn't retain the word "feature" |
| **span** | Rejected | Implies exactly two endpoints (doesn't scale to 3+ features) |
| **channel** | Rejected | Sounds one-dimensional |
| **field** | Rejected | Ambiguous with "field" meaning a single data column |
| **domain** | Close | Logically precise but less intuitive than "space" |
| **feature space** | **Chosen** | Intuitive, spatial, dimensionality-agnostic, and naturally pairs with "searching" |

### Value-level concept (replacing "feature value pair")

| Term | Verdict | Reason |
|---|---|---|
| **signal** | Close | Strong but failed the "brother test" — not immediately grasppable by a fresh reader |
| **point / vector / coordinate** | Rejected | Too mathematical |
| **key / tag / tuple** | Rejected | Too programming-oriented |
| **profile** | Rejected | Implies the full range of features, not scoped to a specific space |
| **trait** | Rejected | Synonym for feature; implies a single value |
| **tell** | Rejected | Poker jargon |
| **edibility signal** | **Chosen** | Domain-qualified, immediately clear, and passed the "brother test" |

## Rationale

- **Feature space** is spatial and intuitive — you search a space. It scales beyond two features without renaming.
- **Edibility signal** anchors the concept in the problem domain. The domain qualifier ("edibility") does the heavy lifting that made bare "signal" or "feature signal" less immediately clear.
- Together: *you search a feature space for edibility signals.*