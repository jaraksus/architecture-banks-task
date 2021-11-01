from util.gen import TNoRepetitionGenerator

from enum import Enum


class TClient(object):
    IdsGen = TNoRepetitionGenerator()
    IdSize = 32

    class TOptionalFields(Enum):
        ADDRESS = 1
        PASSPORT = 2

        def __str__(self):
            return self.name.lower()
    
    class TInfo:
        def __init__(self, client):
            self.client_id = client.id
            self.is_suspicious = not client.has_all_fields()

    def __init__(self, name: str, surname: str):
        self.id = TClient.IdsGen.gen(TClient.IdSize)

        self.name = name
        self.surname = surname

        self.optional_fields = {}

    @property
    def info(self):
        return TClient.TInfo(self)

    def update_optional_fields(self, fields):
        for field, value in fields.items():
            self.optional_fields[field] = value

    def has_all_fields(self) -> bool:
        for field in TClient.TOptionalFields:
            if not str(field) in self.optional_fields:
                return False
        return True

    def __del__(self):
        TClient.IdsGen.free(self.id)


class TClientManager(object):
    def __init__(self):
        self.clients = {}

    def new_client(self, name: str, surname: str, optional_fields={}):
        client = TClient(name, surname)
        client.update_optional_fields(optional_fields)

        self.clients[client.id] = client
        return client.id

    def is_client_suspicious(self, client_id):
        if not client_id in self.clients.keys():
            return None
        return not self.clients[client_id].has_all_fields()

    def get_client(self, client_id) -> TClient:
        if not client_id in self.clients.keys():
            return None
        return self.clients[client_id]
