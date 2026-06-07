"""Stage implementations for the Radar operational orchestrator.

Lazy wrappers avoid importing heavy stage dependencies before the selected
stage hands execution off to its own configured Python environment.
"""


def run_preflight_stage(*args, **kwargs):
    from .preflight_stage import run_stage

    return run_stage(*args, **kwargs)


def run_extraction_stage(*args, **kwargs):
    from .extraction_stage import run_stage

    return run_stage(*args, **kwargs)


def run_preprocessing_stage(*args, **kwargs):
    from .preprocessing_stage import run_stage

    return run_stage(*args, **kwargs)


def run_nlp_stage(*args, **kwargs):
    from .nlp_stage import run_stage

    return run_stage(*args, **kwargs)


def run_modeling_stage(*args, **kwargs):
    from .modeling_stage import run_stage

    return run_stage(*args, **kwargs)


__all__ = [
    "run_preflight_stage",
    "run_extraction_stage",
    "run_preprocessing_stage",
    "run_nlp_stage",
    "run_modeling_stage",
]
