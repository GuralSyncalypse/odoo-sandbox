from odoo.tests.common import TransactionCase


class TestAdminAudit(TransactionCase):
    def setUp(self):
        super().setUp()
        self.account = self.env["telesales.api.account"].create({"external_user_id": "admin-audit-user"})
        self.data_type = self.env["telesales.data.type"].create({"name": "Lead", "code": "lead-audit"})
        self.env["ir.config_parameter"].sudo().set_param("telesales_data_allocation.price.lead-audit", "10")
        self.env["telesales.wallet.service"]._post_entry(self.account.wallet_id, 10, "topup", "audit:credit")
        pool = self.env["telesales.data.pool"].create({"name": "Audit pool", "pool_date": "2026-11-10", "data_type_id": self.data_type.id})
        self.env["telesales.data.item"].create({"pool_id": pool.id, "payload": {"phone": "1"}})

    def test_refund_approval_records_admin_audit(self):
        redemption, _idempotent = self.env["telesales.allocation.service"].create_redemption_request(
            self.account, self.data_type, 1, "audit:redemption"
        )
        redemption.action_approve("external-admin")
        refund = self.env["telesales.refund.request"].create({
            "account_id": self.account.id,
            "redemption_request_id": redemption.id,
            "points": 10,
            "reason": "unreachable",
            "idempotency_key": "audit:refund",
        })

        refund.action_approve("external-admin")

        self.assertEqual(refund.state, "approved")
        self.assertEqual(refund.approved_by, "external-admin")
        self.assertTrue(refund.approved_at)
