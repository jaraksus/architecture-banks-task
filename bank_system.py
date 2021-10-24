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

        TAccount.all[id] = self

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
            TAccount.all[receiver_id] += amount

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

        if self.funds < amount:
            return Status.Error("Insufficient funds")

        status = self.transaction_manager.new_transaction(
            self,
            None,
            amount,
            ETransactionType.A2C,
        )

        if status.IsOk():
            self.funds -= amount

        return status

    def update_interest(self, datetime: datetime):
        raise NotImplementedError("update_interest must be implemented")


class TDebitAccount(TAccount):
    def __init__(self, bank, client_info, interest_rate, transaction_manager):
        TAccount.__init__(self, bank, client_info, EAccountType.DEBIT, transaction_manager)

        self.interest_rate = interest_rate

        self.unpaid_interest = 0
        self.funds = 0

    def update_interest(self, datetime: datetime):
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
        return TAccount.withdraw(self, amount)
    
    def update_interest(self, datetime: datetime):
        self.unpaid_interest += self.funds * self.interest_rate

        if datetime <= self.end_datetime and datetime.day == TAccount.FIRST_DAY_OF_THE_MONTH:
            self.funds += self.unpaid_interest
            self.unpaid_interest = 0

        if datetime >= self.end_datetime:
            self.withdraw_available = True


class TBank(object):
    ONE_YEAR = timedelta(days=365)

    def __init__(self, name: str, time_manager: ITimeManager, transaction_manager):
        self.name = name
        self.time_manager = time_manager
        self.transaction_manager = transaction_manager

        self.accounts = {}
        self.interest_rate = 0
        self.limit_for_suspicious_accounts = 0

    def set_interest_rate(self, interest_rate):
        self.interest_rate = interest_rate
    
    def set_limit_for_suspicious_accounts(self, limit):
        self.limit_for_suspicious_accounts = limit

    def new_account(self, client_info: TClient.TInfo, type: EAccountType):
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
        else:
            raise RuntimeError("unknown account type")

        account.set_suspicious_limit(self.limit_for_suspicious_accounts)
        self.accounts[client_info.client_id].append(account)
    
    def update_client_info(self, client_info: TClient.TInfo):
        if not client_info.client_id in self.accounts.keys():
            return

        for account in self.accounts[client_info.client_id]:
            account.update_client_info(client_info)
    
    def update_interests(self):
        for client_id in self.accounts.keys():
            for account in self.accounts[client_id]:
                account.update_interest(self.time_manager.get_datetime())

    def verify(self, transaction):
        return True


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
