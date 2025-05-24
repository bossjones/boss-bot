"""
Deprecated: This module has been moved to boss_bot.core.downloads.manager
This import path is maintained for backward compatibility and will be removed in v2.0.0
"""

import warnings

from boss_bot.core.downloads.manager import *

warnings.warn(
    "boss_bot.downloaders.base is deprecated. Use boss_bot.core.downloads.manager instead. "
    "This module will be removed in v2.0.0",
    DeprecationWarning,
    stacklevel=2,
)
