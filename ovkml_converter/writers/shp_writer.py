import re
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

    def _attr_fields(self, items):
        """收集所有对象的属性键，生成 (原始键, DBF字段名) 列表。

        DBF 字段名受限：≤10 字符、仅字母数字下划线、需唯一。奥维记录的属性
        （ObjID/tmModify/Time 等）据此写入 DBF，从而在 GIS 属性表中显示。
        """
        keys = []
        seen = set()
        for obj, _ in items:
            for k in (obj.attributes or {}):
                if k not in seen:
                    seen.add(k)
                    keys.append(k)

        fields = []
        used = set()
        for k in keys:
            name = re.sub(r'[^A-Za-z0-9_]', '', k).upper()[:10] or 'ATTR'
            base, i = name, 1
            while name in used:
                suffix = str(i)
                name = base[:10 - len(suffix)] + suffix
                i += 1
            used.add(name)
            fields.append((k, name))
        return fields

    def _new_writer(self, filepath: str, attr_fields):
        w = shapefile.Writer(filepath, encoding='utf-8')
        w.field('NAME', 'C', 100)
        w.field('DESC', 'C', 254)
        w.field('FOLDER', 'C', 100)
        for _, fname in attr_fields:
            w.field(fname, 'C', 80)
        return w

    def _record(self, w, obj, folder_name, attr_fields):
        attrs = obj.attributes or {}
        values = [obj.name, obj.description or '', folder_name]
        values += [str(attrs.get(k, '')) for k, _ in attr_fields]
        w.record(*values)

    def _write_points(self, items, filepath: str):
        attr_fields = self._attr_fields(items)
        w = self._new_writer(filepath, attr_fields)
        for obj, folder_name in items:
            if obj.coordinates:
                c = obj.coordinates[0]
                w.point(c.lon, c.lat)
                self._record(w, obj, folder_name, attr_fields)
        w.close()

    def _write_lines(self, items, filepath: str):
        attr_fields = self._attr_fields(items)
        w = self._new_writer(filepath, attr_fields)
        for obj, folder_name in items:
            if len(obj.coordinates) >= 2:
                w.line([[(c.lon, c.lat) for c in obj.coordinates]])
                self._record(w, obj, folder_name, attr_fields)
        w.close()

    def _write_polygons(self, items, filepath: str):
        attr_fields = self._attr_fields(items)
        w = self._new_writer(filepath, attr_fields)
        for obj, folder_name in items:
            if len(obj.coordinates) >= 3:
                ring = [(c.lon, c.lat) for c in obj.coordinates]
                if ring[0] != ring[-1]:
                    ring.append(ring[0])
                if _signed_area(ring) > 0:
                    ring.reverse()
                w.poly([ring])
                self._record(w, obj, folder_name, attr_fields)
        w.close()
