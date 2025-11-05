"""
Investor namespace bridge for the Fin68 private core.

Exports the default implementation expected by ``fin68.clients``.
"""

from .core_impl import InvestorCoreImpl

__all__ = ["InvestorCoreImpl"]
