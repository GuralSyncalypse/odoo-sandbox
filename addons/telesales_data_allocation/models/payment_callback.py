from odoo import fields, models


class TelesalesPaymentCallback(models.Model):
    _name = "telesales.payment.callback"
    _description = "Verified VietQR Payment Callback"
    _order = "id desc"

    provider = fields.Selection([("vietqr", "VietQR")], default="vietqr", required=True)
    transaction_id = fields.Char(required=True, index=True)
    order_id = fields.Char(required=True, index=True)
    transaction_time = fields.Char(required=True)
    amount = fields.Integer(required=True)
    reference_number = fields.Char()
    bank_account = fields.Char()
    transaction_type = fields.Char()
    signature = fields.Char(required=True)
    payload = fields.Json(required=True)
    state = fields.Selection(
        [("verified", "Verified"), ("rejected", "Rejected")],
        default="verified",
        required=True,
        index=True,
    )
    received_at = fields.Datetime(default=fields.Datetime.now, required=True, readonly=True)

    _provider_transaction_unique = models.Constraint("UNIQUE(provider, transaction_id)", "Payment callback already exists.")
    _amount_positive = models.Constraint("CHECK(amount > 0)", "Callback amount must be positive.")
