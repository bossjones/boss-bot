"""
Deprecated: This module has been moved to boss_bot.bot.cogs
This import path is maintained for backward compatibility and will be removed in v2.0.0
"""

import warnings

from boss_bot.bot.cogs import *

warnings.warn(
    "boss_bot.global_cogs is deprecated. Use boss_bot.bot.cogs instead. This module will be removed in v2.0.0",
    DeprecationWarning,
    stacklevel=2,
)
