from odoo import fields, models


class TelesalesDataItem(models.Model):
    _name = "telesales.data.item"
    _description = "Redeemable Data Item"
    _order = "pool_date, id"

    pool_id = fields.Many2one("telesales.data.pool", required=True, ondelete="cascade", index=True)
    pool_date = fields.Date(related="pool_id.pool_date", store=True, index=True)
    data_type_id = fields.Many2one(related="pool_id.data_type_id", store=True, index=True)
    payload = fields.Json(required=True, help="Data payload returned only to its assigned account.")
    state = fields.Selection(
        [("available", "Available"), ("reserved", "Reserved"), ("assigned", "Assigned"), ("expired", "Expired"), ("refunded", "Refunded")],
        default="available",
        required=True,
        index=True,
    )
    redemption_request_id = fields.Many2one("telesales.data.redemption.request", ondelete="set null", index=True)
    assigned_account_id = fields.Many2one("telesales.api.account", ondelete="set null", index=True)
