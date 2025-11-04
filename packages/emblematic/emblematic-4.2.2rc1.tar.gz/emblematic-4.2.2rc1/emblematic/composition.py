"""
Composition of emblems from multiple documents, making use of various :mod:`.operations`.
"""

from bs4 import BeautifulSoup, Tag

from .svg import stretch_center, contain_center, combine, fill_all, fill_specific, remove_defs, create_defs, create_dropshadow


def compose_basic(
    background: BeautifulSoup,
    foreground: BeautifulSoup,
    *,
    final_width_px: float,
    final_height_px: float,
) -> BeautifulSoup:
    """
    Create an emblem by overlaying the given foreground document on the given background document, rescaling both to the given dimensions.

    .. warning::
        This function **will alter the two given documents**, make sure to copy them with ``__copy__`` if this is undesirable.

    .. warning::
        This function **will not check that the inputs are valid**, make sure that the given documents contain a svg tag each.

    :param background: The background document.
    :param foreground: The foreground document, most likely an icon.
    :param final_width_px: The desired width of the final document.
    :param final_height_px: The desired height of the final document.
    :return: The document containing the created emblem.
    """

    background_svg: Tag = background.svg
    foreground_svg: Tag = foreground.svg

    stretch_center(background_svg)
    contain_center(foreground_svg, width_pct=63.0, height_pct=63.0)
    return combine(background_svg, foreground_svg, width_px=final_width_px, height_px=final_height_px)


def compose_solid(
    background: BeautifulSoup,
    foreground: BeautifulSoup,
    *,
    foreground_fill: str,
    final_width_px: float,
    final_height_px: float,
) -> BeautifulSoup:
    """
    Like :func:`.compose_basic`, but fills all paths in the foreground document with the given color.

    Use-case is FontAwesome Solid icons, but should work with most others as well.

    :param background: The background document.
    :param foreground: The foreground document, most likely an icon.
    :param foreground_fill: The color to fill the foreground with.
    :param final_width_px: The desired width of the final document.
    :param final_height_px: The desired height of the final document.
    :return: The document containing the created emblem.
    """

    foreground_svg: Tag = foreground.svg

    fill_all(foreground_svg, color=foreground_fill)
    return compose_basic(
        background=background,
        foreground=foreground,
        final_width_px=final_width_px,
        final_height_px=final_height_px
    )


def compose_shadow(
    background: BeautifulSoup,
    foreground: BeautifulSoup,
    *,
    foreground_fill: str,
    shadow_x_px: float,
    shadow_y_px: float,
    shadow_stddev: float,
    shadow_color: str,
    shadow_opacity: float,
    final_width_px: float,
    final_height_px: float,
) -> BeautifulSoup:
    """
    Like :func:`compose_solid`, but adds a shadow to the icon.

    .. warning::
        This function **will replace any defs tag the foreground document may contain with its own**.

    .. warning::

        PNG generation will not function correctly if a color with transparency is specified as ``shadow_color``. Use ``shadow_opacity`` instead!

    :param background: The background document.
    :param foreground: The foreground document, most likely an icon.
    :param foreground_fill: The color to fill the foreground with.
    :param shadow_x_px: The horizontal pixel offset of the shadow.
    :param shadow_y_px: The vertical pixel offset of the shadow.
    :param shadow_stddev: The standard deviation of the blur.
    :param shadow_color: The color to fill the shadow with.
    :param shadow_opacity: The opacity of the shadow.
    :param final_width_px: The desired width of the final document.
    :param final_height_px: The desired height of the final document.
    :return: The document containing the created emblem.
    """

    foreground_svg: Tag = foreground.svg

    remove_defs(foreground_svg)
    defs = create_defs(foreground, foreground_svg)

    dropshadow = create_dropshadow(
        foreground,
        defs,
        "emblematic-compose-shadow",
        shadow_x_px=shadow_x_px,
        shadow_y_px=shadow_y_px,
        shadow_stddev=shadow_stddev,
        shadow_color=shadow_color,
        shadow_opacity=shadow_opacity,
    )
    foreground_svg.attrs["filter"] = f"url(#{dropshadow.attrs['id']})"

    return compose_solid(
        background,
        foreground,
        foreground_fill=foreground_fill,
        final_width_px=final_width_px,
        final_height_px=final_height_px,
    )


def compose_duotone(
    background: BeautifulSoup,
    foreground: BeautifulSoup,
    *,
    primary_fill: str,
    secondary_fill: str,
    final_width_px: float,
    final_height_px: float,
) -> BeautifulSoup:
    """
    Like :func:`.compose_basic`, but fills the path with the ``fa-primary`` id with the first color given, and the path with the ``fa-secondary`` id with the second color given.

    This function **will remove any defs tag the foreground document may contain**.

    Use-case is FontAwesome Duotone icons.

    :param background: The background document.
    :param foreground: The foreground document, most likely an icon.
    :param primary_fill: The color to fill the primary part of the icon with.
    :param secondary_fill: The color to fill the secondary part of the icon with.
    :param final_width_px: The desired width of the final document.
    :param final_height_px: The desired height of the final document.
    :return: The document containing the created emblem.
    """

    foreground_svg: Tag = foreground.svg

    remove_defs(foreground_svg)
    fill_specific(foreground_svg, class_="fa-primary", color=primary_fill)
    fill_specific(foreground_svg, class_="fa-secondary", color=secondary_fill)
    return compose_basic(
        background=background,
        foreground=foreground,
        final_width_px=final_width_px,
        final_height_px=final_height_px
    )


__all__ = (
    "compose_basic",
    "compose_solid",
    "compose_shadow",
    "compose_duotone",
)
