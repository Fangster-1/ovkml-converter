from ovkml_converter.convert.conversion_service import detect_ovkml_crs
from ovkml_converter.ui.main_window import crs_to_label, INPUT_CRS_LABELS
from ovkml_converter.models.geo_objects import CoordType


def test_detect_ovkml_crs_returns_detected():
    assert detect_ovkml_crs("奥维格式数据/姚安县验证B线.ovkml") == CoordType.CGCS2000


def test_detect_ovkml_crs_none_for_ovobj():
    assert detect_ovkml_crs("奥维格式数据/姚安县验证.ovobj") is None


def test_detect_ovkml_crs_none_for_missing():
    assert detect_ovkml_crs("不存在的文件.ovkml") is None


def test_crs_to_label_concrete():
    assert crs_to_label(CoordType.CGCS2000) == "CGCS2000"
    assert crs_to_label(CoordType.GCJ02) == "GCJ02"
    assert crs_to_label(CoordType.BD09) == "BD09"
    assert crs_to_label(CoordType.WGS84) == "WGS84"


def test_crs_to_label_unknown_falls_back():
    assert crs_to_label(CoordType.UNKNOWN) == "CGCS2000"


def test_input_crs_labels_are_concrete():
    assert INPUT_CRS_LABELS == ["CGCS2000", "WGS84", "GCJ02", "BD09"]
    assert "与输入坐标系一致" not in INPUT_CRS_LABELS
