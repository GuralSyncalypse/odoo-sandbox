from odoo import fields, models
from odoo.exceptions import ValidationError


class TelesalesPointTopupRequest(models.Model):
    _name = "telesales.point.topup.request"
    _description = "Point Top-up Request"
    _order = "id desc"

    account_id = fields.Many2one("telesales.api.account", required=True, ondelete="restrict", index=True)
    wallet_id = fields.Many2one(related="account_id.wallet_id", store=True, index=True)
    order_id = fields.Char(required=True, index=True)
    points = fields.Integer(required=True)
    expected_amount = fields.Integer(required=True, help="VND amount expected from VietQR.")
    idempotency_key = fields.Char(required=True, index=True)
    state = fields.Selection(
        [("pending", "Pending approval"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="pending",
        required=True,
        index=True,
    )
    callback_id = fields.Many2one("telesales.payment.callback", ondelete="restrict")
    approval_method = fields.Selection(
        [("manual", "Manual bank-statement review"), ("callback", "Verified VietQR callback")],
        readonly=True,
    )
    approved_by = fields.Char(readonly=True)
    approved_at = fields.Datetime(readonly=True)

    _order_id_unique = models.Constraint("UNIQUE(order_id)", "Top-up order ID must be unique.")
    _idempotency_unique = models.Constraint("UNIQUE(account_id, idempotency_key)", "Idempotency key was already used.")
    _points_positive = models.Constraint("CHECK(points > 0)", "Points must be positive.")
    _amount_positive = models.Constraint("CHECK(expected_amount > 0)", "Expected amount must be positive.")

    def action_approve(self, approved_by):
        self.ensure_one()
        if self.state != "pending":
            raise ValidationError("Only pending top-up requests can be approved.")
        if self.callback_id:
            if self.callback_id.state != "verified":
                raise ValidationError("The linked callback must be verified.")
            if self.callback_id.amount != self.expected_amount or self.callback_id.order_id != self.order_id:
                raise ValidationError("The verified callback does not match this top-up request.")
            approval_method = "callback"
        else:
            approval_method = "manual"
        self.env["telesales.wallet.service"].sudo().credit_topup(self, approved_by)
        self.sudo().write({"approval_method": approval_method})
        return True
