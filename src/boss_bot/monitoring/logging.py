# pylint: disable=no-name-in-module
"""
Deprecated: This module has been moved to boss_bot.monitoring.logging.logging_config
This import path is maintained for backward compatibility and will be removed in v2.0.0
"""

import warnings

from boss_bot.monitoring.logging.logging_config import *

warnings.warn(
    "boss_bot.monitoring.logging is deprecated. Use boss_bot.monitoring.logging.logging_config instead. "
    "This module will be removed in v2.0.0",
    DeprecationWarning,
    stacklevel=2,
)
