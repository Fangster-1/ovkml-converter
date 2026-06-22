from ..models.geo_objects import GeoDocument, GeoType, GeoObject, CoordType


class DxfWriter:
    def write(self, doc: GeoDocument, filepath: str):
        coord_type = doc.coord_type
        ct_name = coord_type.value if coord_type != CoordType.UNKNOWN else "WGS84"

        lines = []
        lines.append("0\nSECTION\n2\nHEADER")
        lines.append(f"9\n$COORDTYPE\n1\n{ct_name}")
        lines.append("0\nENDSEC")
        lines.append("0\nSECTION\n2\nTABLES\n0\nENDSEC")
        lines.append("0\nSECTION\n2\nBLOCKS\n0\nENDSEC")
        lines.append("0\nSECTION\n2\nENTITIES")

        lines.append(f"0\nTEXT\n8\nCoordinateSystem")
        lines.append(f"10\n0\n20\n0\n40\n0.001\n1\nCoordType:{ct_name}")

        for folder in doc.folders:
            for obj in folder.objects:
                if obj.geo_type == GeoType.POINT and obj.coordinates:
                    c = obj.coordinates[0]
                    lines.append(f"0\nPOINT\n8\n{folder.name}")
                    lines.append(f"10\n{c.lon}\n20\n{c.lat}\n30\n{c.alt}")
                    if obj.name:
                        lines.append(f"0\nTEXT\n8\n{folder.name}")
                        lines.append(f"10\n{c.lon}\n20\n{c.lat}")
                        lines.append(f"40\n0.001\n1\n{obj.name}")

                elif obj.geo_type == GeoType.LINE and len(obj.coordinates) >= 2:
                    points = [(c.lon, c.lat) for c in obj.coordinates]
                    lines.append(f"0\nPOLYLINE\n8\n{folder.name}\n70\n0\n66\n1")
                    lines.append(f"70\n0")
                    for x, y in points:
                        lines.append(f"0\nVERTEX\n8\n{folder.name}\n10\n{x}\n20\n{y}")
                    lines.append("0\nSEQEND")

                elif obj.geo_type == GeoType.POLYGON and len(obj.coordinates) >= 3:
                    points = [(c.lon, c.lat) for c in obj.coordinates]
                    if points[0] != points[-1]:
                        points.append(points[0])
                    lines.append(f"0\nPOLYLINE\n8\n{folder.name}\n70\n1\n66\n1")
                    for x, y in points:
                        lines.append(f"0\nVERTEX\n8\n{folder.name}\n10\n{x}\n20\n{y}")
                    lines.append("0\nSEQEND")

        lines.append("0\nENDSEC")
        lines.append("0\nEOF")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
