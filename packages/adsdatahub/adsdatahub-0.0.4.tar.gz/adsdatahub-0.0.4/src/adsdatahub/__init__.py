import importlib.metadata

from .client import Client as Client
from .client import MockClient as MockClient
from .client import RealClient as RealClient

__version__ = importlib.metadata.version(__name__)
