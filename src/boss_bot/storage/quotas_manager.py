"""
Deprecated: This module has been moved to boss_bot.storage.managers.quota_manager
This import path is maintained for backward compatibility and will be removed in v2.0.0
"""

import warnings

from boss_bot.storage.managers.quota_manager import *

warnings.warn(
    "boss_bot.storage.quotas_manager is deprecated. Use boss_bot.storage.managers.quota_manager instead. "
    "This module will be removed in v2.0.0",
    DeprecationWarning,
    stacklevel=2,
)
