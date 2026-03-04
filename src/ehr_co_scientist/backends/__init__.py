"""Backend integrations used by the EHR Co-Scientist agent."""

from ehr_co_scientist.backends.adapter import BackendConfig, run_chat_completion

__all__ = ["BackendConfig", "run_chat_completion"]
