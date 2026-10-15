"""Shared flow-state representation for Phase 2+ inlet design components.

Every component that models a stage of the inlet (ramp shock, terminal shock,
duct, etc.) takes a FlowState and returns a FlowState, so results can be
chained regardless of how many stages precede or follow.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class FlowState:
    """Local flow state expressed as ratios relative to the freestream condition.

    M: local Mach number (dimensionless)
    p_ratio: p / p_inf (static pressure ratio to freestream)
    T_ratio: T / T_inf (static temperature ratio to freestream)
    p0_ratio: p0 / p0_inf (total/stagnation pressure ratio to freestream)
    T0_ratio: T0 / T0_inf (total/stagnation temperature ratio to freestream;
        stays 1.0 across adiabatic shocks, since total temperature is conserved)
    """

    M: float
    p_ratio: float
    T_ratio: float
    p0_ratio: float
    T0_ratio: float

    @staticmethod
    def freestream(M):
        """FlowState at the freestream condition itself: all ratios are 1.0 by definition."""
        return FlowState(M=float(M), p_ratio=1.0, T_ratio=1.0, p0_ratio=1.0, T0_ratio=1.0)
