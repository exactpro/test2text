"""
Copyright 2025 Exactpro Systems Limited - All Rights Reserved.

This software is owned by Exactpro Systems Limited and/or its affiliates
(hereinafter collectively referred to as the "Exactpro Group").

The scope and terms of a user license for this proprietary software
(hereinafter referred to as the "Exactpro Software License")
granted by the Exactpro Group to Your Firm are set out in the existing applicable
Master Services Agreement (or a similar overarching services agreement)
and/or relevant statement(s) of work (hereinafter collectively referred to as the "MSA")
between Your Firm and an affiliate of the Exactpro Group.

Any violation of the Exactpro Software License is prohibited and may result in legal action(s),
such as claim(s), lawsuit(s) and severe penalties.

Except as set out in the applicable MSA, this source code is provided 'AS IS'
without warranty of any kind.
The limitations of liability are set out in the applicable MSA.

Please reach out to Your Firm's Legal department for a copy of the applicable MSA.

Utilities for working with StateTransition objects.
"""

from typing import Dict, List

from ex_tmodel2.base.base import StateTransition


def relocate_late_effects(transitions: List[StateTransition]) -> None:
    """
    Relocate late-arrived downstream effects to their corresponding state transitions.

    This function processes a list of StateTransitions and moves effects that arrived late
    (in a later transition) to the transition they actually belong to, based on the
    state_transition_timestamp field.

    The first transition that has an effect with a particular state_transition_timestamp
    "claims" that timestamp. Effects in subsequent transitions with the same timestamp
    are moved to the claiming transition.

    Args:
        transitions: List of StateTransition objects to process (modified in place)
    """
    timestamp_to_transition: Dict[str, StateTransition] = {}

    for transition in transitions:
        # Iterate over a copy since we may remove items
        for effect in transition.downstream_effects[:]:
            timestamp = effect.state_transition_timestamp
            if timestamp is not None:
                if timestamp in timestamp_to_transition:
                    # Move effect to the transition that owns this timestamp
                    target_transition = timestamp_to_transition[timestamp]
                    if target_transition is not transition:
                        transition.downstream_effects.remove(effect)
                        target_transition.add_effect(effect)
                else:
                    # This transition claims this timestamp
                    timestamp_to_transition[timestamp] = transition
