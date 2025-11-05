# Re-export all public symbols from subpackages for convenient imports
# e.g. from agents_adapter.models import AgentReference

# Azure AI Agents models
try:
    from .agents.models import *  # type: ignore  # noqa: F401,F403
    from .agents.models import __all__ as _azure_all  # type: ignore
except Exception:  # pragma: no cover
    _azure_all = []  # type: ignore

# OpenAI-compatible models
try:
    from .openai.models import *  # type: ignore  # noqa: F401,F403
    from .openai.models import __all__ as _openai_all  # type: ignore
except Exception:  # pragma: no cover
    _openai_all = []  # type: ignore

# Construct combined __all__ while preserving order and avoiding duplicates
__all__ = []  # type: ignore[var-annotated]
for _name in list(_azure_all) + list(_openai_all):  # type: ignore
    if _name not in __all__:
        __all__.append(_name)
