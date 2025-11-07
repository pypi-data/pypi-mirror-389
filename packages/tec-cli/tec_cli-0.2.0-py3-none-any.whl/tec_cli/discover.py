import platform
from time import time
from mecom import MeComSerial, ResponseException, WrongChecksum
from serial import SerialException
from serial.serialutil import PortNotOpenError

MAX_COM = 256

def find_first_tec() -> str:
    if platform.system() != "Windows":
        start_index = 0
        base_name = "/dev/ttyUSB"
    else:
        start_index = 1
        base_name = "COM"

    scan_start_time = time()
    session = None
    while True:
        for i in range(start_index, MAX_COM + 1):
            try:
                serial_port = base_name + str(i)
                session = MeComSerial(serialport=serial_port)
                return serial_port
            except SerialException:
                pass
        if session is not None or (time() - scan_start_time) >= self.scan_timeout:
            break
        sleep(0.1) # 100 ms wait time between each scan attempt
    if session is None:
        raise PortNotOpenError


def discover() -> None:
    first = find_first_tec()
    print(first)