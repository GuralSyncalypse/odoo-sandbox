from odoo import fields, models
from odoo.exceptions import ValidationError


class TelesalesDataRedemptionRequest(models.Model):
    _name = "telesales.data.redemption.request"
    _description = "Data Redemption Request"
    _order = "id desc"

    account_id = fields.Many2one("telesales.api.account", required=True, ondelete="restrict", index=True)
    wallet_id = fields.Many2one(related="account_id.wallet_id", store=True, index=True)
    data_type_id = fields.Many2one("telesales.data.type", required=True, ondelete="restrict", index=True)
    quantity = fields.Integer(default=1, required=True)
    point_price = fields.Integer(required=True, readonly=True)
    reserved_points = fields.Integer(required=True, readonly=True)
    idempotency_key = fields.Char(required=True, index=True)
    state = fields.Selection(
        [("pending", "Pending approval"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="pending",
        required=True,
        index=True,
    )
    item_ids = fields.One2many("telesales.data.item", "redemption_request_id")
    approved_by = fields.Char(readonly=True)
    approved_at = fields.Datetime(readonly=True)

    _idempotency_unique = models.Constraint("UNIQUE(account_id, idempotency_key)", "Idempotency key was already used.")
    _quantity_positive = models.Constraint("CHECK(quantity > 0)", "Quantity must be positive.")

    @classmethod
    def values_for_new_request(cls, data_type, quantity):
        price = data_type.get_price_points()
        return {"point_price": price, "reserved_points": price * quantity}

    def action_approve(self, approved_by):
        self.ensure_one()
        if self.state != "pending":
            raise ValidationError("Only pending redemption requests can be approved.")
        self.env["telesales.allocation.service"].sudo().approve_redemption(self, approved_by)
        return True
