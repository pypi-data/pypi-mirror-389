from dataclasses import dataclass
from enum import StrEnum


@dataclass
class Color:
    """ a color with corresponding foreground text color"""
    color: str
    top_text_color: str = '#000000'  # default to black text


class ColorPalette(tuple[Color, ...]):
    """ a pre-defined list of colors to be used for a plot """
    pass


class ClassNames(StrEnum):
    """ string constants for all the class names that are commonly used for styling via CSS """
    # determining the timeline element:
    TITLE = 'title'
    TIME_ARROW = 'time_arrow'
    EVENT = 'event'
    TIMESPAN = 'timespan'
    CONNECTED_EVENTS = 'connected_events'
    IMAGE = 'image'
    # sub-elements
    TIME_ARROW_AXIS = 'time_axis'
    TIME_ARROW_MINOR_TIC = 'minor_tic'
    TIME_ARROW_MAJOR_TIC = 'major_tic'
    # for picking which color to use:
    COLORED = 'colored'
    TOP_TEXT = 'top_text'


DEFAULT_CSS = {
    'rect.background': {
        'fill': 'white',
    },
    'path': {
        'stroke': 'black',
        'stroke-width': '2pt',
        'fill': 'none',
    },
    'text': {
        'font-size': '10pt',
        'font-family': 'Liberation Sans',
        'fill': 'black',
        'text-anchor': 'middle',
        'dominant-baseline': 'central',
    },
    'circle, rect': {
        'fill': 'black',
    },
    f'text.{ClassNames.TITLE}': {
        'font-size': '20pt',
    },
    f'path.{ClassNames.TIME_ARROW_AXIS}': {
        'stroke-width': '3pt',
    },
    f'path.{ClassNames.TIME_ARROW_MAJOR_TIC}': {
        'stroke-width': '2pt',
    },
    f'path.{ClassNames.TIME_ARROW_MINOR_TIC}': {
        'stroke-width': '1pt',
    },
    f'path.{ClassNames.EVENT}': {
        'stroke-width': '2pt',
    },
    f'text.{ClassNames.TIMESPAN}': {
        'font-size': '9pt',
    },
    f'path.{ClassNames.IMAGE}': {
        'stroke-width': '2pt',
    },
}


DEFAULT_COLORS = ColorPalette((
    Color('#000000', '#ffffff'),  # black with white text
    Color('#003f5c', '#ffffff'),  # dark blue with white text
    Color('#58508d', '#ffffff'),  # purple-blue with white text
    Color('#bc5090'),  # purple
    Color('#ff6361'),  # light red
    Color('#ffa600'),  # golden
))


# Default seaborn color palette as generated via:
# > print(sns.color_palette().as_hex())
SEABORN_COLORS = ColorPalette((
    Color('#000000', '#ffffff'),  # black with white text
    Color('#1f77b4'),  # blue
    Color('#ff7f0e'),  # orange
    Color('#2ca02c'),  # green
    Color('#d62728'),  # red
    Color('#9467bd'),  # purple
    Color('#8c564b'),  # brown
    Color('#e377c2'),  # pink
    Color('#7f7f7f'),  # grey
    Color('#bcbd22'),  # lime
    Color('#17becf'),  # cyan
))
