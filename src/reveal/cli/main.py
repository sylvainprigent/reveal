import typer

from reveal.cli.commands.inspect import app as inspect_app
from reveal.cli.commands.check import app as check_app
from reveal.cli.commands.export import app as export_app

app = typer.Typer()

app.add_typer(inspect_app, name="inspect")
app.add_typer(check_app, name="check")
app.add_typer(export_app, name="export")


def main():
    app()