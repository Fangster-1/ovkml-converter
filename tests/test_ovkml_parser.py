import xml.etree.ElementTree as ET
from pathlib import Path
from ovkml_converter.parsers.ovkml_parser import OvkmlParser
from ovkml_converter.models.geo_objects import CoordType, GeoType

FIX = Path(__file__).parent / "fixtures"


def test_parse_coord_type_bd09():
    p = OvkmlParser()
    assert p._parse_coord_type("BD09") == CoordType.BD09
    assert p._parse_coord_type("百度") == CoordType.BD09


def test_multigeometry_line_parsed():
    xml = (
        '<Placemark xmlns="http://www.opengis.net/kml/2.2"><name>L</name>'
        '<MultiGeometry><LineString><coordinates>1,2,0 3,4,0</coordinates>'
        '</LineString></MultiGeometry></Placemark>'
    )
    elem = ET.fromstring(xml)
    obj = OvkmlParser()._parse_placemark(elem)
    assert obj is not None
    assert obj.geo_type == GeoType.LINE
    assert len(obj.coordinates) == 2


def test_point_sample_parses():
    doc = OvkmlParser().parse(str(FIX / "测试点.ovkml"))
    assert doc.get_object_count() == 3
    assert doc.coord_type == CoordType.CGCS2000
    assert all(o.geo_type == GeoType.POINT for o in doc.get_all_objects())


def test_polygon_sample_parses():
    doc = OvkmlParser().parse(str(FIX / "多边形.ovkml"))
    objs = doc.get_all_objects()
    assert len(objs) == 1
    assert objs[0].geo_type == GeoType.POLYGON
    assert len(objs[0].coordinates) == 5  # 闭合环（首尾相同）
