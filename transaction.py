from enum import Enum


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

    def new_transaction(self, id_from, id_to, amount, type):
        self.all_transactions.append(TTransaction(
            id_from, id_to,
            amount,
            type,
            self.time_manager.get_datetime()
        ))
