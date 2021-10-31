from client_system import TClient
from time_system import ITimeManager
from transaction import ETransactionType, TTransactionManager

from util.gen import TNoRepetitionGenerator
from util.status import Status, ValueHolder

from datetime import datetime, timedelta
from enum import Enum


class EAccountType(Enum):
    DEBIT   = 1
    DEPOSIT = 2
    CREDIT  = 3


class TAccount(object):
    all = {}

    FIRST_DAY_OF_THE_MONTH = 1

    IdsGen = TNoRepetitionGenerator()
    IdSize = 32

    def __init__(
        self,
        bank,
        client_info: TClient.TInfo,
        type: EAccountType,
        transaction_manager: TTransactionManager,
    ):
        self.bank = bank
        self.client_id = client_info.client_id
        self.type = type
        self.transaction_manager = transaction_manager
        self.id = TAccount.IdsGen.gen(TAccount.IdSize)

        self.is_suspicious = client_info.is_suspicious
        self.suspicious_limit = 0

        self.funds = 0

        TAccount.all[self.id] = self
    
    def __del__(self):
        del TAccount.all[self.id]
        TAccount.IdsGen.free(self.id)

    def set_suspicious_limit(self, suspicious_limit):
        self.suspicious_limit = suspicious_limit
    
    def update_client_info(self, client_info: TClient.TInfo):
        if client_info.client_id != self.client_id:
            raise RuntimeError(f"client_id must be equal: {client_info.client_id} != {self.client_id}")

        self.is_suspicious = client_info.is_suspicious

    def send(self, receiver_id, amount) -> Status:
        if self.funds < amount:
            return Status.Error("not enought funds")

        status = self.transaction_manager.new_transaction(
            self,
            TAccount.all[receiver_id],
            amount,
            ETransactionType.A2A
        )

        if status.IsOk():
            self.funds -= amount
            TAccount.all[receiver_id].funds += amount

        return status

    def top_up(self, amount) -> Status:
        if self.is_suspicious and amount > self.suspicious_limit:
            return Status.Error(f"amount is higher then suspicious limit: {amount} > {self.suspicious_limit}")

        status = self.transaction_manager.new_transaction(
            None,
            self,
            amount,
            ETransactionType.C2A,
        )

        if status.IsOk():
            self.funds += amount

        return status

    def withdraw(self, amount) -> Status:
        if self.is_suspicious and amount > self.suspicious_limit:
            return Status.Error(f"amount is higher then suspicious limit: {amount} > {self.suspicious_limit}")

        status = self.transaction_manager.new_transaction(
            self,
            None,
            amount,
            ETransactionType.A2C,
        )

        if status.IsOk():
            self.funds -= amount

        return status

    def update(self, datetime: datetime):
        raise NotImplementedError("update must be implemented")


class TDebitAccount(TAccount):
    def __init__(self, bank, client_info, interest_rate, transaction_manager):
        TAccount.__init__(self, bank, client_info, EAccountType.DEBIT, transaction_manager)

        self.interest_rate = interest_rate

        self.unpaid_interest = 0

    def withdraw(self, amount) -> Status:
        if self.funds < amount:
            return Status.Error("Insufficient funds")

        return super().withdraw(amount)

    def update(self, datetime: datetime):
        self.unpaid_interest += self.funds * self.interest_rate

        if datetime.day == TAccount.FIRST_DAY_OF_THE_MONTH:
            self.funds += self.unpaid_interest
            self.unpaid_interest = 0


class TDepositAccount(TAccount):
    def __init__(self, bank, client_info, initial_funds, interest_rate, end_datetime: datetime, transaction_manager):
        TAccount.__init__(self, bank, client_info, EAccountType.DEPOSIT, transaction_manager)

        self.funds = initial_funds
        self.interest_rate = interest_rate
        self.end_datetime = end_datetime

        self.withdraw_available = False

    def withdraw(self, amount) -> Status:
        if not self.withdraw_available:
            return Status.Error("withdraw not available")
        if self.funds < amount:
            return Status.Error("Insufficient funds")

        return TAccount.withdraw(self, amount)
    
    def update(self, datetime: datetime):
        self.unpaid_interest += self.funds * self.interest_rate

        if datetime <= self.end_datetime and datetime.day == TAccount.FIRST_DAY_OF_THE_MONTH:
            self.funds += self.unpaid_interest
            self.unpaid_interest = 0

        if datetime >= self.end_datetime:
            self.withdraw_available = True


class TCreditAccount(TAccount):
    def __init__(self, bank, client_info, transaction_manager, dayly_fee):
        TAccount.__init__(self, bank, client_info, EAccountType.CREDIT, transaction_manager)

        self.dayly_fee = dayly_fee

    def update(self, datetime: datetime):
        if self.funds < 0:
            self.funds -= self.dayly_fee


class TBank(object):
    ONE_YEAR = timedelta(days=365)

    def __init__(self, name: str, time_manager: ITimeManager, transaction_manager):
        self.name = name
        self.time_manager = time_manager
        self.transaction_manager = transaction_manager

        self.accounts = {}
        self.interest_rate = 0
        self.credit_dayly_fee = 0
        self.limit_for_suspicious_accounts = 0

        self.black_list = set()

    def set_interest_rate(self, interest_rate):
        self.interest_rate = interest_rate
    
    def set_credit_dayly_fee(self, dayle_fee):
        self.credit_dayly_fee = dayle_fee

    def set_limit_for_suspicious_accounts(self, limit):
        self.limit_for_suspicious_accounts = limit

    def add_to_black_list(self, client_id):
        self.black_list.add(client_id)

    def new_account(self, client_info: TClient.TInfo, type: EAccountType, kwargs={}):
        if not client_info.client_id in self.accounts.keys():
            self.accounts[client_info.client_id] = []

        account = None
        if type == EAccountType.DEBIT:
            account = TDebitAccount(
                self,
                client_info=client_info,
                interest_rate=self.interest_rate,
                transaction_manager=self.transaction_manager,
            )
        elif type == EAccountType.DEPOSIT:
            account = TDepositAccount(
                self,
                client_info,
                kwargs['initial_funds'],
                self.interest_rate,
                self.time_manager.get_datetime() + TBank.ONE_YEAR,
                self.transaction_manager
            )
        elif type == EAccountType.CREDIT:
            account = TCreditAccount(
                self,
                client_info,
                self.transaction_manager,
                self.credit_dayly_fee
            )

        account.set_suspicious_limit(self.limit_for_suspicious_accounts)
        self.accounts[client_info.client_id].append(account)

        return account.id
    
    def update_client_info(self, client_info: TClient.TInfo):
        if not client_info.client_id in self.accounts.keys():
            return

        for account in self.accounts[client_info.client_id]:
            account.update_client_info(client_info)
    
    def update_accounts(self):
        for client_id in self.accounts.keys():
            for account in self.accounts[client_id]:
                account.update(self.time_manager.get_datetime())

    def verify(self, transaction):
        return (
            not transaction.id_from in self.black_list and
            not transaction.id_to in self.black_list
        )

class TBankManager(object):
    def __init__(self, transaction_manager: TTransactionManager):
        self.banks = {}
        self.transaction_manager = transaction_manager
    
    def new_bank(self, name: str, time_manager: ITimeManager) -> Status:
        if name in self.banks.keys():
            return Status.Error(f"Bank with the name '{name}' already exists")

        self.banks[name] = TBank(name, time_manager, self.transaction_manager)
        return Status.Ok()

    def get_bank(self, name) -> ValueHolder:
        if not name in self.banks.keys():
            return ValueHolder.Error(f"No bank with name {name}")

        return ValueHolder.Ok(self.banks[name])

    def get_all_banks(self):
        return self.banks
