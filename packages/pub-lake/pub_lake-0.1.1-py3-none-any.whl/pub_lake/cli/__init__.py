"""Console script for pub_lake."""

from logging import WARNING, basicConfig

from typer import Typer

from pub_lake.cli.preprints import app as preprints_app

basicConfig(level=WARNING)

app = Typer()
app.add_typer(preprints_app, name="preprints")


if __name__ == "__main__":
    app()
