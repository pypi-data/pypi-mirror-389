from collections.abc import Generator, Iterable
from dataclasses import dataclass
from enum import StrEnum
from functools import partial
from itertools import groupby
from typing import Self

from compile_songbook.args import SongbookArgs

type IterLines = Generator[str, None, None]


class Formatting(StrEnum):
    PLAIN = "plain"
    COMPACT = "compact"


@dataclass
class SongHeader:
    title: str
    composers: list[str]
    lyricists: list[str]
    language: str
    category: str
    formatting: str

    @classmethod
    def from_text(cls, text: str, /, *, args: SongbookArgs) -> Self:
        """Extracts all metadata from a song's header text."""
        header_dict = {}

        for line in text.split("\n"):
            key, value = map(str.strip, line.split(":"))
            header_dict[key.lower()] = value

        if "title" not in header_dict:
            raise ValueError("Could not find title of song.")

        composers = list(
            filter(bool, map(str.strip, header_dict.get("composers", "").split(",")))
        )
        lyricists = list(
            filter(bool, map(str.strip, header_dict.get("lyricists", "").split(",")))
        )
        formatting_str = header_dict.get("formatting", "plain").lower()
        if formatting_str not in Formatting:
            raise ValueError(f"Invalid formatting value: {formatting_str!r}.")

        return cls(
            title=header_dict["title"],
            composers=composers,
            lyricists=lyricists,
            language=header_dict.get("language"),
            category=header_dict.get("category", args.misc_category),
            formatting=Formatting(formatting_str),
        )

    def render(self) -> IterLines:
        yield ".bp"
        yield ".SH 2"
        yield ".ce"
        yield f'.XH 2 "{self.title}"'
        authors_including_duplicates = self.composers + self.lyricists
        authors = sorted(
            set(authors_including_duplicates), key=authors_including_duplicates.index
        )
        if authors:
            yield ".AU"
            yield ", ".join(authors)
        paragraph_distance = "25p" if self.formatting == Formatting.PLAIN else "15p"
        yield ".nr VS 8p"
        yield f".nr PD {paragraph_distance}"


@dataclass
class SongParagraph:
    lines: list[str]

    @classmethod
    def from_text(cls, text: str, /) -> Self:
        return cls(lines=text.strip().split("\n"))

    def is_chorus_marker(self, args: SongbookArgs) -> bool:
        return len(self.lines) == 1 and self.lines[0] in args.chorus_labels

    def render(self, args: SongbookArgs) -> IterLines:
        yield ".KS"
        yield ".LP"

        if self.is_chorus_marker(args=args):
            yield ".sp"
            yield ".BI"
            yield self.lines[0]
            yield ".KE"
            return

        for line in self.lines:
            yield ".sp"
            yield line
        yield ".KE"


@dataclass
class SongBody:
    paragraphs: list[SongParagraph]

    @classmethod
    def from_text(cls, text: str, /, *, args: SongbookArgs) -> Self:
        paragraphs = []

        for paragraph in text.split("\n\n"):
            paragraph = SongParagraph.from_text(paragraph)
            paragraphs.append(paragraph)

        return cls(paragraphs=paragraphs)

    def render(self, args: SongbookArgs) -> IterLines:
        for paragraph in self.paragraphs:
            yield from paragraph.render(args)


@dataclass
class SongInfo:
    header: SongHeader
    body: SongBody

    @classmethod
    def from_text(cls, text: str, /, *, args: SongbookArgs) -> Self:
        """Extracts a song's components from its text."""
        components = text.split("\n\n", 1)
        if len(components) != 2:
            raise ValueError("Could not find song body.")
        header_text, body_text = components
        return cls(
            header=SongHeader.from_text(header_text.strip(), args=args),
            body=SongBody.from_text(body_text.strip(), args=args),
        )

    def get_category(self) -> str:
        return self.header.category

    def get_category_and_title(self, args: SongbookArgs) -> tuple[bool, str, str]:
        category = self.get_category()
        return category == args.misc_category, category, self.header.title

    def render(self, args: SongbookArgs) -> IterLines:
        yield from self.header.render()
        yield from self.body.render(args)
        yield ".nr VS 12p"
        yield ".nr PS 10p"


def render_category(
    category: str, song_infos: Iterable[SongInfo], *, args: SongbookArgs
) -> IterLines:
    yield ".bp"
    yield ".SH 1"
    yield ".ce"
    yield f'.XH 1 "\\fB{category}\\fR"'
    for song_info in song_infos:
        yield from song_info.render(args)


def iter_lines(args: SongbookArgs) -> IterLines:
    song_infos = []
    for song in args.songs.iterdir():
        song_infos.append(SongInfo.from_text(song.read_text(), args=args))

    sort_songs = partial(SongInfo.get_category_and_title, args=args)
    sorted_song_infos = sorted(song_infos, key=sort_songs)

    for category, group in groupby(sorted_song_infos, SongInfo.get_category):
        yield from render_category(category, group, args=args)
