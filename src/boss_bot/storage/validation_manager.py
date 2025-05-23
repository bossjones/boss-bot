"""
Deprecated: This module has been moved to boss_bot.storage.managers.validation_manager
This import path is maintained for backward compatibility and will be removed in v2.0.0
"""

import warnings

from boss_bot.storage.managers.validation_manager import *

warnings.warn(
    "boss_bot.storage.validation_manager is deprecated. Use boss_bot.storage.managers.validation_manager instead. "
    "This module will be removed in v2.0.0",
    DeprecationWarning,
    stacklevel=2,
)
