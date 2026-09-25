"""ResearchCollision evaluation framework (offline-capable).

Everything in this package is designed to run *without* LLM/literature
credentials: provider defaults are forced to the deterministic mock providers
(see ``evaluation.environment``) and the bundled demo dataset is a clearly
labeled SYNTHETIC fixture — never real research evidence.

The framework measures how well a discovery system produces useful,
evidence-grounded research insights. Automatic metrics are computed against
the dataset's known/supporting evidence references; human metrics
(relevance, novelty, plausibility, evidence quality) are defined but never
auto-computed — they are collected offline from raters via the blind rating
template and merged back into reports.
"""

__version__ = "0.1.0"