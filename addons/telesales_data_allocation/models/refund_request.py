from odoo import fields, models
from odoo.exceptions import ValidationError


class TelesalesRefundRequest(models.Model):
    _name = "telesales.refund.request"
    _description = "Point Refund Request"
    _order = "id desc"

    account_id = fields.Many2one("telesales.api.account", required=True, ondelete="restrict", index=True)
    redemption_request_id = fields.Many2one("telesales.data.redemption.request", required=True, ondelete="restrict")
    points = fields.Integer(required=True)
    reason = fields.Selection(
        [("rejected", "Data rejected"), ("expired", "Data expired"), ("unreachable", "Unable to contact")],
        required=True,
    )
    state = fields.Selection(
        [("pending", "Pending approval"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="pending",
        required=True,
        index=True,
    )
    idempotency_key = fields.Char(required=True, index=True)
    approved_by = fields.Char(readonly=True)
    approved_at = fields.Datetime(readonly=True)

    _idempotency_unique = models.Constraint("UNIQUE(account_id, idempotency_key)", "Idempotency key was already used.")
    _points_positive = models.Constraint("CHECK(points > 0)", "Refund points must be positive.")

    def action_approve(self, approved_by):
        self.ensure_one()
        if self.state != "pending":
            raise ValidationError("Only pending refund requests can be approved.")
        self.env["telesales.wallet.service"].sudo().credit_refund(self, approved_by)
        return True
