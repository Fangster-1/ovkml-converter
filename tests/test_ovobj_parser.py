from pathlib import Path
import pytest
from ovkml_converter.parsers.ovobj_parser import OvobjParser
from ovkml_converter.convert.conversion_service import convert_file
from ovkml_converter.models.geo_objects import CoordType, GeoType

FIX = Path(__file__).parent / "fixtures"


def test_ovobj_point_extracts_three_points():
    doc = OvobjParser().parse(str(FIX / "测试点.ovobj"))
    objs = doc.get_all_objects()
    assert len(objs) == 3
    assert all(o.geo_type == GeoType.POINT for o in objs)
    # 首点应与 OVKML 真值一致（纬,经）
    c = objs[0].coordinates[0]
    assert abs(c.lat - 29.67552520) < 1e-6
    assert abs(c.lon - 100.27230263) < 1e-6


def test_ovobj_point_matches_ovkml_coordinates():
    from ovkml_converter.parsers.ovkml_parser import OvkmlParser
    obj_pts = sorted(
        (round(o.coordinates[0].lat, 6), round(o.coordinates[0].lon, 6))
        for o in OvobjParser().parse(str(FIX / "测试点.ovobj")).get_all_objects()
    )
    kml_pts = sorted(
        (round(o.coordinates[0].lat, 6), round(o.coordinates[0].lon, 6))
        for o in OvkmlParser().parse(str(FIX / "测试点.ovkml")).get_all_objects()
    )
    assert obj_pts == kml_pts


def test_ovobj_line_yields_no_points():
    # 线/面 OVOBJ 坐标为非标准编码，提取不到点
    doc = OvobjParser().parse(str(FIX / "CAD多段线.ovobj"))
    assert doc.get_object_count() == 0


def test_convert_ovobj_line_raises_helpful_error(tmp_path):
    with pytest.raises(ValueError, match="OVKML"):
        convert_file(str(FIX / "CAD多段线.ovobj"), CoordType.UNKNOWN,
                     CoordType.CGCS2000, ["kml"], str(tmp_path))
