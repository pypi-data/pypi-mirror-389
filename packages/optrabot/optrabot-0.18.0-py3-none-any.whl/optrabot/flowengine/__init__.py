"""
Flow Engine Module

This module provides the flow engine functionality for automating
actions based on trading events.
"""

from .flowengine import FlowEngine
from .flowconfig import FlowActionType
from .flowevent import (
    FlowEventType,
    FlowEventData,
    TradeOpenedEventData,
    EarlyExitEventData,
    StopLossHitEventData,
    TakeProfitHitEventData
)

__all__ = [
    'FlowEngine',
    'FlowActionType',
    'FlowEventType',
    'FlowEventData',
    'TradeOpenedEventData',
    'EarlyExitEventData',
    'StopLossHitEventData',
    'TakeProfitHitEventData'
]
