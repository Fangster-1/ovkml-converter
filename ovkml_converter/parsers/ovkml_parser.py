import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List
from ..models.geo_objects import (
    CoordType, GeoType, GeoPoint, GeoObject, GeoFolder, GeoDocument
)

KML_NS = '{http://www.opengis.net/kml/2.2}'


class OvkmlParser:
    def parse(self, filepath: str) -> GeoDocument:
        tree = ET.parse(filepath)
        root = tree.getroot()

        doc_name = Path(filepath).stem
        coord_type = CoordType.UNKNOWN
        folders = []

        doc_elem = root.find(f'{KML_NS}Document')
        if doc_elem is None:
            doc_elem = root

        name_elem = doc_elem.find(f'{KML_NS}name')
        if name_elem is not None:
            doc_name = name_elem.text or doc_name

        for folder_elem in doc_elem.findall(f'{KML_NS}Folder'):
            folder = self._parse_folder(folder_elem)
            if folder.objects:
                folders.append(folder)
                if coord_type == CoordType.UNKNOWN and folder.objects:
                    coord_type = folder.objects[0].coord_type

        if not folders:
            placemarks = doc_elem.findall(f'.//{KML_NS}Placemark')
            if placemarks:
                folder = GeoFolder(name=doc_name)
                for pm in placemarks:
                    obj = self._parse_placemark(pm)
                    if obj:
                        folder.objects.append(obj)
                        if coord_type == CoordType.UNKNOWN:
                            coord_type = obj.coord_type
                folders.append(folder)

        return GeoDocument(
            name=doc_name,
            folders=folders,
            coord_type=coord_type
        )

    def _parse_folder(self, elem) -> GeoFolder:
        name = ''
        name_elem = elem.find(f'{KML_NS}name')
        if name_elem is not None:
            name = name_elem.text or ''

        objects = []
        for pm in elem.findall(f'{KML_NS}Placemark'):
            obj = self._parse_placemark(pm)
            if obj:
                objects.append(obj)

        return GeoFolder(name=name, objects=objects)

    def _parse_placemark(self, elem) -> GeoObject:
        name = ''
        name_elem = elem.find(f'{KML_NS}name')
        if name_elem is not None:
            name = name_elem.text or ''

        description = None
        desc_elem = elem.find(f'{KML_NS}description')
        if desc_elem is not None:
            description = desc_elem.text

        coord_type = CoordType.UNKNOWN
        ov_coord = elem.find(f'{KML_NS}OvCoordType')
        if ov_coord is None:
            ov_coord = elem.find('OvCoordType')
        if ov_coord is not None:
            ct = ov_coord.text.strip()
            coord_type = self._parse_coord_type(ct)

        style = self._parse_style(elem)

        attributes = {}
        ov_attr = elem.find(f'{KML_NS}OvAttr')
        if ov_attr is None:
            ov_attr = elem.find('OvAttr')
        if ov_attr is not None:
            icon = ov_attr.find(f'{KML_NS}OvIcon')
            if icon is None:
                icon = ov_attr.find('OvIcon')
            if icon is not None:
                attributes['OvIcon'] = icon.text
            icon_num = ov_attr.find(f'{KML_NS}OvIconNum')
            if icon_num is None:
                icon_num = ov_attr.find('OvIconNum')
            if icon_num is not None:
                attributes['OvIconNum'] = icon_num.text

        point_elem = elem.find(f'{KML_NS}Point')
        if point_elem is not None:
            coords = self._parse_coordinates(point_elem)
            if coords:
                return GeoObject(
                    name=name, description=description,
                    geo_type=GeoType.POINT, coordinates=coords,
                    coord_type=coord_type, style=style, attributes=attributes
                )

        line_elem = elem.find(f'{KML_NS}LineString')
        if line_elem is not None:
            coords = self._parse_coordinates(line_elem)
            if coords:
                return GeoObject(
                    name=name, description=description,
                    geo_type=GeoType.LINE, coordinates=coords,
                    coord_type=coord_type, style=style, attributes=attributes
                )

        poly_elem = elem.find(f'{KML_NS}Polygon')
        if poly_elem is not None:
            outer = poly_elem.find(f'{KML_NS}outerBoundaryIs')
            if outer is not None:
                ring = outer.find(f'{KML_NS}LinearRing')
                if ring is not None:
                    coords = self._parse_coordinates(ring)
                    if coords:
                        return GeoObject(
                            name=name, description=description,
                            geo_type=GeoType.POLYGON, coordinates=coords,
                            coord_type=coord_type, style=style, attributes=attributes
                        )

        multi = elem.find(f'{KML_NS}MultiGeometry')
        if multi is not None:
            tag_to_type = {'Point': GeoType.POINT, 'LineString': GeoType.LINE}
            for child in multi:
                tag = child.tag.replace(KML_NS, '')
                if tag in tag_to_type:
                    coords = self._parse_coordinates(child)
                    if coords:
                        return GeoObject(
                            name=name, description=description,
                            geo_type=tag_to_type[tag], coordinates=coords,
                            coord_type=coord_type, style=style, attributes=attributes
                        )
                if tag == 'Polygon':
                    outer = child.find(f'{KML_NS}outerBoundaryIs')
                    ring = outer.find(f'{KML_NS}LinearRing') if outer is not None else None
                    coords = self._parse_coordinates(ring) if ring is not None else []
                    if coords:
                        return GeoObject(
                            name=name, description=description,
                            geo_type=GeoType.POLYGON, coordinates=coords,
                            coord_type=coord_type, style=style, attributes=attributes
                        )

        return None

    def _parse_coordinates(self, elem) -> List[GeoPoint]:
        coords_elem = elem.find(f'{KML_NS}coordinates')
        if coords_elem is None:
            coords_elem = elem.find('coordinates')
        if coords_elem is None or not coords_elem.text:
            return []

        points = []
        text = coords_elem.text.strip()
        for part in text.split():
            vals = part.split(',')
            if len(vals) >= 2:
                try:
                    lon = float(vals[0])
                    lat = float(vals[1])
                    alt = float(vals[2]) if len(vals) > 2 else 0.0
                    points.append(GeoPoint(lon=lon, lat=lat, alt=alt))
                except ValueError:
                    continue
        return points

    def _parse_coord_type(self, text: str) -> CoordType:
        text = text.upper()
        if 'CGCS2000' in text or '2000' in text:
            return CoordType.CGCS2000
        elif 'GCJ02' in text or 'GCJ' in text:
            return CoordType.GCJ02
        elif 'WGS84' in text or 'WGS' in text:
            return CoordType.WGS84
        elif 'BD09' in text or 'BD' in text or '百度' in text:
            return CoordType.BD09
        return CoordType.UNKNOWN

    def _parse_style(self, elem) -> dict:
        style = {}
        style_elem = elem.find(f'{KML_NS}Style')
        if style_elem is None:
            return style

        icon_style = style_elem.find(f'{KML_NS}IconStyle')
        if icon_style is not None:
            color = icon_style.find(f'{KML_NS}color')
            if color is not None:
                style['icon_color'] = color.text
            icon = icon_style.find(f'{KML_NS}Icon/{KML_NS}href')
            if icon is not None:
                style['icon_href'] = icon.text

        line_style = style_elem.find(f'{KML_NS}LineStyle')
        if line_style is not None:
            color = line_style.find(f'{KML_NS}color')
            if color is not None:
                style['line_color'] = color.text
            width = line_style.find(f'{KML_NS}width')
            if width is not None:
                style['line_width'] = width.text

        poly_style = style_elem.find(f'{KML_NS}PolyStyle')
        if poly_style is not None:
            color = poly_style.find(f'{KML_NS}color')
            if color is not None:
                style['poly_color'] = color.text

        return style
