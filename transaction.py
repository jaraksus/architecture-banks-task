from enum import Enum

from util.status import Status


class ETransactionType(Enum):
    A2A = 1 # account to account / перевод средств
    C2A = 2 # client to account  / ввод средств
    A2C = 3 # account to client  / вывод средств


class TTransaction(object):
    def __init__(self, id_from, id_to, amount, type: ETransactionType, datetime):
        self.id_from = id_from
        self.id_to = id_to
        self.amount = amount
        self.type = type
        self.datetime = datetime


class TTransactionManager(object):
    def __init__(self, time_manager):
        self.time_manager = time_manager

        self.all_transactions = []

    def new_transaction(self, account_from, account_to, amount, type) -> Status:
        id_from = account_from.id if account_from is not None else None
        id_to = account_to.id if account_to is not None else None

        transaction = TTransaction(
            id_from, id_to,
            amount,
            type,
            self.time_manager.get_datetime()
        )

        if type == ETransactionType.A2A:
            verifiers = [
                account_from.bank,
                account_to.bank,
            ]

            for verifier in verifiers:
                if not verifier.verify(transaction):
                    return Status.Error("not verified")

        self.all_transactions.append(transaction)
        return Status.Ok()
