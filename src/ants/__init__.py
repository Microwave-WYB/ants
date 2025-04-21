import httpx
from pathlib import Path
from ants.core import download_file
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Download files from a URL")
    parser.add_argument("url", type=str, help="URL to download")
    parser.add_argument(
        "-n",
        "--workers",
        type=int,
        default=4,
        help="Number of workers",
    )
    parser.add_argument("-o", "--output", type=str, help="Output file")
    args = parser.parse_args()

    output = Path(args.output or Path.cwd() / "downloads")
    if output.is_dir():
        download_file(httpx.Request("GET", args.url), max_workers=args.workers, output_dir=output)
    elif output.is_file() or not output.exists():
        download_file(
            httpx.Request("GET", args.url),
            max_workers=args.workers,
            output_dir=output.parent,
            filename=output.name,
        )
    elif output.exists():
        print(f"File {output} already exists")
        exit(1)


__all__ = ["download_file"]
