from ovkml_converter.ui.main_window import CRS_LABELS, label_to_crs
from ovkml_converter.models.geo_objects import CoordType


def test_crs_labels_contain_keep_as_is():
    assert "与输入坐标系一致" in CRS_LABELS


def test_label_to_crs_mapping():
    assert label_to_crs("与输入坐标系一致") == CoordType.UNKNOWN
    assert label_to_crs("WGS84") == CoordType.WGS84
    assert label_to_crs("GCJ02") == CoordType.GCJ02
    assert label_to_crs("BD09") == CoordType.BD09
    assert label_to_crs("CGCS2000") == CoordType.CGCS2000
