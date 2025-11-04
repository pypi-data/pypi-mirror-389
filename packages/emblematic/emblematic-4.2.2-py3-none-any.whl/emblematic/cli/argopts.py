import pathlib

from click import Path, argument, option

option_background_file = option(
    "-b", "--background-file", "background_file",
    type=Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        allow_dash=False,
        path_type=pathlib.Path,
    ),
    required=True,
    help="SVG file to use as background.",
)

arguments_foreground_filename = argument(
    "foreground_filename",
    type=Path(
        exists=True,
        file_okay=True,
        dir_okay=True,
        readable=True,
        allow_dash=False,
        path_type=pathlib.Path,
    ),
    nargs=-1,
)

option_output_dir = option(
    "-o", "--output-dir", "output_dir",
    type=Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
        readable=True,
        writable=True,
        executable=True,
        allow_dash=False,
        path_type=pathlib.Path,
    ),
    required=True,
    help="Base directory where created emblems should be stored in. Must already exist.",
)

option_save_svg = option(
    "-s/-S", "--save-svg/--ignore-svg", "save_svg",
    type=bool,
    is_flag=True,
    default=False,
    help="Whether an emblem in SVG format should be generated or not.",
)

option_save_png = option(
    "-p/-P", "--save-png/--ignore-png", "save_png",
    type=bool,
    is_flag=True,
    default=True,
    help="Whether an emblem in PNG format should be generated or not.",
)

option_width_px = option(
    "-w", "--width-px", "width_px",
    type=float,
    default=512.0,
    help="Width in pixels of the output.",
)

option_height_px = option(
    "-h", "--height-px", "height_px",
    type=float,
    default=512.0,
    help="Height in pixels of the output.",
)

option_foreground_color = option(
    "-c", "--foreground-color", "foreground_color",
    type=str,
    required=True,
    help="CSS color (`red`, `#ff0000`, `rgb(255 0 0)`...) of the foreground.",
)

option_primary_color = option(
    "-c", "--primary-color", "primary_color",
    type=str,
    required=True,
    help="Primary CSS color (`red`, `#ff0000`, `rgb(255 0 0)`...) of the foreground.",
)

option_secondary_color = option(
    "-C", "--secondary-color", "secondary_color",
    type=str,
    required=True,
    help="Secondary CSS color (`lime`, `#00ff00`, `rgb(0 255 0)`...) of the foreground.",
)

option_shadow_offset_x_px = option(
    "-x", "--shadow-offset-x-px", "shadow_offset_x_px",
    type=float,
    required=True,
    help="Horizontal pixel offset of the shadow.",
)

option_shadow_offset_y_px = option(
    "-y", "--shadow-offset-y-px", "shadow_offset_y_px",
    type=float,
    required=True,
    help="Vertical pixel offset of the shadow.",
)

option_shadow_stddev = option(
    "-r", "--shadow-stddev", "shadow_stddev",
    type=float,
    required=True,
    help="Shadow blur standard deviation.",
)

option_shadow_color = option(
    "-f", "--shadow-color", "shadow_color",
    type=str,
    required=True,
    help="CSS color (`black`, `#000000`, `rgb(0 0 0)`...) of the shadow. *Does not support transparency if generating a PNG, use --shadow-opacity instead!*",
)

option_shadow_opacity = option(
    "-t", "--shadow-opacity", "shadow_opacity",
    type=float,
    default=1.0,
    help="Opacity of the produced shadow.",
)

__all__ = (
    "option_background_file",
    "arguments_foreground_filename",
    "option_output_dir",
    "option_save_svg",
    "option_save_png",
    "option_width_px",
    "option_height_px",
    "option_foreground_color",
    "option_primary_color",
    "option_secondary_color",
    "option_shadow_offset_x_px",
    "option_shadow_offset_y_px",
    "option_shadow_stddev",
    "option_shadow_color",
    "option_shadow_opacity",
)
