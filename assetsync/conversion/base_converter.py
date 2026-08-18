from abc import ABC, abstractmethod

from ..core.asset_descriptor import AssetDescriptor
from .conversion_result import ConversionResult


class BaseConverter(ABC):
    source_formats = frozenset()
    target_format = ""
    version = 1

    @abstractmethod
    def convert(self, asset: AssetDescriptor, destination: str) -> ConversionResult:
        raise NotImplementedError

