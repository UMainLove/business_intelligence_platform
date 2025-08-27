"""
Legal and Compliance Module

Handles user agreements, disclaimers, and legal compliance for the Business Intelligence Platform.
"""

from .user_agreement import LegalAgreement, require_legal_acceptance

__all__ = ["LegalAgreement", "require_legal_acceptance"]
