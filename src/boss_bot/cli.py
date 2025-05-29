# pylint: disable=no-name-in-module
"""
Deprecated: CLI functionality has been moved to boss_bot.cli.main
This import path is maintained for backward compatibility and will be removed in v2.0.0
"""

import warnings

# Removed wildcard import to avoid sys.modules conflicts
# from boss_bot.cli.main import *

warnings.warn(
    "Importing from boss_bot.cli is deprecated. Use boss_bot.cli.main instead. This module will be removed in v2.0.0",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export CLI functions for backward compatibility
from boss_bot.cli.main import entry, main

if __name__ == "__main__":
    main()
