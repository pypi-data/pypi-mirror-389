import typer

import read

app = typer.Typer()

app.add_typer(read.read_app, name="read", help="Query a value from the TEC")

if __name__ == "__main__":
    app()