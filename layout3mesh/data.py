"""
Data sctructures for layout2svg
"""

from dataclasses import dataclass
from typing import Tuple, Union, Optional, List, Dict


@dataclass
class Material:
    text: str  # material texture
    rgba: List[int]

    @property
    def rgb(self):
        return tuple(self.rgba[:3])

    @property
    def hex(self):
        return "#%02x%02x%02x" % self.rgb

    @property
    def hexa(self):
        return "#%02x%02x%02x%02x" % self.rgba


@dataclass
class LayerMetadata:
    type: str
    keys: List[str]  # alternative names for the layer
    material: Material


@dataclass
class LayerProperties:
    ly: float
    dt: float
    # Non necessary properties for this tool:
    top: Optional[float] = None
    bot: Optional[float] = None
    zh: Optional[float] = None
    th: Optional[float] = None
    mw: Optional[float] = None
    sqrres: Optional[float] = None
    dc_avgcd: Optional[float] = None
    ac_rmscd: Optional[float] = None
    sqrcap: Optional[float] = None


@dataclass
class Layer:
    name: str  # layer name
    lydt: Tuple[int, int]
    metadata: Optional[LayerMetadata]
    properties: Optional[LayerProperties]

    def __getitem__(self, index):
        return self.lydt[index]

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Layer):
            return self.lydt == __value.lydt
        elif isinstance(__value, tuple):
            return self.lydt == __value
        return False

    def __hash__(self) -> int:
        return hash(self.lydt)

    def __repr__(self) -> str:
        return f"Layer({self.lydt})"

    def __ne__(self, __value: object) -> bool:
        return not (self.__eq__(__value))


@dataclass
class LayerStack(Dict):
    layers: Dict[Tuple[int, int], Layer]

    def __init__(self, layers: Dict[Tuple[int, int], Layer]):
        self.layers = layers

    def __getitem__(self, key):
        return self.layers.get(key)

    def __setitem__(self, key, value):
        self.layers[key] = value

    def __delitem__(self, key):
        del self.layers[key]

    def __iter__(self):
        self._iter = iter(self.layers)

    def __next__(self):
        self._iter.__next__()

    def __len__(self):
        return len(self.layers)

    def __repr__(self) -> str:
        return f"LayerStack({self.layers})"
