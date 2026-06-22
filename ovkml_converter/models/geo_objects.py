from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class CoordType(Enum):
    WGS84 = "WGS84"
    GCJ02 = "GCJ02"
    CGCS2000 = "CGCS2000"
    UNKNOWN = "UNKNOWN"


class GeoType(Enum):
    POINT = "Point"
    LINE = "LineString"
    POLYGON = "Polygon"


@dataclass
class GeoPoint:
    lon: float
    lat: float
    alt: float = 0.0


@dataclass
class GeoObject:
    name: str
    description: Optional[str] = None
    geo_type: GeoType = GeoType.POINT
    coordinates: List[GeoPoint] = field(default_factory=list)
    coord_type: CoordType = CoordType.UNKNOWN
    style: Optional[Dict[str, Any]] = None
    attributes: Optional[Dict[str, Any]] = None


@dataclass
class GeoFolder:
    name: str
    objects: List[GeoObject] = field(default_factory=list)


@dataclass
class GeoDocument:
    name: str
    folders: List[GeoFolder] = field(default_factory=list)
    coord_type: CoordType = CoordType.UNKNOWN

    def get_all_objects(self) -> List[GeoObject]:
        result = []
        for folder in self.folders:
            result.extend(folder.objects)
        return result

    def get_object_count(self) -> int:
        return sum(len(f.objects) for f in self.folders)
