# Mushroom

Analysis of the UCI Mushroom dataset.

## Hypothesis

No single feature perfectly separates edible from poisonous mushrooms — every attribute (odor, gill color, habitat, etc.) has at least some values that appear in both classes. However, certain combinations of two features form exclusive patterns that belong entirely to one class.

A *feature pair* is exclusive for a given class if every mushroom in the dataset that exhibits that pair of values has the same edibility. The hypothesis is that a minimal set of these exclusive feature pairs is enough to determine the edibility of every mushroom.

Two sets can be computed:

- **Edible-only set**: feature pairs that appear exclusively on edible mushrooms. If a mushroom matches any rule in this set, it is edible; otherwise, it is poisonous.
- **Poisonous-only set**: feature pairs that appear exclusively on poisonous mushrooms. If a mushroom matches any rule in this set, it is poisonous; otherwise, it is edible.

Either set alone is sufficient to classify the entire dataset. The most useful set is whichever is smaller — that is, whichever requires fewer feature-pair rules to cover its class. Running the notebook computes both and identifies the winner.

## Contributing

### Commit Messages

- Describe the change in plain, conceptual language tied to the problem domain
- No method names, variable names, or language keywords — concrete enough to be meaningful, but never mechanical
- No conventional commit prefixes or category labels (`fix:`, `feat:`, `refactor:`, etc.)
- Sentence casing — capitalize the first word
- Drop unnecessary filler words ("the", "that", etc.)

| ✅ | ❌ |
|---|---|
| Improve expressiveness of algorithm | Refactor: use while condition and incremental sum in findMinimalSet... |
| Guard against missing feature pairs | Fix: prevent IndexError when no matching feature pairs remain |