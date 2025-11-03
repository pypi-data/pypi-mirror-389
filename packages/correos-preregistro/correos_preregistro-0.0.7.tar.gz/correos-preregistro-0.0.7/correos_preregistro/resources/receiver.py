from dataclasses import dataclass


@dataclass
class Receiver:
    name: str
    address: str
    city: str
    state: str
    zip: str
    phone: str
    email: str
    lang: str
    surname: str = None
    nif: str = None
    sms_phone: str = None
