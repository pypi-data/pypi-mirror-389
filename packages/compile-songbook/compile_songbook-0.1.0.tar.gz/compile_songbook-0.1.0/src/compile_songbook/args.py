import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Self


@dataclass
class SongbookArgs:
    songs: Path
    output: Path
    title: str
    authors: list[str]
    misc_category: str
    chorus_labels: list[str]
    table_of_contents_label: str

    @staticmethod
    def _get_parser_args() -> argparse.Namespace:
        """Provides a CLI interface that takes a single output argument.

        Returns:
            An argparse namespace with a single argument `output` pointing to where
            the compiled songbook will be placed.
        """
        parser = argparse.ArgumentParser(
            prog="Songbook", description="Compiles a songbook."
        )
        parser.add_argument("songs", type=Path, help="Directory containing songs.")
        parser.add_argument("output", type=Path, help="Where to output the document.")
        parser.add_argument("--title", help="The title of the songbook.")
        parser.add_argument(
            "--author", dest="authors", nargs="+", help="An author of the songbook."
        )
        parser.add_argument(
            "--misc-category",
            help="The default song category.",
            default="Miscellaneous",
        )
        parser.add_argument(
            "--chorus-label",
            help="The text that identifies the chorus.",
            action="append",
            dest="chorus_labels",
            default=[],
        )
        parser.add_argument(
            "--table-of-contents-label",
            help="The label for the table of contents.",
            default="Table of Contents",
        )
        return parser.parse_args()

    @classmethod
    def from_argparse(cls) -> Self:
        args = cls._get_parser_args()
        return cls(
            songs=Path(args.songs),
            output=Path(args.output),
            title=args.title,
            authors=args.authors,
            misc_category=args.misc_category,
            chorus_labels=args.chorus_labels,
            table_of_contents_label=args.table_of_contents_label,
        )
