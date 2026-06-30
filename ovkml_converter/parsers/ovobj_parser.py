import struct
from pathlib import Path
from typing import List, Optional, Tuple
from ..models.geo_objects import (
    CoordType, GeoType, GeoPoint, GeoObject, GeoFolder, GeoDocument
)


class OvobjParser:
    """解析奥维 OVOBJ（私有二进制）格式 —— 仅尽力提取点对象。

    OVOBJ 是奥维私有二进制格式，布局随版本变化、无公开文档。经逆向实测：
      - 点对象坐标以 小端 double 的 (纬度, 经度) 成对出现，可被定位；
      - 点对象图标 ID 位于坐标 lat double 起点后偏移 +20 处的 小端 int32；
      - 对象名称以 Pascal 串存储（1 字节长度前缀 + UTF-8 字节），可全局扫描提取；
      - 线/面对象坐标采用非标准压缩编码（double/float/varint/定点/delta 均无法还原），
        无法可靠解析。

    因此本解析器只做"点对象"的尽力提取：扫描全文件中落在中国经纬度范围内、且
    紧邻成对的 (纬, 经) double 作为点坐标，并尽量还原图标 ID 与名称。
    **线/面数据请改用同名的 OVKML / OVKMZ / OVJSN 文件转换。**
    """

    MAGIC = b'OviO'

    # 中国大致经纬度范围（含港澳台及边境余量），用于把坐标 double 从其它字节中区分出来。
    # 纬度下限与坐标转换 out_of_china 的 3.86 对齐，覆盖南海等边境点。
    _LAT_MIN, _LAT_MAX = 3.86, 54.0
    _LON_MIN, _LON_MAX = 73.0, 136.0

    # 点对象图标 int32 相对坐标 lat double 起点的偏移（lat8 + lon8 + 4 字节间隔）
    _ICON_OFFSET = 20

    def parse(self, filepath: str) -> GeoDocument:
        with open(filepath, 'rb') as f:
            data = f.read()

        if len(data) < 16 or data[:4] != self.MAGIC:
            raise ValueError("不是有效的 OVOBJ 文件")

        doc_name = Path(filepath).stem
        hits = self._scan_point_hits(data)
        names = self._scan_pascal_names(data)

        objects: List[GeoObject] = []
        for i, (lat, lon, icon, coord_off) in enumerate(hits):
            name = names[i] if i < len(names) else f"点{i + 1}"
            attributes = {'OvIcon': str(icon)} if icon is not None else None
            objects.append(GeoObject(
                name=name,
                geo_type=GeoType.POINT,
                coordinates=[GeoPoint(lon=lon, lat=lat)],
                coord_type=CoordType.UNKNOWN,
                attributes=attributes,
            ))

        folders = [GeoFolder(name=doc_name, objects=objects)] if objects else []
        return GeoDocument(name=doc_name, folders=folders, coord_type=CoordType.UNKNOWN)

    def _scan_point_hits(self, data: bytes) -> List[Tuple[float, float, Optional[int], int]]:
        """扫描成对 (lat, lon) double，并尝试读取其后的图标 int32。

        返回 [(lat, lon, icon_or_None, coord_lat_offset), ...]。
        """
        hits = []
        i = 0
        n = len(data)
        while i <= n - 16:
            lat = struct.unpack('<d', data[i:i + 8])[0]
            lon = struct.unpack('<d', data[i + 8:i + 16])[0]
            if self._LAT_MIN < lat < self._LAT_MAX and self._LON_MIN < lon < self._LON_MAX:
                icon = self._read_icon(data, i)
                hits.append((lat, lon, icon, i))
                i += 16
            else:
                i += 1
        return hits

    def _read_icon(self, data: bytes, coord_off: int) -> Optional[int]:
        """读取坐标 lat double 起点后偏移 +20 处的小端 int32 作为图标 ID。

        仅当值落在合理范围（奥维图标编号通常为小正整数）才返回，否则返回 None。
        """
        pos = coord_off + self._ICON_OFFSET
        if pos + 4 > len(data):
            return None
        icon = struct.unpack('<I', data[pos:pos + 4])[0]
        # 奥维图标编号为小正整数；过滤明显非图标的大值（如对齐填充 0 也允许，写时再判）
        return icon if icon < 0x10000 else None

    def _scan_pascal_names(self, data: bytes) -> List[str]:
        """扫描全文件的 Pascal 串名称（1 字节长度前缀 + UTF-8 字节）。

        OVOBJ 把对象名称以"长度前缀 + UTF-8"存储。本方法提取所有合法的此类字符串，
        按出现顺序返回。点对象名称为空时不会产生命中（长度前缀 0 被跳过），
        调用方按索引与点配对，配不上时回落到"点N"。
        """
        names = []
        i = 0
        n = len(data)
        while i < n:
            lb = data[i]
            if 1 <= lb <= 64 and i + 1 + lb <= n:
                try:
                    s = data[i + 1:i + 1 + lb].decode('utf-8')
                    if s and all(c.isprintable() for c in s):
                        names.append(s)
                        i += 1 + lb
                        continue
                except UnicodeDecodeError:
                    pass
            i += 1
        return names
