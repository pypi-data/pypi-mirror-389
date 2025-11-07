import typer

import read
import discover

app = typer.Typer()

app.add_typer(read.read_app, name="read", help="Query a value from the TEC")

@app.command(name="discover")
def find_first():
    """Find the first Meerstetter TEC device"""
    discover.discover()

if __name__ == "__main__":
    app()