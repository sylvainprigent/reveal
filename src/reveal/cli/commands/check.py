import typer

app = typer.Typer()


@app.callback(invoke_without_command=True)
def run(
    project: str = typer.Option(..., "-p", "--project"),
):
    print("CHECK")
    print(project)