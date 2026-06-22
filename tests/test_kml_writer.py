from ovkml_converter.writers.kml_writer import KmlWriter
from ovkml_converter.models.geo_objects import (
    CoordType, GeoType, GeoPoint, GeoObject, GeoFolder, GeoDocument,
)


def test_kml_has_encoding_declaration(tmp_path):
    obj = GeoObject(name="p", geo_type=GeoType.POINT,
                    coordinates=[GeoPoint(lon=101.1, lat=25.4)],
                    coord_type=CoordType.CGCS2000)
    doc = GeoDocument(name="d", coord_type=CoordType.CGCS2000,
                      folders=[GeoFolder(name="f", objects=[obj])])
    out = tmp_path / "o.kml"
    KmlWriter().write(doc, str(out))
    first = out.read_text(encoding="utf-8").splitlines()[0]
    assert "encoding=" in first.lower()
    assert "utf-8" in first.lower()
