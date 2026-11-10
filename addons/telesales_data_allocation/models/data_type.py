from odoo import fields, models
from odoo.exceptions import ValidationError


class TelesalesDataType(models.Model):
    _name = "telesales.data.type"
    _description = "Redeemable Data Type"
    _rec_name = "name"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)

    _code_unique = models.Constraint("UNIQUE(code)", "Data type code must be unique.")

    def get_price_points(self):
        self.ensure_one()
        raw_value = self.env["ir.config_parameter"].sudo().get_param(
            "telesales_data_allocation.price.%s" % self.code
        )
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            raise ValidationError("No valid point price is configured for data type %s." % self.code)
        if value <= 0:
            raise ValidationError("Point price must be positive.")
        return value
