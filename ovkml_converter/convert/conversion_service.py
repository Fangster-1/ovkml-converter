from pathlib import Path

from ..parsers import OvkmlParser, OvobjParser
from ..writers import KmlWriter, ShpWriter, DxfWriter
from ..transforms.coordinate_transform import transform_document, out_of_china
from ..models.geo_objects import CoordType, GeoDocument


def resolve_source_crs(filepath, parsed_doc, ovobj_src_crs, sibling_files):
    ext = Path(filepath).suffix.lower()
    if ext == ".ovkml":
        if parsed_doc.coord_type != CoordType.UNKNOWN:
            return parsed_doc.coord_type
        return ovobj_src_crs
    stem = Path(filepath).stem
    for sf in sibling_files or []:
        sp = Path(sf)
        if sp.suffix.lower() == ".ovkml" and sp.stem == stem and sp.exists():
            try:
                sib = OvkmlParser().parse(str(sp))
                if sib.coord_type != CoordType.UNKNOWN:
                    return sib.coord_type
            except Exception:
                pass
    same_dir = Path(filepath).with_suffix(".ovkml")
    if same_dir.exists():
        try:
            sib = OvkmlParser().parse(str(same_dir))
            if sib.coord_type != CoordType.UNKNOWN:
                return sib.coord_type
        except Exception:
            pass
    return ovobj_src_crs


def detect_ovkml_crs(filepath):
    """OVKML 文件返回其检测到的坐标系（读 OvCoordType）；OVOBJ 或检测失败返回 None。

    供 UI 在添加文件时自动回填"输入坐标系"下拉用。
    """
    if Path(filepath).suffix.lower() != ".ovkml":
        return None
    try:
        doc = OvkmlParser().parse(filepath)
        if doc.coord_type != CoordType.UNKNOWN:
            return doc.coord_type
    except Exception:
        pass
    return None


def _stamp_source(doc: GeoDocument, src: CoordType, override_all: bool) -> None:
    for folder in doc.folders:
        for obj in folder.objects:
            if override_all or obj.coord_type == CoordType.UNKNOWN:
                obj.coord_type = src
    doc.coord_type = src


def _crs_class(crs: CoordType):
    if crs in (CoordType.WGS84, CoordType.CGCS2000):
        return "wgs"
    return crs


def _any_in_china(doc: GeoDocument) -> bool:
    for folder in doc.folders:
        for obj in folder.objects:
            for p in obj.coordinates:
                if not out_of_china(p.lon, p.lat):
                    return True
    return False


def convert_file(filepath, target_crs, ovobj_src_crs, formats, out_dir, sibling_files=None):
    ext = Path(filepath).suffix.lower()
    if ext == ".ovkml":
        doc = OvkmlParser().parse(filepath)
    elif ext == ".ovobj":
        doc = OvobjParser().parse(filepath)
    else:
        raise ValueError(f"不支持的格式: {ext}")

    src = resolve_source_crs(filepath, doc, ovobj_src_crs, sibling_files)
    _stamp_source(doc, src, override_all=(ext == ".ovobj"))

    in_china = _any_in_china(doc)
    out_doc = transform_document(doc, target_crs)
    effective_target = src if target_crs == CoordType.UNKNOWN else target_crs

    stem = Path(filepath).stem
    out = Path(out_dir)
    if "kml" in formats:
        KmlWriter().write(out_doc, str(out / f"{stem}.kml"))
    if "shp" in formats:
        ShpWriter().write(out_doc, str(out / f"{stem}.shp"))
    if "dxf" in formats:
        DxfWriter().write(out_doc, str(out / f"{stem}.dxf"))

    needs_offset = (target_crs != CoordType.UNKNOWN
                    and _crs_class(src) != _crs_class(effective_target))
    return {
        "source_crs": src,
        "target_crs": effective_target,
        "out_of_china": (needs_offset and not in_china),
    }
