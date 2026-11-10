from odoo.tests.common import TransactionCase


class TestWalletAndAllocation(TransactionCase):
    def setUp(self):
        super().setUp()
        self.account = self.env["telesales.api.account"].create({"external_user_id": "website-user"})
        self.data_type = self.env["telesales.data.type"].create({"name": "Lead", "code": "lead"})
        self.env["ir.config_parameter"].sudo().set_param("telesales_data_allocation.price.lead", "10")

    def test_wallet_is_ledger_derived_and_allocation_is_fifo(self):
        wallet = self.account.wallet_id
        self.env["telesales.wallet.service"]._post_entry(wallet, 20, "topup", "test:credit")
        first_pool = self.env["telesales.data.pool"].create({
            "name": "Older", "pool_date": "2026-01-01", "data_type_id": self.data_type.id,
        })
        second_pool = self.env["telesales.data.pool"].create({
            "name": "Newer", "pool_date": "2026-01-02", "data_type_id": self.data_type.id,
        })
        first = self.env["telesales.data.item"].create({"pool_id": first_pool.id, "payload": {"phone": "1"}})
        self.env["telesales.data.item"].create({"pool_id": second_pool.id, "payload": {"phone": "2"}})
        values = self.env["telesales.data.redemption.request"].values_for_new_request(self.data_type, 1)
        redemption = self.env["telesales.data.redemption.request"].create({
            "account_id": self.account.id, "data_type_id": self.data_type.id,
            "quantity": 1, "idempotency_key": "redeem-1", **values,
        })
        self.assertEqual(wallet.get_balances()[2], 10)
        redemption.action_approve("admin")
        self.assertEqual(redemption.state, "approved")
        self.assertEqual(first.state, "assigned")
        self.assertEqual(wallet.get_balances()[0], 10)

    def test_pending_redemption_reserves_points(self):
        wallet = self.account.wallet_id
        self.env["telesales.wallet.service"]._post_entry(wallet, 10, "topup", "test:reserve")
        values = self.env["telesales.data.redemption.request"].values_for_new_request(self.data_type, 1)
        self.env["telesales.data.redemption.request"].create({
            "account_id": self.account.id, "data_type_id": self.data_type.id,
            "quantity": 1, "idempotency_key": "reserve-1", **values,
        })
        self.assertEqual(wallet.get_balances()[0], 10)
        self.assertEqual(wallet.get_balances()[2], 0)

    def test_redemption_for_full_available_balance_can_be_approved(self):
        wallet = self.account.wallet_id
        self.env["telesales.wallet.service"]._post_entry(wallet, 10, "topup", "test:full-balance")
        pool = self.env["telesales.data.pool"].create({
            "name": "Pool", "pool_date": "2026-01-01", "data_type_id": self.data_type.id,
        })
        self.env["telesales.data.item"].create({"pool_id": pool.id, "payload": {"phone": "1"}})
        redemption, _idempotent = self.env["telesales.allocation.service"].create_redemption_request(
            self.account, self.data_type, 1, "full-balance"
        )
        redemption.action_approve("admin")
        self.assertEqual(redemption.state, "approved")
        self.assertEqual(wallet.get_balances()[0], 0)

    def test_manual_topup_approval_posts_credit_without_callback(self):
        topup = self.env["telesales.point.topup.request"].create({
            "account_id": self.account.id, "order_id": "manual-order", "points": 25,
            "expected_amount": 100000, "idempotency_key": "manual-topup",
        })
        topup.action_approve("admin")
        self.assertEqual(topup.state, "approved")
        self.assertEqual(topup.approval_method, "manual")
        self.assertEqual(self.account.wallet_id.get_balances()[0], 25)
