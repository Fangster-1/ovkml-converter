import struct
from pathlib import Path
from typing import List, Tuple, Optional
from ..models.geo_objects import (
    CoordType, GeoType, GeoPoint, GeoObject, GeoFolder, GeoDocument
)


class OvobjParser:
    MAGIC = b'OviO'

    def parse(self, filepath: str) -> GeoDocument:
        with open(filepath, 'rb') as f:
            data = f.read()

        if len(data) < 16 or data[:4] != self.MAGIC:
            raise ValueError("不是有效的 OVOBJ 文件")

        doc_name = Path(filepath).stem
        coord_type = CoordType.CGCS2000

        objs_with_pos = self._extract_all_objects(data)

        folders = self._assign_to_folders(data, objs_with_pos, doc_name)

        if not folders and objs_with_pos:
            folders = [GeoFolder(name=doc_name, objects=[o for o, _ in objs_with_pos])]

        return GeoDocument(
            name=doc_name,
            folders=folders,
            coord_type=coord_type
        )

    def _extract_all_objects(self, data: bytes):
        objects = []
        i = 0
        while i < len(data) - 32:
            start = i
            obj, new_pos = self._try_parse_object(data, i)
            if obj:
                objects.append((obj, start))
                i = new_pos
            else:
                i += 1
        return objects

    def _try_parse_object(self, data: bytes, pos: int) -> Tuple[Optional[GeoObject], int]:
        if pos + 32 > len(data):
            return None, pos + 1

        lat = struct.unpack('<d', data[pos:pos+8])[0]
        lon = struct.unpack('<d', data[pos+8:pos+16])[0]

        if not (20 < lat < 55 and 70 < lon < 140):
            return None, pos + 1

        pos += 16

        if pos + 16 > len(data):
            return None, pos

        padding = struct.unpack('>I', data[pos:pos+4])[0]
        pos += 4

        obj_type = struct.unpack('>I', data[pos:pos+4])[0]
        pos += 4

        flag = struct.unpack('>I', data[pos:pos+4])[0]
        pos += 4

        name_len = struct.unpack('>I', data[pos:pos+4])[0]
        pos += 4

        if name_len > 500 or pos + name_len > len(data):
            return None, pos

        try:
            name = data[pos:pos+name_len].decode('utf-8')
        except UnicodeDecodeError:
            name = f'Object_{pos}'
        pos += name_len

        description = None
        if pos + 4 <= len(data):
            desc_len = struct.unpack('>I', data[pos:pos+4])[0]
            if 0 < desc_len < 1000 and pos + 4 + desc_len <= len(data):
                try:
                    desc_bytes = data[pos+4:pos+4+desc_len]
                    desc = desc_bytes.decode('utf-8')
                    if desc.isprintable() and not desc.isspace():
                        description = desc
                        pos += 4 + desc_len
                except UnicodeDecodeError:
                    pass

        pos = self._skip_tail(data, pos)

        geo_type = self._type_from_code(obj_type)
        coordinates = [GeoPoint(lon=lon, lat=lat)]

        return GeoObject(
            name=name,
            description=description,
            geo_type=geo_type,
            coordinates=coordinates,
            coord_type=CoordType.CGCS2000
        ), pos

    def _skip_tail(self, data: bytes, pos: int) -> int:
        if pos + 8 > len(data):
            return pos

        marker = struct.unpack('>I', data[pos:pos+4])[0]
        if marker in (0x67, 0x68, 0x69, 0xa5, 0xa7, 0xa9, 0xe5):
            pos += 4
            if pos + 4 <= len(data):
                extra = struct.unpack('>I', data[pos:pos+4])[0]
                if extra < 200:
                    pos += 4 + extra
                else:
                    pos += 4

        return pos

    def _assign_to_folders(self, data: bytes, objs_with_pos, default_name: str):
        marks = sorted(self._find_folder_names(data), key=lambda m: m[1])

        folders = []
        name_to_folder = {}

        def folder_for(name: str) -> GeoFolder:
            if name not in name_to_folder:
                f = GeoFolder(name=name, objects=[])
                name_to_folder[name] = f
                folders.append(f)
            return name_to_folder[name]

        for obj, pos in objs_with_pos:
            fname = default_name
            for name, fpos in marks:
                if fpos <= pos:
                    fname = name
                else:
                    break
            folder_for(fname).objects.append(obj)

        return folders

    def _find_folder_names(self, data: bytes) -> List[Tuple[str, int]]:
        folders = []
        for i in range(0x10, len(data) - 4):
            name_len = struct.unpack('>I', data[i:i+4])[0]
            if 3 < name_len < 50 and i + 4 + name_len <= len(data):
                try:
                    name = data[i+4:i+4+name_len].decode('utf-8')
                    chinese_count = sum(1 for c in name if '\u4e00' <= c <= '\u9fff')
                    if chinese_count >= 2:
                        folders.append((name, i))
                except UnicodeDecodeError:
                    continue
        return folders

    def _type_from_code(self, code: int) -> GeoType:
        type_map = {
            4: GeoType.POINT,
            2: GeoType.LINE,
            3: GeoType.POLYGON,
        }
        return type_map.get(code, GeoType.POINT)
