from bank_system import EAccountType, TAccount, TBankManager
from client_system import TClientManager
from time_system import ITimeManager
from transaction import TTransactionManager
from util.status import Status


class API(object):
    def __init__(self, time_manager: ITimeManager):
        self.time_manager = time_manager

        self.transaction_manager = TTransactionManager(self.time_manager)
        self.bank_manager = TBankManager(self.transaction_manager)
        self.client_manager = TClientManager()

    def new_client(self, kwargs: dict):
        return self.client_manager.new_client(**kwargs)

    def update_client_optional_info(self, client_id, fields):
        client = self.client_manager.get_client(client_id)
        client.update_optional_fields(fields)

        banks = self.bank_manager.get_all_banks()
        for _, bank in banks.items():
            bank.update_client_info(client.info)

    def new_bank(self, kwargs: dict):
        return self.bank_manager.new_bank(**kwargs, time_manager=self.time_manager)

    def new_account(self, client_id, bank_name: str, type_str: str, kwargs={}):
        type = EAccountType.DEBIT
        if type_str == "debit":
            type = EAccountType.DEBIT
        elif type_str == "deposit":
            type = EAccountType.DEPOSIT
        elif type_str == "credit":
            type = EAccountType.CREDIT

        client_info = self.client_manager.get_client(client_id).info

        bank = self.bank_manager.get_bank(bank_name)
        return bank.Get().new_account(client_info, type, kwargs)

    def top_up(self, account_id, amount):
        account = TAccount.all[account_id]
        return account.top_up(amount)

    def withdraw(self, client_id, account_id, amount):
        account = TAccount.all[account_id]

        if client_id != account.client_id:
            return Status.Error(f"account does not belong to client {client_id}")

        return account.withdraw(amount)

    def send(self, client_id, from_id, to_id, amount):
        account = TAccount.all[from_id]

        if client_id != account.client_id:
            return Status.Error(f"account does not belong to client {client_id}")

        return account.send(to_id, amount)

    def add_to_black_list(self, bank_name, client_id):
        self.bank_manager.get_bank(bank_name).add_to_black_list(client_id)
