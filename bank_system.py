from time_system import ITimeManager

from util.gen import TNoRepetitionGenerator
from util.status import Status, ValueHolder

from datetime import datetime, timedelta
from enum import Enum


class EAccountType(Enum):
    DEBIT   = 1
    DEPOSIT = 2
    CREDIT  = 3


class IAccount(object):
    all = []

    FIRST_DAY_OF_THE_MONTH = 1

    IdsGen = TNoRepetitionGenerator()
    IdSize = 32

    def __init__(self, client_id, type: EAccountType):
        self.client_id = client_id
        self.type = type
        self.id = IAccount.IdsGen.gen(IAccount.IdSize)
        IAccount.all.append(self)

    def top_up(self, amount) -> Status:
        raise NotImplementedError("top_up must be implemented")
    
    def withdraw(self, amount) -> Status:
        raise NotImplementedError("withdraw must be implemented")

    def update_interest(self, datetime: datetime):
        raise NotImplementedError("update_interest must be implemented")


class TDebitAccount(IAccount):
    def __init__(self, client_id, interest_rate):
        IAccount.__init__(self, client_id, EAccountType.DEBIT)

        self.interest_rate = interest_rate

        self.unpaid_interest = 0
        self.funds = 0
    
    def top_up(self, amount) -> Status:
        self.funds += amount
        return Status.Ok()
    
    def withdraw(self, amount) -> Status:
        if self.funds < amount:
            return Status.Error("Insufficient funds")

        self.funds -= amount
        return Status.Ok()
    
    def update_interest(self, datetime: datetime):
        self.unpaid_interest += self.funds * self.interest_rate

        if datetime.day == IAccount.FIRST_DAY_OF_THE_MONTH:
            self.funds += self.unpaid_interest
            self.unpaid_interest = 0


class TDepositAccount(IAccount):
    def __init__(self, client_id, initial_funds, interest_rate, end_datetime: datetime):
        IAccount.__init__(self, client_id, EAccountType.DEPOSIT)

        self.funds = initial_funds
        self.interest_rate = interest_rate
        self.end_datetime = end_datetime

        self.withdraw_available = False

    def top_up(self, amount) -> Status:
        self.funds += amount
        return Status.Ok()

    def withdraw(self, amount) -> Status:
        if not self.withdraw_available:
            return Status.Error("withdraw not available")
        
        self.funds -= amount
        return Status.Ok()
    
    def update_interest(self, datetime: datetime):
        self.unpaid_interest += self.funds * self.interest_rate

        if datetime <= self.end_datetime and datetime.day == IAccount.FIRST_DAY_OF_THE_MONTH:
            self.funds += self.unpaid_interest
            self.unpaid_interest = 0

        if datetime >= self.end_datetime:
            self.withdraw_available = True


class TBank(object):
    ONE_YEAR = timedelta(days=365)

    def __init__(self, name: str, time_manager: ITimeManager):
        self.name = name
        self.interest_rate = 0

        self.accounts = {}

        self.time_manager = time_manager
    
    def set_interest_rate(self, interest_rate):
        self.interest_rate = interest_rate

    def new_account(self, client_id, type: EAccountType):
        if not client_id in self.accounts.keys():
            self.accounts[client_id] = []

        if type == EAccountType.DEBIT:
            self.accounts[client_id].append(TDebitAccount(
                client_id=client_id,
                interest_rate=self.interest_rate,
            ))
    
    def update_interests(self):
        for client_id in self.accounts.keys():
            for account in self.accounts[client_id]:
                account.update_interest(self.time_manager.get_datetime())


class TBankManager(object):
    def __init__(self):
        self.banks = {}
    
    def new_bank(self, name: str, time_manager: ITimeManager) -> Status:
        if name in self.banks.keys():
            return Status.Error(f"Bank with the name '{name}' already exists")

        self.banks[name] = TBank(name, time_manager)
        return Status.Ok()
    
    def get_bank(self, name) -> ValueHolder:
        if not name in self.banks.keys():
            return ValueHolder.Error(f"No bank with name {name}")

        return ValueHolder.Ok(self.banks[name])
