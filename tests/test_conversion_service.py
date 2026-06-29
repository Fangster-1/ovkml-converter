import shutil
from pathlib import Path
from ovkml_converter.convert.conversion_service import (
    resolve_source_crs, convert_file, parse_input,
)
from ovkml_converter.models.geo_objects import CoordType

FIX = Path(__file__).parent / "fixtures"
OVOBJ = str(FIX / "测试点.ovobj")
OVKML = str(FIX / "测试点.ovkml")


def test_resolve_text_format_uses_detected():
    doc = parse_input(OVKML)
    crs = resolve_source_crs(OVKML, doc, CoordType.WGS84, None)
    assert crs == CoordType.CGCS2000


def test_resolve_ovobj_uses_default_without_sibling(tmp_path):
    # 把 ovobj 单独拷到无同名文本格式的目录，确认回落到手动默认值
    lone = tmp_path / "孤立点.ovobj"
    shutil.copy(OVOBJ, lone)
    doc = parse_input(str(lone))
    crs = resolve_source_crs(str(lone), doc, CoordType.WGS84, None)
    assert crs == CoordType.WGS84


def test_resolve_ovobj_sibling_fallback(tmp_path):
    # 同目录存在同名 ovkml 时，自动借用其坐标系
    shutil.copy(OVOBJ, tmp_path / "测试点.ovobj")
    shutil.copy(OVKML, tmp_path / "测试点.ovkml")
    target = str(tmp_path / "测试点.ovobj")
    doc = parse_input(target)
    crs = resolve_source_crs(target, doc, CoordType.WGS84, None)
    assert crs == CoordType.CGCS2000


def test_convert_file_keep_as_is_writes_kml(tmp_path):
    res = convert_file(OVKML, CoordType.UNKNOWN, CoordType.CGCS2000,
                       ["kml"], str(tmp_path))
    assert res["source_crs"] == CoordType.CGCS2000
    assert res["target_crs"] == CoordType.CGCS2000
    assert (tmp_path / "测试点.kml").exists()


def test_convert_file_cgcs2000_to_wgs84_relabels(tmp_path):
    res = convert_file(OVKML, CoordType.WGS84, CoordType.CGCS2000,
                       ["kml"], str(tmp_path))
    assert res["target_crs"] == CoordType.WGS84


from ovkml_converter.convert.conversion_service import _stamp_source, _crs_class
from ovkml_converter.models.geo_objects import GeoType, GeoPoint, GeoObject, GeoFolder, GeoDocument


def test_stamp_source_preserves_known_object_crs():
    known = GeoObject(name="k", geo_type=GeoType.POINT,
                      coordinates=[GeoPoint(lon=1, lat=2)], coord_type=CoordType.GCJ02)
    unknown = GeoObject(name="u", geo_type=GeoType.POINT,
                        coordinates=[GeoPoint(lon=1, lat=2)], coord_type=CoordType.UNKNOWN)
    doc = GeoDocument(name="d", coord_type=CoordType.UNKNOWN,
                      folders=[GeoFolder(name="f", objects=[known, unknown])])
    _stamp_source(doc, CoordType.WGS84, override_all=False)
    assert known.coord_type == CoordType.GCJ02
    assert unknown.coord_type == CoordType.WGS84
    assert doc.coord_type == CoordType.WGS84


def test_stamp_source_override_all():
    o = GeoObject(name="o", geo_type=GeoType.POINT,
                  coordinates=[GeoPoint(lon=1, lat=2)], coord_type=CoordType.CGCS2000)
    doc = GeoDocument(name="d", coord_type=CoordType.CGCS2000,
                      folders=[GeoFolder(name="f", objects=[o])])
    _stamp_source(doc, CoordType.GCJ02, override_all=True)
    assert o.coord_type == CoordType.GCJ02


def test_crs_class_wgs_equivalence():
    assert _crs_class(CoordType.WGS84) == _crs_class(CoordType.CGCS2000)
    assert _crs_class(CoordType.GCJ02) != _crs_class(CoordType.WGS84)
    assert _crs_class(CoordType.BD09) != _crs_class(CoordType.GCJ02)
