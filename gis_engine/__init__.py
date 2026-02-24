"""GIS Engine - Main package initialization."""

from .core import WorkflowExecutor, StepRegistry, ContextManager
from .raster import DEMProcessor, SlopeCalculator, Reclassify
from .vector import OSMLoader, Buffer, LandUseAnalysis
from .analysis import Overlay, Threshold, SuitabilityAnalysis
from .utils import FileIO, CRSManager, Logger

__version__ = '0.1.0'

__all__ = [
    'WorkflowExecutor',
    'StepRegistry',
    'ContextManager',
    'DEMProcessor',
    'SlopeCalculator',
    'Reclassify',
    'OSMLoader',
    'Buffer',
    'LandUseAnalysis',
    'Overlay',
    'Threshold',
    'SuitabilityAnalysis',
    'FileIO',
    'CRSManager',
    'Logger',
]
