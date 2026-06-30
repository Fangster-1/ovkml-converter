from ..models.geo_objects import GeoDocument, GeoType, CoordType


class DxfWriter:
    def write(self, doc: GeoDocument, filepath: str):
        ct = doc.coord_type
        ct_name = ct.value if ct != CoordType.UNKNOWN else "WGS84"

        layer_names = []
        for folder in doc.folders:
            if folder.name and folder.name not in layer_names:
                layer_names.append(folder.name)
        for special in ("CoordinateSystem",):
            if special not in layer_names:
                layer_names.append(special)

        lines = []
        lines.append("0\nSECTION\n2\nHEADER")
        lines.append("9\n$ACADVER\n1\nAC1009")
        lines.append(f"9\n$COORDTYPE\n1\n{ct_name}")
        lines.append("0\nENDSEC")
        lines.append("0\nSECTION\n2\nTABLES")
        lines.append(f"0\nTABLE\n2\nLAYER\n70\n{len(layer_names)}")
        for name in layer_names:
            lines.append(f"0\nLAYER\n2\n{name}\n70\n0\n62\n7\n6\nCONTINUOUS")
        lines.append("0\nENDTAB")
        lines.append("0\nENDSEC")
        lines.append("0\nSECTION\n2\nBLOCKS\n0\nENDSEC")
        lines.append("0\nSECTION\n2\nENTITIES")
        lines.append("0\nTEXT\n8\nCoordinateSystem")
        lines.append(f"10\n0\n20\n0\n40\n0.001\n1\nCoordType:{ct_name}")

        for folder in doc.folders:
            layer = folder.name or "0"
            for obj in folder.objects:
                if obj.geo_type == GeoType.POINT and obj.coordinates:
                    c = obj.coordinates[0]
                    lines.append(f"0\nPOINT\n8\n{layer}")
                    lines.append(f"10\n{c.lon}\n20\n{c.lat}\n30\n{c.alt}")
                    if obj.name:
                        lines.append(f"0\nTEXT\n8\n{layer}")
                        lines.append(f"10\n{c.lon}\n20\n{c.lat}")
                        lines.append(f"40\n0.001\n1\n{obj.name}")
                elif obj.geo_type == GeoType.LINE and len(obj.coordinates) >= 2:
                    lines.append(f"0\nPOLYLINE\n8\n{layer}\n70\n0\n66\n1")
                    for c in obj.coordinates:
                        lines.append(f"0\nVERTEX\n8\n{layer}\n10\n{c.lon}\n20\n{c.lat}\n30\n{c.alt}")
                    lines.append("0\nSEQEND")
                elif obj.geo_type == GeoType.POLYGON and len(obj.coordinates) >= 3:
                    pts = obj.coordinates[:]
                    if pts[0] != pts[-1]:
                        pts.append(pts[0])
                    lines.append(f"0\nPOLYLINE\n8\n{layer}\n70\n1\n66\n1")
                    for c in pts:
                        lines.append(f"0\nVERTEX\n8\n{layer}\n10\n{c.lon}\n20\n{c.lat}\n30\n{c.alt}")
                    lines.append("0\nSEQEND")

        lines.append("0\nENDSEC")
        lines.append("0\nEOF")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
