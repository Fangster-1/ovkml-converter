from ovkml_converter.models.geo_objects import CoordType


def test_bd09_coordtype_exists():
    assert CoordType.BD09.value == "BD09"
