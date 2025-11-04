"""
Basic operations that can be performed on ``<svg>`` tags, like stretching and centering.

Except for :func:`combine`, all these methods operate in-place.
"""

from bs4 import BeautifulSoup, Tag


def stretch_center(tag: Tag, width_pct: float = 100.0, height_pct: float = 100.0) -> None:
    """
    Make a SVG tag fill a portion of its parent, ignoring its original aspect ratio.

    :param tag: The tag to edit.
    :param width_pct: The width percentage to fill.
    :param height_pct: The height percentage to fill.
    """

    tag.attrs["width"] = f"{width_pct}%"
    tag.attrs["height"] = f"{height_pct}%"

    tag.attrs["x"] = f"{(100.0 - width_pct) / 2}%"
    tag.attrs["y"] = f"{(100.0 - height_pct) / 2}%"


def contain_center(tag: Tag, width_pct: float = 100.0, height_pct: float = 100.0) -> None:
    """
    Make a SVG tag fill a portion of its parent, respecting its original aspect ratio by making it smaller than the area if necessary, then centering.

    :param tag: The tag to edit.
    :param width_pct: The width percentage to fill.
    :param height_pct: The height percentage to fill.
    """

    tag.attrs["preserveAspectRatio"] = "xMidYMid meet"

    tag.attrs["width"] = f"{width_pct}%"
    tag.attrs["height"] = f"{height_pct}%"

    tag.attrs["x"] = f"{(100.0 - width_pct) / 2}%"
    tag.attrs["y"] = f"{(100.0 - height_pct) / 2}%"


def combine(*tags: Tag, width_px: float, height_px: float) -> BeautifulSoup:
    """
    Create a new SVG document of the given absolute size containing all the given tags.

    :param tags: The tags to combine.
    :param width_px: The absolute width in pixels of the new document.
    :param height_px: The absolute height in pixels of the new document.
    :return: The created SVG document.
    """

    doc = BeautifulSoup(features="lxml-xml")

    svg = doc.new_tag("svg", xmlns="http://www.w3.org/2000/svg")
    svg.attrs["viewBox"] = f"0 0 {width_px} {height_px}"

    for tag in tags:
        svg.append(tag)

    doc.append(svg)

    return doc


def remove_defs(tag: Tag) -> None:
    """
    Remove all defs tags from the given SVG tag.

    :param tag: The tag to edit.
    """

    defs = tag.find_all("defs")
    for d in defs:
        d.decompose()


def create_defs(doc: BeautifulSoup, tag: Tag) -> Tag:
    """
    Create a defs tag in the given SVG tag.

    :param doc: The document the tag is contained in.
    :param tag: The svg tag to create defs in.
    :return: The created defs tag.
    """

    defs: Tag = tag.append(doc.new_tag("defs"))  # type: ignore
    return defs


def create_dropshadow(
    doc: BeautifulSoup,
    tag: Tag,
    id_: str,
    shadow_x_px: float,
    shadow_y_px: float,
    shadow_stddev: float,
    shadow_color: str,
    shadow_opacity: float,
) -> Tag:
    """
    Create a filter tag describing a shadow with gaussian blur in the given defs tag.

    .. warning::

        Inkscape does not support transparency in ``feFlood[flood-color]``, so specifying a transparent color as ``shadow_color`` will break PNG generation.

    :param doc: The document the tag is contained in.
    :param tag: The defs tag to create filter in.
    :param id_: The id to give to the filter.
    :param shadow_x_px: The horizontal pixel offset of the shadow.
    :param shadow_y_px: The vertical pixel offset of the shadow.
    :param shadow_stddev: The standard deviation of the blur.
    :param shadow_color: The color of the shadow.
    :param shadow_opacity: The opacity of the shadow.
    :return: The created filter tag.
    """

    # noinspection PyTypeChecker
    filter_: Tag = tag.append(doc.new_tag("filter"))
    filter_.attrs["id"] = id_
    filter_.attrs["color-interpolation-filters"] = "sRGB"

    # noinspection PyTypeChecker
    flood: Tag = filter_.append(doc.new_tag("feFlood"))
    flood.attrs["in"] = "SourceGraphic"
    flood.attrs["result"] = "flood"
    flood.attrs["flood-color"] = f"{shadow_color}"
    flood.attrs["flood-opacity"] = f"{shadow_opacity}"

    # noinspection PyTypeChecker
    blur: Tag = filter_.append(doc.new_tag("feGaussianBlur"))
    blur.attrs["in"] = "SourceGraphic"
    blur.attrs["result"] = "blur"
    blur.attrs["stdDeviation"] = f"{shadow_stddev}"

    # noinspection PyTypeChecker
    offset: Tag = filter_.append(doc.new_tag("feOffset"))
    offset.attrs["in"] = blur.attrs["result"]
    offset.attrs["result"] = "offset"
    offset.attrs["dx"] = f"{shadow_x_px}"
    offset.attrs["dy"] = f"{shadow_y_px}"

    # noinspection PyTypeChecker
    shadow: Tag = filter_.append(doc.new_tag("feComposite"))
    shadow.attrs["in"] = flood.attrs["result"]
    shadow.attrs["in2"] = offset.attrs["result"]
    shadow.attrs["operator"] = "in"
    shadow.attrs["result"] = "shadow"

    # noinspection PyTypeChecker
    image: Tag = filter_.append(doc.new_tag("feComposite"))
    image.attrs["in"] = "SourceGraphic"
    image.attrs["in2"] = shadow.attrs["result"]
    image.attrs["operator"] = "over"
    image.attrs["result"] = "image"

    ### Unfortunately, not supported in Inkscape yet.
    # effect: Tag = filter_.append(doc.new_tag("feDropShadow"))
    # effect.attrs["dx"] = f"{shadow_x_px}"
    # effect.attrs["dy"] = f"{shadow_y_px}"
    # effect.attrs["stdDeviation"] = f"{shadow_stddev}"
    # effect.attrs["flood-color"] = f"{shadow_color}"
    ###

    return filter_


def fill_all(tag: Tag, color: str) -> None:
    """
    Fill, with the given color, all paths in the given SVG tag.

    :param tag: The tag to edit.
    :param color: The color to fill paths with.
    """

    paths = tag.find_all("path")

    for path in paths:
        path.attrs["fill"] = color


def fill_specific(tag: Tag, class_: str, color: str) -> None:
    """
    Fill, with the given color, the paths with the given ``class`` in the given SVG tag.

    :param tag: The tag to edit.
    :param class_: The class name to find.
    :param color: The color to fill paths with.
    """

    paths = tag.find_all("path", {"class": class_})
    for path in paths:
        path.attrs["fill"] = color


__all__ = (
    "stretch_center",
    "contain_center",
    "combine",
    "remove_defs",
    "create_defs",
    "create_dropshadow",
    "fill_all",
    "fill_specific",
)
