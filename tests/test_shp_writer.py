import shapefile
from ovkml_converter.writers.shp_writer import ShpWriter
from ovkml_converter.models.geo_objects import (
    CoordType, GeoType, GeoPoint, GeoObject, GeoFolder, GeoDocument,
)


def _point_doc():
    obj = GeoObject(name="p1", description="d", geo_type=GeoType.POINT,
                    coordinates=[GeoPoint(lon=101.1, lat=25.4)],
                    coord_type=CoordType.CGCS2000)
    return GeoDocument(name="doc", coord_type=CoordType.CGCS2000,
                       folders=[GeoFolder(name="线路A", objects=[obj])])


def test_cpg_written(tmp_path):
    ShpWriter().write(_point_doc(), str(tmp_path / "out.shp"))
    cpg = tmp_path / "out_points.cpg"
    assert cpg.exists()
    assert cpg.read_text().strip().upper() == "UTF-8"


def test_folder_field_present(tmp_path):
    ShpWriter().write(_point_doc(), str(tmp_path / "out.shp"))
    r = shapefile.Reader(str(tmp_path / "out_points.shp"))
    field_names = [f[0] for f in r.fields if f[0] != "DeletionFlag"]
    assert "FOLDER" in field_names
    assert r.record(0)["FOLDER"] == "线路A"


def test_bd09_prj(tmp_path):
    doc = _point_doc()
    doc.coord_type = CoordType.BD09
    ShpWriter().write(doc, str(tmp_path / "out.shp"))
    prj = (tmp_path / "out_points.prj").read_text()
    assert "GEOGCS" in prj
