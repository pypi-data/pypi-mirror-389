"""
Module containing functions to operate on files or directories.
"""

import subprocess
from pathlib import Path
from typing import Iterable


class WorkUnit:
    def __init__(self, source: Path, destination_stem: Path):
        self.source: Path = source
        self.destination_stem: Path = destination_stem

    @classmethod
    def find(cls, sources: Iterable[Path], destination: Path, dir_glob: str = "**/*.svg") -> set["WorkUnit"]:
        """
        Create a :class:`set` of :class:`.WorkUnit` from a list of sources and a destination directory.

        If a source is a directory, this function selects all files inside matching ``dir_glob``, producing destination paths preserving the original source directory structure.

        .. warning::
            This method **assumes the sources exist**. Check before calling it!

        .. warning::
            This method **assumes the destination exists and is a directory already**. Check before calling it!

        :param sources: An iterable of the paths to the sources to use. Sources can be both files or directories.
        :param destination: Path to the destination directory.
        :param dir_glob: Glob to use to find files inside directory sources.
        :return: The resulting :class:`set` of :class:`.WorkUnit`.
        """

        collection = set()

        for source in sources:
            if not source.exists():
                raise FileNotFoundError("Source does not exist: ", source)

            if source.is_dir():
                for file in source.glob(dir_glob):
                    # Skip directories
                    if file.is_dir():
                        continue

                    relative = file.relative_to(source)
                    destination_stem = destination / relative.parent / relative.stem
                    collection.add(cls(source=file, destination_stem=destination_stem))

            else:
                destination_stem = destination / source.stem
                collection.add(cls(source=source, destination_stem=destination_stem))

        return collection

    def create_destination_parents(self):
        """
        Create the parent directories of :attr:`.destination_stem`, if they do not already exist.
        """
        self.destination_stem.parent.mkdir(parents=True, exist_ok=True)

    def destination_svg(self) -> Path:
        """
        :return: :attr:`.destination_stem`, but with the ``.svg`` file extension.
        """
        return self.destination_stem.with_name(self.destination_stem.name + ".svg")

    def write_svg(self, svg_data: str) -> Path:
        """
        Write the given SVG document to :meth:`.destination_svg`.

        .. warning::
            This method **assumes the parent directories exist**. Create them with :meth:`.create_destination_parents` before running it!

        :param svg_data: The SVG document, in string form.
        """

        destination_svg_path = self.destination_svg()

        with destination_svg_path.open("w", encoding="utf-8") as destination_svg_file:
            destination_svg_file.write(svg_data)

        return destination_svg_path

    def destination_png(self) -> Path:
        """
        :return: :attr:`.destination_stem`, but with the ``.png`` file extension.
        """
        return self.destination_stem.with_name(self.destination_stem.name + ".png")

    def write_png(self, svg_data: str, *, width_px: int, height_px: int) -> Path:
        """
        Write the given SVG document as PNG to :meth:`.destination_png`, calling Inkscape in a :mod:`subprocess` to perform the conversion.

        .. warning::
            This method **assumes the parent directories exist**. Create them with :meth:`.create_destination_parents` before running it!

        :param svg_data: The SVG document, in string form.
        :param width_px: The width in pixels of the resulting image.
        :param height_px: The height in pixels of the resulting image.
        """

        destination_png_path = self.destination_png()

        result = subprocess.run(
            args=[
                "inkscape",
                "--pipe",
                "--export-type=png",
                f"--export-filename={self.destination_png()}",
                f"--export-width={width_px}",
                f"--export-height={height_px}"
            ],
            input=svg_data.encode("utf-8"),
        )
        if result.returncode != 0:
            raise ChildProcessError("Conversion to PNG with Inkscape returned non-zero exit code: ", result.returncode)

        return destination_png_path


__all__ = (
    "WorkUnit",
)
