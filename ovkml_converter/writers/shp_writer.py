import shapefile
from pathlib import Path
from ..models.geo_objects import GeoDocument, GeoType, GeoObject, CoordType
from typing import List


PRJ_TEMPLATES = {
    CoordType.WGS84: 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]',
    CoordType.CGCS2000: 'GEOGCS["GCS_China_Geodetic_Coordinate_System_2000",DATUM["D_China_2000",SPHEROID["CGCS2000",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]',
    CoordType.GCJ02: 'GEOGCS["GCS_GCJ_02",DATUM["D_GCJ_02",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]',
}


class ShpWriter:
    def write(self, doc: GeoDocument, filepath: str):
        points = []
        lines = []
        polygons = []

        for folder in doc.folders:
            for obj in folder.objects:
                if obj.geo_type == GeoType.POINT:
                    points.append(obj)
                elif obj.geo_type == GeoType.LINE:
                    lines.append(obj)
                elif obj.geo_type == GeoType.POLYGON:
                    polygons.append(obj)

        base = Path(filepath)
        coord_type = doc.coord_type

        if points:
            shp_path = str(base.with_name(base.stem + '_points.shp'))
            self._write_points(points, shp_path)
            self._write_prj(shp_path, coord_type)
        if lines:
            shp_path = str(base.with_name(base.stem + '_lines.shp'))
            self._write_lines(lines, shp_path)
            self._write_prj(shp_path, coord_type)
        if polygons:
            shp_path = str(base.with_name(base.stem + '_polygons.shp'))
            self._write_polygons(polygons, shp_path)
            self._write_prj(shp_path, coord_type)

        if not points and not lines and not polygons:
            shp_path = str(base)
            self._write_points([], shp_path)
            self._write_prj(shp_path, coord_type)

    def _write_prj(self, shp_path: str, coord_type: CoordType):
        prj_path = Path(shp_path).with_suffix('.prj')
        wkt = PRJ_TEMPLATES.get(coord_type, PRJ_TEMPLATES[CoordType.WGS84])
        with open(prj_path, 'w', encoding='utf-8') as f:
            f.write(wkt)

    def _write_points(self, objects: List[GeoObject], filepath: str):
        w = shapefile.Writer(filepath)
        w.field('NAME', 'C', 100)
        w.field('DESC', 'C', 254)

        for obj in objects:
            if obj.coordinates:
                c = obj.coordinates[0]
                w.point(c.lon, c.lat)
                w.record(obj.name, obj.description or '')

        w.close()

    def _write_lines(self, objects: List[GeoObject], filepath: str):
        w = shapefile.Writer(filepath)
        w.field('NAME', 'C', 100)
        w.field('DESC', 'C', 254)

        for obj in objects:
            if len(obj.coordinates) >= 2:
                line = [(c.lon, c.lat) for c in obj.coordinates]
                w.line([line])
                w.record(obj.name, obj.description or '')

        w.close()

    def _write_polygons(self, objects: List[GeoObject], filepath: str):
        w = shapefile.Writer(filepath)
        w.field('NAME', 'C', 100)
        w.field('DESC', 'C', 254)

        for obj in objects:
            if len(obj.coordinates) >= 3:
                ring = [(c.lon, c.lat) for c in obj.coordinates]
                if ring[0] != ring[-1]:
                    ring.append(ring[0])
                w.poly([ring])
                w.record(obj.name, obj.description or '')

        w.close()
