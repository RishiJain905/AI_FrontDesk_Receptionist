"""Runtime orchestration boundaries for after-hours gating and lifecycle coordination."""

from orchestration.after_hours_gate import GateDecision, is_after_hours

__all__ = ["GateDecision", "is_after_hours"]
