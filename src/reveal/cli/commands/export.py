import typer

app = typer.Typer()


@app.callback(invoke_without_command=True)
def run(
    project: str = typer.Option(..., "-p", "--project"),
    filename: str = typer.Option(..., "-f", "--filename"),
):
    print("EXPORT")
    print(project)
    print(filename)