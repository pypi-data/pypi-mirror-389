from .download import check_files
from .base import Iri2020
from .settings import Settings, ComputedSettings, B0B1Model, FoF2Model, NiModel, NeMode, MagField, F1Model, TeTopModel, DRegionModel, TopsideModel, HmF2Model, IonTempModel, PlasmasphereModel
from .utils import alt_grid
check_files()

__all__ = [
    "Iri2020", "Settings", "ComputedSettings", "B0B1Model", "FoF2Model", "NiModel", "NeMode", "MagField",
    "F1Model", "TeTopModel", "DRegionModel", "TopsideModel", "HmF2Model", "IonTempModel", "PlasmasphereModel",
    "alt_grid"
]
