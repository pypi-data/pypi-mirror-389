import typer
from mecom import MeComSerial

from typing_extensions import Annotated

from discover import find_first_tec

read_app = typer.Typer()

COMMAND_TABLE = {
    "loop status": [1200, ""],
    "object temperature": [1000, "degC"],
    "target object temperature": [3000, "degC"],
    "output current": [1020, "A"],
    "output voltage": [1021, "V"],
    "sink temperature": [1001, "degC"],
    "ramp temperature": [1011, "degC"],
}

@read_app.command()
def temperature(serial_port: Annotated[str, typer.Argument()] = None) -> None:

    if serial_port is None:
        serial_port = find_first_tec()

    serial_port = serial_port.upper()
    
    sesh = MeComSerial(serialport=serial_port)
    id = sesh.identify()
    channel = 1
    temperature = sesh.get_parameter(parameter_id=3000, address=id, parameter_instance=channel)
    print(f"{temperature}℃")


