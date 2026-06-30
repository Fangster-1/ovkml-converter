from pathlib import Path
from ovkml_converter.convert.conversion_service import parse_input
from ovkml_converter.parsers.ovjsn_parser import OvjsnParser
from ovkml_converter.models.geo_objects import CoordType, GeoType

FIX = Path(__file__).parent / "fixtures"


# ---------- OVJSN ----------

def test_ovjsn_point():
    doc = OvjsnParser().parse(str(FIX / "测试点.ovjsn"))
    objs = doc.get_all_objects()
    assert len(objs) == 3
    assert all(o.geo_type == GeoType.POINT for o in objs)
    assert doc.coord_type == CoordType.CGCS2000
    c = objs[0].coordinates[0]
    assert abs(c.lat - 29.67552520) < 1e-6 and abs(c.lon - 100.27230263) < 1e-6


def test_ovjsn_extracts_attribute_table():
    # 奥维记录的属性表内容（ObjID/修改时间/创建时间）应被提取，供 GIS 属性表显示
    objs = OvjsnParser().parse(str(FIX / "测试点.ovjsn")).get_all_objects()
    a = objs[0].attributes
    assert a["ObjID"] == "464016062"
    assert a["tmModify"] == "2026/06/25 16:12:18"
    assert a["Time"] == "2026/06/25 16:12:21"


def test_ovjsn_line():
    objs = OvjsnParser().parse(str(FIX / "CAD多段线.ovjsn")).get_all_objects()
    assert len(objs) == 1
    assert objs[0].geo_type == GeoType.LINE
    assert len(objs[0].coordinates) == 5


def test_ovjsn_polygon():
    objs = OvjsnParser().parse(str(FIX / "多边形.ovjsn")).get_all_objects()
    assert len(objs) == 1
    assert objs[0].geo_type == GeoType.POLYGON
    assert len(objs[0].coordinates) == 4  # OVJSN 不闭合，4 个顶点


# ---------- OVKMZ ----------

def test_ovkmz_equals_ovkml():
    # OVKMZ 是 OVKML 的 zip，解析结果应与 OVKML 完全一致
    for stem in ("测试点", "CAD多段线", "多边形"):
        kml = parse_input(str(FIX / f"{stem}.ovkml"))
        kmz = parse_input(str(FIX / f"{stem}.ovkmz"))
        assert kmz.get_object_count() == kml.get_object_count()
        for a, b in zip(kmz.get_all_objects(), kml.get_all_objects()):
            assert a.geo_type == b.geo_type
            assert len(a.coordinates) == len(b.coordinates)
            assert abs(a.coordinates[0].lon - b.coordinates[0].lon) < 1e-9


def test_ovkmz_line_geometry():
    objs = parse_input(str(FIX / "CAD多段线.ovkmz")).get_all_objects()
    assert len(objs) == 1 and objs[0].geo_type == GeoType.LINE
    assert len(objs[0].coordinates) == 5


# ---------- 跨格式一致性 ----------

def test_line_coords_consistent_across_formats():
    def coords(path):
        objs = parse_input(path).get_all_objects()
        line = [o for o in objs if o.geo_type == GeoType.LINE][0]
        return [(round(p.lat, 6), round(p.lon, 6)) for p in line.coordinates]

    kml = coords(str(FIX / "CAD多段线.ovkml"))
    ovjsn = coords(str(FIX / "CAD多段线.ovjsn"))
    assert kml == ovjsn  # OVKML 与 OVJSN 的线坐标逐点一致
