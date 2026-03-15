"""Tests for safety policy engine."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.safety.policy import SafetyPolicy
from src.schemas.capability import CapabilityDefinition, IntentClass, SafetyLevel


class TestSafetyPolicy:
    """Test safety policy."""

    def test_policy_creation(self):
        """Test creating safety policy."""
        policy = SafetyPolicy()
        assert policy is not None

    def test_autonomous_capability(self):
        """Test autonomous capability."""
        policy = SafetyPolicy()
        cap = CapabilityDefinition(
            id="lint",
            name="Lint",
            description="Lint",
            intent_class=IntentClass.LINT,
            safety_level=SafetyLevel.AUTONOMOUS,
        )
        policy.register_capability(cap)

        can_execute, reason = policy.can_execute("lint")
        assert can_execute is True
        assert reason is None

    def test_approval_required(self):
        """Test approval required capability."""
        policy = SafetyPolicy()
        cap = CapabilityDefinition(
            id="update-deps",
            name="Update Dependencies",
            description="Update",
            intent_class=IntentClass.DEPENDENCY_UPDATE,
            safety_level=SafetyLevel.APPROVAL_REQUIRED,
        )
        policy.register_capability(cap)

        can_execute, reason = policy.can_execute("update-deps", user_approved=False)
        assert can_execute is False

        can_execute, reason = policy.can_execute("update-deps", user_approved=True)
        assert can_execute is True

    def test_forbidden_capability(self):
        """Test forbidden capability."""
        policy = SafetyPolicy()
        cap = CapabilityDefinition(
            id="forbidden",
            name="Forbidden",
            description="Forbidden",
            intent_class=IntentClass.DEBUG,
            safety_level=SafetyLevel.FORBIDDEN,
        )
        policy.register_capability(cap)

        can_execute, reason = policy.can_execute("forbidden")
        assert can_execute is False

    def test_get_summary(self):
        """Test getting policy summary."""
        policy = SafetyPolicy()
        policy.register_capability(
            CapabilityDefinition(
                id="auto",
                name="Auto",
                description="Auto",
                intent_class=IntentClass.LINT,
                safety_level=SafetyLevel.AUTONOMOUS,
            )
        )
        summary = policy.get_summary()
        assert summary["autonomous"] == 1
        assert summary["approval_required"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
