from ovkml_converter.writers.dxf_writer import DxfWriter
from ovkml_converter.models.geo_objects import (
    CoordType, GeoType, GeoPoint, GeoObject, GeoFolder, GeoDocument,
)


def _doc():
    obj = GeoObject(name="p1", geo_type=GeoType.POINT,
                    coordinates=[GeoPoint(lon=101.1, lat=25.4)],
                    coord_type=CoordType.CGCS2000)
    return GeoDocument(name="doc", coord_type=CoordType.CGCS2000,
                       folders=[GeoFolder(name="线路A", objects=[obj])])


def test_has_acadver(tmp_path):
    out = tmp_path / "o.dxf"
    DxfWriter().write(_doc(), str(out))
    text = out.read_text(encoding="utf-8")
    assert "$ACADVER" in text


def test_layer_table_defines_folder(tmp_path):
    out = tmp_path / "o.dxf"
    DxfWriter().write(_doc(), str(out))
    text = out.read_text(encoding="utf-8")
    assert "TABLE\n2\nLAYER" in text
    assert "0\nLAYER\n2\n线路A" in text
