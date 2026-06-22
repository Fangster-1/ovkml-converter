from pathlib import Path
from ovkml_converter.convert.conversion_service import resolve_source_crs, convert_file
from ovkml_converter.parsers.ovobj_parser import OvobjParser
from ovkml_converter.models.geo_objects import CoordType

OVOBJ = "奥维格式数据/姚安县验证.ovobj"
OVKML = "奥维格式数据/姚安县验证B线.ovkml"


def test_resolve_ovkml_uses_detected():
    from ovkml_converter.parsers.ovkml_parser import OvkmlParser
    doc = OvkmlParser().parse(OVKML)
    crs = resolve_source_crs(OVKML, doc, CoordType.WGS84, None)
    assert crs == CoordType.CGCS2000


def test_resolve_ovobj_uses_default_without_sibling():
    doc = OvobjParser().parse(OVOBJ)
    crs = resolve_source_crs(OVOBJ, doc, CoordType.WGS84, None)
    assert crs == CoordType.WGS84


def test_resolve_ovobj_sibling_fallback():
    doc = OvobjParser().parse(OVOBJ)
    sibling = "奥维格式数据/姚安县验证.ovkml"
    crs = resolve_source_crs(OVOBJ, doc, CoordType.WGS84, [OVOBJ, sibling])
    assert crs in (CoordType.CGCS2000, CoordType.WGS84)


def test_convert_file_keep_as_is_writes_kml(tmp_path):
    res = convert_file(OVKML, CoordType.UNKNOWN, CoordType.CGCS2000,
                       ["kml"], str(tmp_path))
    assert res["source_crs"] == CoordType.CGCS2000
    assert res["target_crs"] == CoordType.CGCS2000
    assert (tmp_path / "姚安县验证B线.kml").exists()


def test_convert_file_transform_changes_coords(tmp_path):
    res = convert_file(OVKML, CoordType.WGS84, CoordType.CGCS2000,
                       ["kml"], str(tmp_path))
    assert res["target_crs"] == CoordType.WGS84
