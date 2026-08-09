import typer

app = typer.Typer()


@app.callback(invoke_without_command=True)
def run(
    filename: str = typer.Option(..., "-f", "--filename"),
    project: str = typer.Option(..., "-p", "--project"),
):
    print("INSPECT")
    print(filename)
    print(project)