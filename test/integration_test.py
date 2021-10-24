from time_system import TToyTimeManager
from bank_system import *
from client_system import *

from datetime import datetime

class TestSimpleScenarios:
    def setup(self):
        self.time_manager = TToyTimeManager(
            start_datetime=datetime(year=2021, month=9, day=3),
            step=timedelta(days=1),
        )

        self.transaction_manager = TTransactionManager(self.time_manager)

        self.bank_manager = TBankManager(self.transaction_manager)
        self.client_manager = TClientManager()


    def test_create_client(self):
        client_id = self.client_manager.new_client("Vasya", "Beliy")
        assert(len(self.client_manager.clients) == 1)
        
        client = self.client_manager.get_client(client_id)
        assert(client is not None)

        assert(client.name == "Vasya")
        assert(client.surname == "Beliy")

    def test_create_bank(self):
        result = self.bank_manager.new_bank("Sber", self.time_manager)
        assert(result.IsOk())

    def test_create_debit_account(self):
        # create client
        client_id = self.client_manager.new_client("Vasya", "Beliy")

        # create bank
        self.bank_manager.new_bank("Sber", self.time_manager)

        bank = self.bank_manager.get_bank("Sber")
        assert(bank.IsOk)
        bank = bank.Get()

        # create debit account
        bank.new_account(self.client_manager.get_client(client_id).info, EAccountType.DEBIT)
        assert(len(TAccount.all) == 1)
