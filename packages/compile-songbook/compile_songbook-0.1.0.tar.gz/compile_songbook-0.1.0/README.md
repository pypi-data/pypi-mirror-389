# songbook

Tool for compiling text files containing lyrics into a single PDF.

## How to run

This tool is designed with Linux systems bundling GNU roff (groff) on them.
There are two primary ways to install this tool, but in either case, you will
need to install the [uv package manager](https://docs.astral.sh/uv/):

### Using uvx

The simplest way to run this tool is to use the `uvx` command. Installation is
handled in a temporary virtual environment behind the scenes.

```sh
uvx compile-songbook path/to/my/songs output/songbook.pdf --title="My songs" --author="Bob"
```

### As a developer

If you are familiar with groff, the more hands-on method is to clone the code.

```sh
git clone https://github.com/clockback/songbook
cd songbook
```

You can then use uv to run the code like so:

```sh
uv run compile-songbook path/to/my/songs output/songbook.pdf --title="My songs" --author="Bob"
```

The source code is written in Python and easy to modify if you wish to apply
further customization.

## Formatting songs

When you provide an argument to identify your songs (e.g. `path/to/my/songs`), all files in that directory will need to follow the following format:

```
Title: Song of the Flamingos

This is the first verse,
These words are all I've got,
Do you like flamingos?
I most certainly do not...

Chorus

No I don't like flamingos,
I don't like them one jot,
They cause me so much trouble,
Yes I despise them such a lot...

This is the second verse,
It's no better than the first,
I'll desist from writing more verses,
They'll probably get worse.

Chorus

Chorus
```

The first line constitutes metadata for the song, and a number of optional
fields may be provided, for example:

```
Title: Song of the Flamingos
Composers: Joseph Derbyshire
Lyricists: Colin Kirk
Language: English
Category: Comedy songs
Formatting: Compact
```

The `Language` field is not presently used. The `Formatting` field can be set
to `Plain` (default) or `Compact`, the latter of which will reduce the
paragraph spacing.
