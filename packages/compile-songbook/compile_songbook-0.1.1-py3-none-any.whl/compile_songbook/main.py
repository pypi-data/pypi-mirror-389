#!/usr/bin/env python
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import IO

from compile_songbook.args import SongbookArgs
from compile_songbook.parse import iter_lines


def build_template(songbook_args: SongbookArgs, template: IO[str]) -> None:
    empty_template = Path(__file__).parent / "songbook.ms"

    bare_template = empty_template.read_text()
    text = bare_template.format(
        title=songbook_args.title,
        authors=", ".join(songbook_args.authors),
        contents="\n".join(iter_lines(songbook_args)),
        toc=songbook_args.table_of_contents_label,
    )

    template.write(text)
    template.close()


def compile(songbook_args: SongbookArgs) -> None:
    """Takes a group of songs and creates a PDF songbook.

    Args:
        songbook_args: The arguments to compile the songbook.
    """
    groff_font_path = Path(__file__).parent / "fonts"
    with NamedTemporaryFile("w", encoding="utf8", delete_on_close=False) as template:
        build_template(songbook_args, template)
        arguments = [
            "/usr/bin/groff",
            "-k",
            "-Tutf8",
            f"-F{groff_font_path}",
            "-ms",
            "-dpaper=a5",
            "-P-pa5",
            "-Tpdf",
            template.name,
        ]
        with songbook_args.output.open("w", encoding="utf8") as outfile:
            subprocess.check_call(arguments, stdout=outfile)
        Path(template.name).unlink()


def main() -> None:
    """Entry point for the application."""
    songbook_args = SongbookArgs.from_argparse()
    compile(songbook_args)


if __name__ == "__main__":
    main()
