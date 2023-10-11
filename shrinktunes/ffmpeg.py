import re
import subprocess
from dataclasses import dataclass

import typer


@dataclass
class FFmpegFormat:
    is_decoder: bool
    is_encoder: bool
    extension: str
    description: str


def get_ffmpeg_supported_formats() -> list[FFmpegFormat]:
    process = subprocess.run(["ffmpeg", "-formats"], capture_output=True, text=True)
    output = process.stdout

    # Regex with named capture groups
    pattern = re.compile(r"""
        ^\s*                      # Start of the line, potential spaces
        (?P<is_decoder>D)?        # 'D' indicates a decoder, optional
        \.?                       # Potential dot separator
        (?P<is_encoder>E)?        # 'E' indicates an encoder, optional
        \s+                       # One or more spaces
        (?P<extension>\S+)\s+     # Extension (no spaces, followed by spaces)
        (?P<description>.*?)\s*$  # Description (non-greedy capture till end of line)
    """, re.VERBOSE)

    formats = []
    for line in output.split("\n"):
        match = pattern.match(line)
        if match:
            d = match.groupdict()
            for ext in d["extension"].split(","):
                formats.append(FFmpegFormat(
                    is_decoder=d["is_decoder"] == 'D',
                    is_encoder=d["is_encoder"] == 'E',
                    extension=ext,
                    description=d["description"].strip()  # Remove potential trailing whitespace
                ))

    return formats


def filter_extensions(formats: list[FFmpegFormat], exts=None) -> list[FFmpegFormat]:
    exts = exts or {"wav", "mp3", "m4a", "ogg", "flac", "wma", "aac", "mp4", "webm", "mkv", "avi", "wma"}
    return [fmt for fmt in formats if fmt.extension in exts]


SUPPORTED_FORMATS = sorted(get_ffmpeg_supported_formats(), key=lambda fmt: fmt.extension)
SUPPORTED_FORMATS_BY_EXTENSION = {fmt.extension: fmt for fmt in SUPPORTED_FORMATS}

SUPPORTED_DECODE_FORMATS = [fmt for fmt in SUPPORTED_FORMATS if fmt.is_decoder]
SUPPORTED_ENCODE_FORMATS = [fmt for fmt in SUPPORTED_FORMATS if fmt.is_encoder]

COMMON_SUPPORTED_DECODE_FORMATS = filter_extensions(SUPPORTED_DECODE_FORMATS)
COMMON_SUPPORTED_ENCODE_FORMATS = filter_extensions(SUPPORTED_ENCODE_FORMATS)


def check_ffmpeg_installation():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except FileNotFoundError:
        return False


def print_ffmpeg_info(print_decoders=False, print_encoders=True, show_all=False):
    if check_ffmpeg_installation():
        typer.echo(typer.style("ffmpeg is installed", fg=typer.colors.GREEN))
    else:
        typer.echo(typer.style("ffmpeg is NOT installed", fg=typer.colors.RED))
        raise SystemExit(1)

    ext_max_len = max(len(fmt.extension) for fmt in SUPPORTED_FORMATS)
    gap = 3

    if print_decoders:
        typer.echo("\nDecoders:")
        for fmt in SUPPORTED_DECODE_FORMATS if show_all else COMMON_SUPPORTED_DECODE_FORMATS:
            typer.echo(typer.style(
                f"{fmt.extension:{ext_max_len + gap}}{fmt.description}",
                bold=fmt in COMMON_SUPPORTED_DECODE_FORMATS,
                fg=typer.colors.YELLOW
            ))
    if print_encoders:
        typer.echo("\nEncoders:")
        for fmt in SUPPORTED_ENCODE_FORMATS if show_all else COMMON_SUPPORTED_ENCODE_FORMATS:
            typer.echo(typer.style(
                f"{fmt.extension:{ext_max_len + gap}}{fmt.description}",
                bold=fmt in COMMON_SUPPORTED_ENCODE_FORMATS,
                fg=typer.colors.BLUE
            ))


if __name__ == "__main__":
    print_ffmpeg_info()
