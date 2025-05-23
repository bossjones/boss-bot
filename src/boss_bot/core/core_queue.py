"""
Deprecated: This module has been moved to boss_bot.core.queue.manager
This import path is maintained for backward compatibility and will be removed in v2.0.0
"""

import warnings

from boss_bot.core.queue.manager import *

warnings.warn(
    "boss_bot.core.core_queue is deprecated. Use boss_bot.core.queue.manager instead. "
    "This module will be removed in v2.0.0",
    DeprecationWarning,
    stacklevel=2,
)
