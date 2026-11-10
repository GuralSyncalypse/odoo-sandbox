from odoo import fields, models


class TelesalesDataPool(models.Model):
    _name = "telesales.data.pool"
    _description = "Daily Data Pool"
    _order = "pool_date, id"

    name = fields.Char(required=True)
    pool_date = fields.Date(required=True, default=fields.Date.today, index=True)
    data_type_id = fields.Many2one("telesales.data.type", required=True, ondelete="restrict", index=True)
    item_ids = fields.One2many("telesales.data.item", "pool_id")
    active = fields.Boolean(default=True)
