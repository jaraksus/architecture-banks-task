from util.gen import TNoRepetitionGenerator


class TClient(object):
    IdsGen = TNoRepetitionGenerator()
    IdSize = 32

    def __init__(self, name: str, surname: str, address=None, passport=None):
        self.id = TClient.IdsGen.gen(TClient.IdSize)

        self.name = name
        self.surname = surname
        self.address = address
        self.passport = passport

    def __del__(self):
        TClient.IdsGen.free(self.id)


class TClientManager(object):
    def __init__(self):
        self.clients = {}

    def new_client(self, name: str, surname: str, address=None, passport=None):
        client = TClient(name, surname, address, passport)
        self.clients[client.id] = client
        return client.id

    def get_clients_ids(self):
        return list(self.clients.keys())

    def get_all_clients(self):
        return self.clients
    
    def get_client(self, client_id):
        if not client_id in self.clients.keys():
            return None
        return self.clients[client_id]
