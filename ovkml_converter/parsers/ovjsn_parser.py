import json
from pathlib import Path
from typing import List, Optional
from ..models.geo_objects import (
    CoordType, GeoType, GeoPoint, GeoObject, GeoFolder, GeoDocument
)


class OvjsnParser:
    """解析奥维 OVJSN（JSON）格式。

    结构要点（实测自奥维 V10.6.2 导出）：
      {"Version":..,"Type":1,"ObjItems":[
          {"Type":<7点/8线/13面>,"Object":{
              "Name":..,"Comment":..,"ObjectDetail":{
                  "Gcj02":0|1,            # 顶层坐标系标志：1=GCJ02，0=CGCS2000
                  "Lat":..,"Lng":..,      # 点对象的单点坐标
                  "Latlng":[lat,lon,..]   # 线/面对象的扁平坐标数组（纬,经 顺序）
              }}}]}
    注意：ObjectDetail 内还嵌有一个 Obj3dView.Gcj02，与坐标系无关，**不可使用**。
    """

    TYPE_MAP = {7: GeoType.POINT, 8: GeoType.LINE, 13: GeoType.POLYGON}

    def parse(self, filepath: str) -> GeoDocument:
        # OVJSN 文件常带 UTF-8 BOM，用 utf-8-sig 读取以兼容
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)

        doc_name = Path(filepath).stem
        objects = []
        doc_coord = CoordType.UNKNOWN

        for item in data.get('ObjItems', []):
            obj = self._parse_item(item)
            if obj:
                objects.append(obj)
                if doc_coord == CoordType.UNKNOWN:
                    doc_coord = obj.coord_type

        folder = GeoFolder(name=doc_name, objects=objects)
        return GeoDocument(name=doc_name, folders=[folder], coord_type=doc_coord)

    def _parse_item(self, item: dict) -> Optional[GeoObject]:
        obj_node = item.get('Object') or {}
        geo_type = self.TYPE_MAP.get(obj_node.get('Type'))
        if geo_type is None:
            return None

        detail = obj_node.get('ObjectDetail') or {}
        name = obj_node.get('Name') or ''
        comment = obj_node.get('Comment') or None
        coord_type = CoordType.GCJ02 if detail.get('Gcj02', 0) == 1 else CoordType.CGCS2000

        coords = self._extract_coords(geo_type, detail)
        if not coords:
            return None

        return GeoObject(
            name=name, description=comment, geo_type=geo_type,
            coordinates=coords, coord_type=coord_type
        )

    def _extract_coords(self, geo_type: GeoType, detail: dict) -> List[GeoPoint]:
        if geo_type == GeoType.POINT:
            lat, lon = detail.get('Lat'), detail.get('Lng')
            if lat is None or lon is None:
                return []
            return [GeoPoint(lon=lon, lat=lat)]

        # 线/面：Latlng 为扁平的 [纬, 经, 纬, 经, ...]
        flat = detail.get('Latlng') or []
        points = []
        for i in range(0, len(flat) - 1, 2):
            points.append(GeoPoint(lon=flat[i + 1], lat=flat[i]))
        return points
