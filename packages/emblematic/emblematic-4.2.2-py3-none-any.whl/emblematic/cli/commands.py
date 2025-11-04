import pathlib
from typing import Iterator

import bs4
import click

from emblematic.composition import compose_basic, compose_solid, compose_shadow, compose_duotone
from .argopts import option_background_file, arguments_foreground_filename, option_output_dir, option_save_svg, option_save_png, option_width_px, \
    option_height_px, option_foreground_color, option_primary_color, option_secondary_color, option_shadow_offset_x_px, option_shadow_offset_y_px, \
    option_shadow_stddev, option_shadow_color, option_shadow_opacity
from .files import WorkUnit


@click.group()
@click.version_option(package_name="emblematic", prog_name="emblematic")
@click.pass_context
def main(ctx: click.Context):
    """
    Generate an emblem, an easily recognizable yet consistently styled icon.
    """

    # 80 is NOT a sensible default in any case, let the user choose!
    ctx.max_content_width = 10000
    ctx.show_default = True


@main.command()
@option_background_file
@arguments_foreground_filename
@option_output_dir
@option_save_svg
@option_save_png
@option_width_px
@option_height_px
def basic(
    background_file: pathlib.Path,
    foreground_filename: Iterator[pathlib.Path],
    output_dir: pathlib.Path,
    save_svg: bool,
    save_png: bool,
    width_px: float,
    height_px: float,
):
    """
    Create a simple emblem.
    """

    click.echo(
        err=True,
        message=
        click.style("Generating ", fg="cyan") +
        click.style("basic", fg="cyan", bold=True) +
        click.style(" emblems.", fg="cyan")
    )

    work_units = WorkUnit.find(sources=foreground_filename, destination=output_dir)

    click.echo(
        err=True,
        message=
        click.style("Found ", fg="cyan") +
        click.style(f"{len(work_units)}", fg="cyan", bold=True) +
        click.style(" foreground elements.", fg="cyan")
    )

    with background_file.open("r") as background_file:
        background_soup_original = bs4.BeautifulSoup(background_file, features="lxml-xml")

    for work_unit in work_units:
        background_soup = background_soup_original.__copy__()

        with work_unit.source.open("r") as foreground_file:
            foreground_soup = bs4.BeautifulSoup(foreground_file, features="lxml-xml")

        result = compose_basic(
            background=background_soup,
            foreground=foreground_soup,
            final_width_px=width_px,
            final_height_px=height_px,
        ).prettify()

        work_unit.create_destination_parents()

        if save_svg:
            svg_path = work_unit.write_svg(result)
            click.echo(svg_path)

        if save_png:
            png_path = work_unit.write_png(result, width_px=int(width_px), height_px=int(height_px))
            click.echo(png_path)


@main.command()
@option_background_file
@arguments_foreground_filename
@option_output_dir
@option_save_svg
@option_save_png
@option_width_px
@option_height_px
@option_foreground_color
def solid(
    background_file: pathlib.Path,
    foreground_filename: Iterator[pathlib.Path],
    output_dir: pathlib.Path,
    save_svg: bool,
    save_png: bool,
    width_px: float,
    height_px: float,
    foreground_color: str,
):
    """
    Create an emblem with a solid color foreground.

    Intended for Font Awesome Solid icons.
    """

    click.echo(
        err=True,
        message=
        click.style("Generating ", fg="cyan") +
        click.style("solid", fg="cyan", bold=True) +
        click.style(" emblems.", fg="cyan")
    )

    work_units = WorkUnit.find(sources=foreground_filename, destination=output_dir)

    click.echo(
        err=True,
        message=
        click.style("Found ", fg="cyan") +
        click.style(f"{len(work_units)}", fg="cyan", bold=True) +
        click.style(" foreground elements.", fg="cyan")
    )

    with background_file.open("r") as background_file:
        background_soup_original = bs4.BeautifulSoup(background_file, features="lxml-xml")

    for work_unit in work_units:
        background_soup = background_soup_original.__copy__()

        with work_unit.source.open("r") as foreground_file:
            foreground_soup = bs4.BeautifulSoup(foreground_file, features="lxml-xml")

        result = compose_solid(
            background=background_soup,
            foreground=foreground_soup,
            foreground_fill=foreground_color,
            final_width_px=width_px,
            final_height_px=height_px,
        ).prettify()

        work_unit.create_destination_parents()

        if save_svg:
            svg_path = work_unit.write_svg(result)
            click.echo(svg_path)

        if save_png:
            png_path = work_unit.write_png(result, width_px=int(width_px), height_px=int(height_px))
            click.echo(png_path)


@main.command()
@option_background_file
@arguments_foreground_filename
@option_output_dir
@option_save_svg
@option_save_png
@option_width_px
@option_height_px
@option_foreground_color
@option_shadow_offset_x_px
@option_shadow_offset_y_px
@option_shadow_stddev
@option_shadow_color
@option_shadow_opacity
def shadow(
    background_file: pathlib.Path,
    foreground_filename: Iterator[pathlib.Path],
    output_dir: pathlib.Path,
    save_svg: bool,
    save_png: bool,
    width_px: float,
    height_px: float,
    foreground_color: str,
    shadow_offset_x_px: float,
    shadow_offset_y_px: float,
    shadow_stddev,
    shadow_color,
    shadow_opacity: float,
):
    """
    Create an emblem with a solid color foreground with a shadow.

    Intended for Font Awesome Solid icons.
    """

    click.echo(
        err=True,
        message=
        click.style("Generating ", fg="cyan") +
        click.style("shadow", fg="cyan", bold=True) +
        click.style(" emblems.", fg="cyan")
    )

    work_units = WorkUnit.find(sources=foreground_filename, destination=output_dir)

    click.echo(
        err=True,
        message=
        click.style("Found ", fg="cyan") +
        click.style(f"{len(work_units)}", fg="cyan", bold=True) +
        click.style(" foreground elements.", fg="cyan")
    )

    with background_file.open("r") as background_file:
        background_soup_original = bs4.BeautifulSoup(background_file, features="lxml-xml")

    for work_unit in work_units:
        background_soup = background_soup_original.__copy__()

        with work_unit.source.open("r") as foreground_file:
            foreground_soup = bs4.BeautifulSoup(foreground_file, features="lxml-xml")

        result = compose_shadow(
            background=background_soup,
            foreground=foreground_soup,
            foreground_fill=foreground_color,
            shadow_x_px=shadow_offset_x_px,
            shadow_y_px=shadow_offset_y_px,
            shadow_stddev=shadow_stddev,
            shadow_color=shadow_color,
            shadow_opacity=shadow_opacity,
            final_width_px=width_px,
            final_height_px=height_px,
        ).prettify()

        work_unit.create_destination_parents()

        if save_svg:
            svg_path = work_unit.write_svg(result)
            click.echo(svg_path)

        if save_png:
            png_path = work_unit.write_png(result, width_px=int(width_px), height_px=int(height_px))
            click.echo(png_path)


@main.command()
@option_background_file
@arguments_foreground_filename
@option_output_dir
@option_save_svg
@option_save_png
@option_width_px
@option_height_px
@option_primary_color
@option_secondary_color
def duotone(
    background_file: pathlib.Path,
    foreground_filename: Iterator[pathlib.Path],
    output_dir: pathlib.Path,
    save_svg: bool,
    save_png: bool,
    width_px: float,
    height_px: float,
    primary_color: str,
    secondary_color: str,
):
    """
    Create an emblem with two separate colors as foreground.

    Intended for Font Awesome Duotone icons.
    """

    click.echo(
        err=True,
        message=
        click.style("Generating ", fg="cyan") +
        click.style("duotone", fg="cyan", bold=True) +
        click.style(" emblems.", fg="cyan")
    )

    work_units = WorkUnit.find(sources=foreground_filename, destination=output_dir)

    click.echo(
        err=True,
        message=
        click.style("Found ", fg="cyan") +
        click.style(f"{len(work_units)}", fg="cyan", bold=True) +
        click.style(" foreground elements.", fg="cyan")
    )

    with background_file.open("r") as background_file:
        background_soup_original = bs4.BeautifulSoup(background_file, features="lxml-xml")

    for work_unit in work_units:
        background_soup = background_soup_original.__copy__()

        with work_unit.source.open("r") as foreground_file:
            foreground_soup = bs4.BeautifulSoup(foreground_file, features="lxml-xml")

        result = compose_duotone(
            background=background_soup,
            foreground=foreground_soup,
            primary_fill=primary_color,
            secondary_fill=secondary_color,
            final_width_px=width_px,
            final_height_px=height_px,
        ).prettify()

        work_unit.create_destination_parents()

        if save_svg:
            svg_path = work_unit.write_svg(result)
            click.echo(svg_path)

        if save_png:
            png_path = work_unit.write_png(result, width_px=int(width_px), height_px=int(height_px))
            click.echo(png_path)


__all__ = (
    "main",
)
