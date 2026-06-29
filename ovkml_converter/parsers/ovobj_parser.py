import struct
from pathlib import Path
from typing import List
from ..models.geo_objects import (
    CoordType, GeoType, GeoPoint, GeoObject, GeoFolder, GeoDocument
)


class OvobjParser:
    """解析奥维 OVOBJ（私有二进制）格式 —— 仅尽力提取点对象。

    OVOBJ 是奥维私有二进制格式，布局随版本变化、无公开文档：
      - 点对象的坐标以 小端 double 的 (纬度, 经度) 成对出现，可被定位；
      - 线/面对象的坐标采用非标准编码（实测在常规 double/float/缩放整数下均无法
        还原），无法可靠解析。

    因此本解析器只做"点对象"的尽力提取：扫描全文件中落在中国经纬度范围内、且
    紧邻成对的 (纬, 经) double，作为点输出。对象名称/分组无法从二进制可靠还原。
    **线/面数据请改用同名的 OVKML / OVKMZ / OVJSN 文件转换。**
    """

    MAGIC = b'OviO'

    # 中国大致经纬度范围（含港澳台及边境余量），用于把坐标 double 从其它字节中区分出来
    _LAT_MIN, _LAT_MAX = 18.0, 54.0
    _LON_MIN, _LON_MAX = 73.0, 136.0

    def parse(self, filepath: str) -> GeoDocument:
        with open(filepath, 'rb') as f:
            data = f.read()

        if len(data) < 16 or data[:4] != self.MAGIC:
            raise ValueError("不是有效的 OVOBJ 文件")

        doc_name = Path(filepath).stem
        coords = self._scan_points(data)

        objects = [
            GeoObject(
                name=f"点{i + 1}",
                geo_type=GeoType.POINT,
                coordinates=[GeoPoint(lon=lon, lat=lat)],
                coord_type=CoordType.UNKNOWN,
            )
            for i, (lat, lon) in enumerate(coords)
        ]

        folders = [GeoFolder(name=doc_name, objects=objects)] if objects else []
        return GeoDocument(name=doc_name, folders=folders, coord_type=CoordType.UNKNOWN)

    def _scan_points(self, data: bytes) -> List[tuple]:
        points = []
        i = 0
        n = len(data)
        while i <= n - 16:
            lat = struct.unpack('<d', data[i:i + 8])[0]
            lon = struct.unpack('<d', data[i + 8:i + 16])[0]
            if self._LAT_MIN < lat < self._LAT_MAX and self._LON_MIN < lon < self._LON_MAX:
                points.append((lat, lon))
                i += 16
            else:
                i += 1
        return points
