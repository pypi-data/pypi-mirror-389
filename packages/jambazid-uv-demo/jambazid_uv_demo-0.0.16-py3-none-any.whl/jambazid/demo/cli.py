"""
Typer-based CLI demo.
"""

import pathlib
import typing

import typer


app = typer.Typer()


@app.command()
def main(
    foo: typing.Annotated[str, typer.Option(help="Dummy Option #1.")],
    bar: typing.Annotated[list[str], typer.Option(help="Dummy Option #2.", default_factory=list[str])],
    src: typing.Annotated[pathlib.Path, typer.Option(help="Dummy Option #3.")],
) -> None:
    """
    A dummy Typer CLI.

    See "https://typer.tiangolo.com/".
    """
    print("foo:", foo)

    for idx, value in enumerate(bar):
        print(f"bar[{idx}]:", value)

    print("src:", src.as_posix())


if __name__ == "__main__":
    app()
