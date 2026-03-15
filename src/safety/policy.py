"""
Safety policy engine for Windows Dev Agent Plugin.

Enforces safety levels and approval requirements.
"""

import logging
from typing import Dict, Tuple, Optional
from ..schemas.capability import SafetyLevel, CapabilityDefinition

logger = logging.getLogger(__name__)


class SafetyPolicy:
    """Manages safety levels and approval requirements."""

    def __init__(self):
        self.autonomous_capabilities = set()
        self.approval_required_capabilities = set()
        self.forbidden_capabilities = set()

    def register_capability(self, capability: CapabilityDefinition):
        """Register a capability with its safety level."""
        if capability.is_autonomous():
            self.autonomous_capabilities.add(capability.id)
        elif capability.requires_approval():
            self.approval_required_capabilities.add(capability.id)
        elif capability.is_forbidden():
            self.forbidden_capabilities.add(capability.id)

    def can_execute(self, capability_id: str, user_approved: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Check if a capability can be executed.

        Returns:
            (can_execute, reason_if_not)
        """
        if capability_id in self.autonomous_capabilities:
            return True, None

        if capability_id in self.forbidden_capabilities:
            return False, "Capability is forbidden"

        if capability_id in self.approval_required_capabilities:
            if user_approved:
                return True, None
            else:
                return False, "Capability requires user approval"

        return False, "Unknown capability"

    def get_safety_level(self, capability_id: str) -> SafetyLevel:
        """Get safety level of a capability."""
        if capability_id in self.autonomous_capabilities:
            return SafetyLevel.AUTONOMOUS
        elif capability_id in self.approval_required_capabilities:
            return SafetyLevel.APPROVAL_REQUIRED
        else:
            return SafetyLevel.FORBIDDEN

    def get_summary(self) -> Dict[str, int]:
        """Get safety summary."""
        return {
            "autonomous": len(self.autonomous_capabilities),
            "approval_required": len(self.approval_required_capabilities),
            "forbidden": len(self.forbidden_capabilities),
        }
