"""Type definitions for CQTech Metrics SDK"""
from typing import Union, List, Dict, Any, Optional
from enum import Enum


class MetricType(Enum):
    """Metric type enumeration"""
    ATOMIC = 1
    DERIVED = 2
    COMPOSITE = 3
    CUSTOM = 4


class SceneVersionStatus(Enum):
    """Scene version status enumeration"""
    OFFLINE = 0
    ONLINE = 1


class MetricInstanceState(Enum):
    """Metric instance state enumeration"""
    OFFLINE = 0
    ONLINE = 1