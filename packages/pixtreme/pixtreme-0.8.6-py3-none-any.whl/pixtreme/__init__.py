"""pixtreme: A High-Performance Graphics Library with CUDA Support

Meta-package that provides unified access to all pixtreme functionality.

Core package is always available. Other packages (aces, filter, draw, upscale)
are optional and imported if available.

Install options:
- pip install pixtreme          # Core only
- pip install pixtreme[all]     # Core + all optional packages
- pip install pixtreme[aces]    # Core + ACES color management
- pip install pixtreme[filter]  # Core + image filters
- pip install pixtreme[draw]    # Core + drawing primitives
- pip install pixtreme[upscale] # Core + upscaling backends
- pip install pixtreme[full]    # All packages including legacy + tensorrt
"""

__version__ = "0.8.6"

# Core package is always available
from pixtreme_core import *

# Optional packages - import if available
try:
    from pixtreme_aces import *
except ImportError:
    pass

try:
    from pixtreme_filter import *
except ImportError:
    pass

try:
    from pixtreme_draw import *
except ImportError:
    pass

try:
    from pixtreme_upscale import *
except ImportError:
    pass
