class AlphaWatchError(Exception):
    """Base exception for domain failures."""


class DataContractError(AlphaWatchError):
    """Input violates a declared data contract."""


class LookAheadError(DataContractError):
    """Information was used before it was available."""


class IdentityResolutionError(DataContractError):
    """A security identity cannot be resolved unambiguously."""
