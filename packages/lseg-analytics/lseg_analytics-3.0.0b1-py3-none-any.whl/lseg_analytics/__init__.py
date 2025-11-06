import warnings
import sys

warnings.warn(
    "The 'lseg-analytics' package has been renamed to 'lseg-analytics-pricing'. "
    "Please update your dependencies:\n"
    "  pip uninstall lseg-analytics\n"
    "  pip install lseg-analytics-pricing\n"
    "This compatibility package will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

__version__ = "3.0.0b1"
