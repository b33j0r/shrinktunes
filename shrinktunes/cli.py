import typer
import asyncio
from pathlib import Path
import subprocess
from datetime import datetime
import platform

from shrinktunes.ffmpeg import get_ffmpeg_supported_formats, SUPPORTED_FORMATS, check_ffmpeg_installation, \
    print_ffmpeg_info, SUPPORTED_FORMATS_BY_EXTENSION

app = typer.Typer()


# Log with a timestamp, only if verbose mode is enabled
def log(message, verbose):
    if verbose:
        typer.echo(f"[{datetime.now().isoformat()}] {message}")


# Convert a single file to the desired format
async def convert_file(input_path: Path, output_format: str, verbose: bool, force: bool):
    output_path = input_path.with_suffix(f".{output_format}")
    if output_path.exists() and not force:
        log(f"Skipping {output_path} as it already exists. Use -f to force overwrite.", verbose)
        return False
    subprocess.run(["ffmpeg", "-i", str(input_path), str(output_path)], check=True)
    log(f"Converted {input_path} -> {output_path}", verbose)
    return True


# Convert all files matching the glob pattern to the desired formats
async def convert_files(glob_pattern: str, output_formats: list[str], verbose: bool, force: bool):
    # Use Path().glob() to expand the pattern and get all matching files
    paths = list(Path().glob(glob_pattern))
    log(f"Scanning glob {glob_pattern}", verbose)
    log(f"Found {len(paths)} files", verbose)

    converted_count = 0
    for output_format in output_formats:
        for path in paths:
            if path.suffix == ".wav":
                success = await convert_file(path, output_format, verbose, force)
                if success:
                    converted_count += 1
        log(f"Converted {converted_count} files to {output_format}", verbose)
    log(f"{converted_count} files converted, {len(paths) - converted_count} skipped.", verbose)


@app.command()
def convert(
        glob_pattern: str = typer.Argument(..., help="Glob pattern for .wav files to convert."),
        output: list[str] = typer.Option(..., "-o",
                                         help="Output format(s). Supported formats are dynamically determined from ffmpeg."),
        verbose: bool = typer.Option(False, "-v", help="Enable verbose mode."),
        force: bool = typer.Option(False, "-f", help="Force overwrite of existing files.")
):
    """
    Convert .wav files matching the glob pattern to the specified format(s).
    """
    if not check_ffmpeg_installation():
        typer.echo("ffmpeg is not installed. Please install it first.")

        # Recommend installation method based on the platform
        os_type = platform.system()
        if os_type == "Darwin":
            typer.echo("For macOS: brew install ffmpeg")
        elif os_type == "Linux":
            typer.echo("For Ubuntu: sudo apt-get install ffmpeg")
        elif os_type == "Windows":
            typer.echo("For Windows: winget install ffmpeg OR scoop install ffmpeg")
        else:
            typer.echo(f"Please check the ffmpeg installation guide for {os_type}.")
        raise typer.Exit(code=1)

    # Check if the output format is supported
    for fmt in output:
        if fmt not in SUPPORTED_FORMATS_BY_EXTENSION:
            typer.echo(f"Unsupported output format: {fmt}")
            raise typer.Exit(code=1)

    try:
        # Convert the files
        asyncio.run(convert_files(glob_pattern, output, verbose, force))
    except Exception as e:
        typer.echo(f"Error occurred: {e}")
        raise typer.Exit(code=1)


@app.command()
def info():
    print_ffmpeg_info(print_decoders=True, print_encoders=True)


def cli_main():
    app()


if __name__ == "__main__":
    cli_main()
