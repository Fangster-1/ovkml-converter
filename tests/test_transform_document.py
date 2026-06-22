from copy import deepcopy
from ovkml_converter.models.geo_objects import (
    CoordType, GeoType, GeoPoint, GeoObject, GeoFolder, GeoDocument,
)
from ovkml_converter.transforms.coordinate_transform import (
    transform_point, transform_document,
)


def _doc(coord_type):
    obj = GeoObject(name="p", geo_type=GeoType.POINT,
                    coordinates=[GeoPoint(lon=116.404, lat=39.915)],
                    coord_type=coord_type)
    return GeoDocument(name="d", folders=[GeoFolder(name="f", objects=[obj])],
                       coord_type=coord_type)


def test_transform_point_same_crs_identity():
    assert transform_point(116.404, 39.915, CoordType.WGS84, CoordType.WGS84) == (116.404, 39.915)


def test_transform_point_wgs84_cgcs2000_identity():
    assert transform_point(116.404, 39.915, CoordType.WGS84, CoordType.CGCS2000) == (116.404, 39.915)


def test_transform_point_gcj_to_wgs_moves():
    lon, lat = transform_point(116.404, 39.915, CoordType.GCJ02, CoordType.WGS84)
    assert (lon, lat) != (116.404, 39.915)


def test_transform_document_keep_as_is_unchanged():
    doc = _doc(CoordType.GCJ02)
    out = transform_document(doc, CoordType.UNKNOWN)
    assert out.coord_type == CoordType.GCJ02
    assert out.folders[0].objects[0].coordinates[0].lon == 116.404


def test_transform_document_relabels_and_moves():
    doc = _doc(CoordType.GCJ02)
    out = transform_document(doc, CoordType.WGS84)
    assert out.coord_type == CoordType.WGS84
    assert out.folders[0].objects[0].coord_type == CoordType.WGS84
    assert out.folders[0].objects[0].coordinates[0].lon != 116.404


def test_transform_document_does_not_mutate_input():
    doc = _doc(CoordType.GCJ02)
    snapshot = deepcopy(doc)
    transform_document(doc, CoordType.WGS84)
    assert doc.folders[0].objects[0].coordinates[0].lon == snapshot.folders[0].objects[0].coordinates[0].lon
