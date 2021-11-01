from numpy import select
from bank_system import EAccountType, TAccount
from time_system import TToyTimeManager
from api import API

from datetime import datetime, timedelta
import math


class TestScenarios:
    def setup(self):
        self.time_manager = TToyTimeManager(
            start_datetime=datetime(year=2021, month=9, day=3),
            step=timedelta(days=1),
        )

        self.api = API(self.time_manager)

    def teardown(self):
        TAccount.all = {}

    def test_create_client(self):
        client_id = self.api.new_client({
            "name": "Vasya",
            "surname": "Beliy",
        })

        assert(len(self.api.client_manager.clients) == 1)

        client = self.api.client_manager.get_client(client_id)
        assert(client is not None)

        assert(client.name == "Vasya")
        assert(client.surname == "Beliy")

    def test_update_client_info(self):
        client_id = self.api.new_client({
            "name": "Vasya",
            "surname": "Beliy",
        })

        client_info = self.api.client_manager.get_client(client_id).info
        assert(client_info.client_id == client_id)
        assert(client_info.is_suspicious)

        self.api.update_client_optional_info(
            client_id,
            {
                "address": "moscow",
                "passport": "123456789",
            }
        )

        client_info = self.api.client_manager.get_client(client_id).info
        assert(client_info.client_id == client_id)
        assert(not client_info.is_suspicious)

    def test_create_bank(self):
        result = self.api.new_bank({
            "name": "Sber"
        })
        assert(result.IsOk())

    def test_create_debit_account(self):
        client_id = self.api.new_client({
            "name": "Vasya",
            "surname": "Beliy",
        })

        self.api.new_bank({
            "name": "Sber"
        })

        self.api.new_account(client_id, "Sber", "debit")

        assert(len(TAccount.all.items()) == 1)

        account = list(TAccount.all.items())[0][1]
        assert(account.bank.name == "Sber")
        assert(account.client_id == client_id)
        assert(account.type == EAccountType.DEBIT)

    def test_create_deposit_account(self):
        client_id = self.api.new_client({
            "name": "Vasya",
            "surname": "Beliy",
        })

        self.api.new_bank({
            "name": "Sber"
        })

        account_id = self.api.new_account(client_id, "Sber", "deposit", {"initial_funds": 10})

        assert(len(TAccount.all.items()) == 1)

        account = TAccount.all[account_id]
        assert(account.bank.name == "Sber")
        assert(account.client_id == client_id)
        assert(account.type == EAccountType.DEPOSIT)

    def test_create_credit_account(self):
        client_id = self.api.new_client({
            "name": "Vasya",
            "surname": "Beliy",
        })

        self.api.new_bank({
            "name": "Sber"
        })

        account_id = self.api.new_account(client_id, "Sber", "credit")

        assert(len(TAccount.all.items()) == 1)

        account = TAccount.all[account_id]
        assert(account.bank.name == "Sber")
        assert(account.client_id == client_id)
        assert(account.type == EAccountType.CREDIT)

    def test_top_up(self):
        vasya_id = self.api.new_client({
            "name": "Vasya",
            "surname": "Beliy",
            "optional_fields": {
                "address": "addr",
                "passport": "pas"
            }
        })

        self.api.new_bank({
            "name": "Sber"
        })

        account_id = self.api.new_account(vasya_id, "Sber", "debit")

        self.api.top_up(account_id, 10.5)

        account = TAccount.all[account_id]
        assert(math.isclose(account.funds, 10.5))

        suspicious_id = self.api.new_client({
            "name": "V**d***r",
            "surname": "P*t*n",
        })

        suspicious_account_id = self.api.new_account(suspicious_id, "Sber", "debit")
        account = TAccount.all[suspicious_account_id]
        assert(math.isclose(account.funds, 0))

    def test_withdraw(self):
        vasya_id = self.api.new_client({
            "name": "Vasya",
            "surname": "Beliy",
            "optional_fields": {
                "address": "addr",
                "passport": "pas"
            }
        })

        self.api.new_bank({
            "name": "Sber"
        })

        account_id = self.api.new_account(vasya_id, "Sber", "debit")
        self.api.top_up(account_id, 10.5)

        res = self.api.withdraw(vasya_id, account_id, 5.5)
        assert(res.IsOk())

        account = TAccount.all[account_id]
        assert(math.isclose(account.funds, 5))

    def test_send(self):
        vasya_id = self.api.new_client({
            "name": "Vasya",
            "surname": "Beliy",
            "optional_fields": {
                "address": "addr",
                "passport": "pas"
            }
        })
        petya_id = self.api.new_client({
            "name": "Petya",
            "surname": "Volkov",
            "optional_fields": {
                "address": "addr",
                "passport": "pas"
            }
        })

        self.api.new_bank({
            "name": "Sber"
        })

        vasya_account_id = self.api.new_account(vasya_id, "Sber", "debit")
        self.api.top_up(vasya_account_id, 10.5)
        petya_account_id = self.api.new_account(vasya_id, "Sber", "debit")

        self.api.send(vasya_id, vasya_account_id, petya_account_id, 5.5)

        assert(math.isclose(TAccount.all[vasya_account_id].funds, 5))
        assert(math.isclose(TAccount.all[petya_account_id].funds, 5.5))
