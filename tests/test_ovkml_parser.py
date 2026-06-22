import xml.etree.ElementTree as ET
from ovkml_converter.parsers.ovkml_parser import OvkmlParser
from ovkml_converter.models.geo_objects import CoordType, GeoType


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


def test_existing_sample_still_parses():
    doc = OvkmlParser().parse("奥维格式数据/姚安县验证B线.ovkml")
    assert doc.get_object_count() == 32
    assert doc.coord_type == CoordType.CGCS2000
