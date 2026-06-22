import shapefile
from pathlib import Path
from ..models.geo_objects import GeoDocument, GeoType, GeoObject, CoordType
from typing import List, Tuple


PRJ_TEMPLATES = {
    CoordType.WGS84: 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]',
    CoordType.CGCS2000: 'GEOGCS["GCS_China_Geodetic_Coordinate_System_2000",DATUM["D_China_2000",SPHEROID["CGCS2000",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]',
    CoordType.GCJ02: 'GEOGCS["GCS_GCJ_02",DATUM["D_GCJ_02",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]',
    CoordType.BD09: 'GEOGCS["GCS_BD_09",DATUM["D_BD_09",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]',
}


def _signed_area(ring: List[Tuple[float, float]]) -> float:
    s = 0.0
    for i in range(len(ring) - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]
        s += x1 * y2 - x2 * y1
    return s / 2.0


class ShpWriter:
    def write(self, doc: GeoDocument, filepath: str):
        points, lines, polygons = [], [], []
        for folder in doc.folders:
            for obj in folder.objects:
                if obj.geo_type == GeoType.POINT:
                    points.append((obj, folder.name))
                elif obj.geo_type == GeoType.LINE:
                    lines.append((obj, folder.name))
                elif obj.geo_type == GeoType.POLYGON:
                    polygons.append((obj, folder.name))

        base = Path(filepath)
        ct = doc.coord_type

        if points:
            p = str(base.with_name(base.stem + '_points.shp'))
            self._write_points(points, p)
            self._write_sidecars(p, ct)
        if lines:
            p = str(base.with_name(base.stem + '_lines.shp'))
            self._write_lines(lines, p)
            self._write_sidecars(p, ct)
        if polygons:
            p = str(base.with_name(base.stem + '_polygons.shp'))
            self._write_polygons(polygons, p)
            self._write_sidecars(p, ct)

        if not points and not lines and not polygons:
            p = str(base)
            self._write_points([], p)
            self._write_sidecars(p, ct)

    def _write_sidecars(self, shp_path: str, coord_type: CoordType):
        Path(shp_path).with_suffix('.prj').write_text(
            PRJ_TEMPLATES.get(coord_type, PRJ_TEMPLATES[CoordType.WGS84]), encoding='utf-8')
        Path(shp_path).with_suffix('.cpg').write_text('UTF-8', encoding='utf-8')

    def _new_writer(self, filepath: str):
        w = shapefile.Writer(filepath, encoding='utf-8')
        w.field('NAME', 'C', 100)
        w.field('DESC', 'C', 254)
        w.field('FOLDER', 'C', 100)
        return w

    def _write_points(self, items, filepath: str):
        w = self._new_writer(filepath)
        for obj, folder_name in items:
            if obj.coordinates:
                c = obj.coordinates[0]
                w.point(c.lon, c.lat)
                w.record(obj.name, obj.description or '', folder_name)
        w.close()

    def _write_lines(self, items, filepath: str):
        w = self._new_writer(filepath)
        for obj, folder_name in items:
            if len(obj.coordinates) >= 2:
                w.line([[(c.lon, c.lat) for c in obj.coordinates]])
                w.record(obj.name, obj.description or '', folder_name)
        w.close()

    def _write_polygons(self, items, filepath: str):
        w = self._new_writer(filepath)
        for obj, folder_name in items:
            if len(obj.coordinates) >= 3:
                ring = [(c.lon, c.lat) for c in obj.coordinates]
                if ring[0] != ring[-1]:
                    ring.append(ring[0])
                if _signed_area(ring) > 0:
                    ring.reverse()
                w.poly([ring])
                w.record(obj.name, obj.description or '', folder_name)
        w.close()
