""" base classes for creating SVG files """
import math
from base64 import b64encode
from html import escape
from mimetypes import guess_type
from pathlib import Path
from textwrap import indent
from typing import Optional, Self

from svg_timeline.svg_style_defaults import DEFAULT_CSS, ColorPalette, DEFAULT_COLORS
from svg_timeline.vectors import Vector


_INDENT = 2 * ' '


class SvgElement:
    """ general class for describing an element in an SVG and transforming it into
    its XML representation for saving it """
    def __init__(self, tag: str,
                 attributes: Optional[dict[str, str]] = None,
                 content: Optional[str] = None,
                 classes: Optional[list[str]] = None,
                 ):
        self._tag = tag
        self._attributes = attributes or {}
        self._content = content
        self._add_classes(classes)

    @property
    def tag(self) -> str:
        """ the element's tag as a string """
        return self._tag

    def _add_classes(self, classes: Optional[list[str]] = None) -> None:
        """ add new classes to the element's attributes """
        if classes is None or len(classes) == 0:
            return
        if 'class' not in self._attributes:
            self._attributes['class'] = ' '.join(classes)
            return
        for class_name in classes:
            if class_name in self._attributes['class']:
                continue
            self._attributes['class'] += ' ' + class_name

    @property
    def attributes(self) -> dict[str, str]:
        """ dictionary of the element's attributes """
        return self._attributes

    @property
    def classes(self) -> list[str]:
        """ list of the element's classes """
        if 'class' in self._attributes:
            return self._attributes['class'].split(' ')
        return []

    @property
    def content(self) -> Optional[str]:
        """ the element's content as a string """
        return self._content

    def __str__(self) -> str:
        svg_element = f'<{self.tag}'
        for key, value in self.attributes.items():
            svg_element += f' {key}="{escape(value)}"'
        if self.content is not None:
            svg_element += f'>{self.content}</{self.tag}>'
        else:
            svg_element += ' />'
        return svg_element


class CascadeStyleSheet(dict):
    """ basic representation of a CSS """
    def __init__(self, custom_entries: Optional[dict] = None):
        super().__init__(DEFAULT_CSS)
        if custom_entries is not None:
            self.update(custom_entries)
        self.full_validate()
        self._used_color_palette: Optional[ColorPalette] = None

    def full_validate(self):
        """ check that the object represents valid CSS """
        for key, value in self.items():
            self.__validate_one_entry(key, value)

    def __setitem__(self, key, value):
        self.__validate_one_entry(key, value)
        super().__setitem__(key, value)

    @staticmethod
    def __validate_one_entry(key, value):
        if not isinstance(key, str):
            raise TypeError(f"Invalid key {key}. All CSS keys must be strings.")
        if not isinstance(value, dict):
            raise TypeError(f"Invalid entry for key {key}. All CSS entries must be dicts.")
        for sub_key, sub_value in value.items():
            if not isinstance(sub_key, str):
                raise TypeError(f"Invalid subkey {sub_key} in entry {key}. All CSS keys must be strings.")
            if not isinstance(sub_value, str):
                raise TypeError(f"Invalid value for {sub_key} in entry {key}. All CSS values must be strings.")

    def compile(self, indent='', line_break='\n') -> str:
        """ compile the contained style definition into a css file """
        if self._used_color_palette is None:
            self.set_color_palette(DEFAULT_COLORS)
        css_section = f'{line_break or " "}'
        for selector, props in self.items():
            css_section += f'{selector} {{{line_break}'
            css_section += f'{line_break or " "}'.join(
                f'{indent}{name}: {value};' for name, value in props.items()
            )
            css_section += f'{line_break or " "}}}{line_break or " "}'
        return css_section

    def set_color_palette(self, palette: ColorPalette) -> None:
        """ add CSS entries for all colors in the given palette """
        if self._used_color_palette is not None:
            raise RuntimeError("Color palette was already set on this CascadeStyleSheet")
        for i, color in enumerate(palette):
            self[f'.colored.c{i:02}'] = {
                'stroke': color.color,
                'fill': color.color,
            }
            self[f'.top_text.c{i:02}'] = {
                'fill': color.top_text_color,
            }
        self._used_color_palette = palette


class SvgFile:
    """ representation of an SVG file used to collect the contained elements
    and save them into a .svg along with the necessary meta-data
    """
    def __init__(self, width: int, height: int,
                 css: Optional[CascadeStyleSheet] = None,
                 elements: Optional[list[SvgElement]] = None,
                 definitions: Optional[list[SvgElement]] = None):
        self.width = width
        self.height = height
        self.css = css or CascadeStyleSheet()
        self.elements = elements or []
        self.defs = definitions or []

    @property
    def header(self) -> str:
        """ first lines of the .svg file """
        width, height = int(self.width), int(self.height)
        view_x, view_y = 0, 0
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"',
            f'     width="{width}" height="{height}" viewBox="{view_x} {view_y} {width} {height}">',
        ]
        return '\n'.join(lines) + '\n'

    @property
    def style_section(self) -> str:
        """ style section lines of the .svg file """
        style_section = '<style>'
        style_section += self.css.compile(indent='  ', line_break='\n')
        style_section += '</style>\n'
        return style_section

    @property
    def defs_section(self) -> str:
        """ definition section lines of the .svg file """
        defs_section = ''
        if len(self.defs) > 0:
            defs_section += '<defs>\n'
            defs_section += ''.join(_INDENT + str(element) + '\n'
                                    for element in self.defs)
            defs_section += '</defs>\n'
        return defs_section

    @property
    def element_section(self) -> str:
        """ main elements section lines of the .svg file """
        element_section = ''.join(str(element) + '\n'
                                  for element in self.elements)
        return element_section

    @property
    def footer(self) -> str:
        """ last lines of the .svg file """
        return '</svg>\n'

    @property
    def full(self) -> str:
        """ the full raw .svg file """
        full = self.header
        full += self.style_section
        full += self.defs_section
        full += self.element_section
        full += self.footer
        return full

    def save_as(self, file_path: Path) -> None:
        """ save the SVG under given file path """
        with open(file_path, 'w', encoding='utf-8') as out_file:
            out_file.write(self.full)


class Line(SvgElement):
    """ straight line from one point to another """
    def __init__(self, source: Vector, target: Vector, classes: Optional[list[str]] = None):
        super().__init__(tag='path', classes=classes)
        self.source = source
        self.target = target
        self._update_attributes()

    def _update_attributes(self) -> None:
        self._attributes.update({
            'd': f'M{self.source.x},{self.source.y} L{self.target.x},{self.target.y}'
        })


class Text(SvgElement):
    """ text at a fixed position on the canvas """
    def __init__(self, coord: Vector, text: str, classes: Optional[list[str]] = None):
        super().__init__(tag='text', content=escape(text), classes=classes)
        self.coord = coord
        self._update_attributes()

    def _update_attributes(self) -> None:
        self._attributes.update({
            'x': str(self.coord.x),
            'y': str(self.coord.y),
        })


class Rectangle(SvgElement):
    """ rectangle filled with the given color """
    def __init__(self, corner1: Vector, corner2: Vector, classes: Optional[list[str]] = None):
        super().__init__(tag='rect', classes=classes)
        self.corner1 = corner1
        self.corner2 = corner2
        self._update_attributes()

    def _update_attributes(self) -> None:
        self._attributes.update({
            'x': str(min(self.corner1.x, self.corner2.x)),
            'y': str(min(self.corner1.y, self.corner2.y)),
            'width': str(math.fabs(self.corner1.x - self.corner2.x)),
            'height': str(math.fabs(self.corner1.y - self.corner2.y)),
        })


class Circle(SvgElement):
    """ circle filled with the given color """
    def __init__(self, center: Vector, radius: float, classes: Optional[list[str]] = None):
        super().__init__(tag='circle', classes=classes)
        self.center = center
        self.radius = radius
        self._update_attributes()

    def _update_attributes(self) -> None:
        self._attributes.update({
            'cx': str(self.center.x),
            'cy': str(self.center.y),
            'r': str(self.radius),
        })


class Image(SvgElement):
    """ SVG embedding of the image found at the given file path """
    def __init__(self, top_left: Vector, width: float, height: float,
                 xlink_href: str, classes: Optional[list[str]] = None):
        super().__init__(tag='image', classes=classes)
        self.top_left = top_left
        self.width = width
        self.height = height
        self.xlink_href = xlink_href
        self._update_attributes()

    def _update_attributes(self) -> None:
        self._attributes.update({
            'x': str(self.top_left.x),
            'y': str(self.top_left.y),
            'width': str(self.width),
            'height': str(self.height),
            'xlink:href': self.xlink_href,
        })

    @staticmethod
    def xlink_href_from_file_path(file: Path) -> str:
        """ determine the data representation of the image from its path """
        mimetype, encoding = guess_type(file)
        with open(file, 'rb', encoding=encoding) as image_file:
            image_data = b64encode(image_file.read())
        xlink_href = f'data:{mimetype};base64,{image_data.decode()}'
        return xlink_href

    @classmethod
    def from_path(cls, top_left: Vector, width: float, height: float,
                  file_path: Path, classes: Optional[list[str]] = None) -> Self:
        """ generate an instance from a file path instead of the data """
        xlink_href = cls.xlink_href_from_file_path(file_path)
        return cls(top_left, width, height, xlink_href, classes)


class SvgGroup(SvgElement):
    """ a group of SVG elements inside a g-container """
    id_counters = {}

    def __init__(self,
                 elements: Optional[list[SvgElement]] = None,
                 attributes: Optional[dict[str, str]] = None,
                 classes: Optional[list[str]] = None,
                 id_base: str = 'group',
                 exact_id: Optional[str] = None,
                 ):
        super().__init__(tag='g', attributes=attributes, classes=classes)
        self._elements = elements or []
        counter = SvgGroup.id_counters.setdefault(id_base, 1)
        if exact_id is not None:
            self._attributes['id'] = exact_id
        else:
            self._attributes['id'] = f'{id_base}_{counter:03}'
        SvgGroup.id_counters[id_base] += 1

    @property
    def content(self) -> Optional[str]:
        """ the contained elements """
        if len(self._elements) == 0:
            return None
        content_lines = [indent(str(element), _INDENT) for element in self._elements]
        return '\n' + '\n'.join(content_lines) + '\n'

    def append(self, element: SvgElement) -> None:
        """ add an element to this group """
        self._elements.append(element)
