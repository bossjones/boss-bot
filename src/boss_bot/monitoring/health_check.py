"""
Deprecated: This module has been moved to boss_bot.monitoring.health.checker
This import path is maintained for backward compatibility and will be removed in v2.0.0
"""

import warnings

from boss_bot.monitoring.health.checker import *

warnings.warn(
    "boss_bot.monitoring.health_check is deprecated. Use boss_bot.monitoring.health.checker instead. "
    "This module will be removed in v2.0.0",
    DeprecationWarning,
    stacklevel=2,
)
