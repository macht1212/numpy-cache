import os
from dataclasses import dataclass

import click

from ._cache import inspect


@dataclass
class Header:
    magic: str
    version: int
    ndim: int
    dtype: int
    uncompressed_size: int
    compressed_size: int
    shape: tuple[int, ...]


@click.group()
def cli(): ...

@cli.command(name="inspect")
@click.argument("path")
def show_file_headers(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not find on {path=}.")

    info = Header(**inspect(path))

    click.echo(
        f"Magic: {info.magic}\nVersion: {info.version}\n"
        f"NDIM: {info.ndim}\ndType: {info.dtype}\n"
        f"Uncompressed size: {info.uncompressed_size}\n"
        f"Compressed size: {info.compressed_size}\n"
        f"Shape: {info.shape}"
    )


if __name__ == "__main__":
    cli()