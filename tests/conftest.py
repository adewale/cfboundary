from __future__ import annotations

from hypothesis import settings

# Every run, local or CI, uses a fixed budget and a derandomized seed so a failure reproduces
# exactly. 100 examples is Hypothesis's own default, so this does not raise the budget.
# For a deeper, randomized run on demand: uv run pytest tests/test_surface_polish.py --hypothesis-profile=deep
settings.register_profile("fixed", max_examples=100, derandomize=True)
settings.register_profile("deep", max_examples=5_000)
settings.load_profile("fixed")
