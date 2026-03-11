"""Backend integrations used by the MedCLI agent."""

from medcli.backends.adapter import BackendConfig, run_chat_completion

__all__ = ["BackendConfig", "run_chat_completion"]
