import typer
from mecompyapi.tec import MeerstetterTEC, SaveToFlashState

from typing_extensions import Annotated

read_app = typer.Typer()

@read_app.command()
def temperature(serial_port: str) -> None:

    serial_port = serial_port.upper()
    
    mc = MeerstetterTEC()
    mc.connect_serial_port(port="COM11")
    print(f"{mc.get_temperature()}℃")
    mc.tear()

