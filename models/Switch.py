from pydantic import BaseModel
from typing import Optional
import telnetlib 
import time

class Credentials(BaseModel):
    user: str
    password: str

class SSHData(Credentials):
    max_connections: int

class Switch(BaseModel):
    id: str
    ip: str
    model: str
    vendor: str
    connection: str
    credentials: Credentials
    ssh: Optional[SSHData]
    def EnablePoe(self, port: str):
        tn = telnetlib.Telnet(self.ip)
        tn.read_until(b"User:")
        tn.write(self.credentials.user.encode('ascii') + b"\r")
        tn.read_until(b"Password:")
        tn.write(self.credentials.password.encode('ascii') + b"\r")
        tn.write(b"enable" + b"\r")
        tn.write(b"config" + b"\r")
        tn.write(b"interface gigabitEthernet " + port.encode('ascii') + b"\r")
        tn.write(b"power inline supply enable" + b"\r")
        #tn.write(b"exit\r")
        #tn.write(b"exit\r")
        #tn.write(b"exit\r")
        #tn.write(b"exit\r")
        #lastpost = tn.read_all().decode('ascii')
        #print(lastpost)
        tn.close()
    def DisablePoe(self, port: str):
        tn = telnetlib.Telnet(self.ip)
        tn.read_until(b"User:")
        tn.write(self.credentials.user.encode('ascii') + b"\r")
        tn.read_until(b"Password:")
        tn.write(self.credentials.password.encode('ascii') + b"\r")
        tn.write(b"enable" + b"\r")
        tn.write(b"config" + b"\r")
        tn.write(b"interface gigabitEthernet " + port.encode('ascii') + b"\r")
        tn.write(b"power inline supply disable" + b"\r")
        #tn.write(b"exit\r")
        #tn.write(b"exit\r")
        #tn.write(b"exit\r")
        #tn.write(b"exit\r")
        #lastpost = tn.read_all().decode('ascii')
        #print(lastpost)
        tn.close()


