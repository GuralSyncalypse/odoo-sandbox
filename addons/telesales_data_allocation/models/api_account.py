from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TelesalesApiAccount(models.Model):
    _name = "telesales.api.account"
    _description = "Website API Account"
    _rec_name = "external_user_id"

    external_user_id = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    is_admin = fields.Boolean(default=False)
    wallet_id = fields.Many2one("telesales.wallet", string="Wallet", readonly=True, ondelete="restrict")

    _external_user_id_unique = models.Constraint("UNIQUE(external_user_id)", "External user ID must be unique.")

    @api.model_create_multi
    def create(self, vals_list):
        accounts = super().create(vals_list)
        for account in accounts:
            wallet = self.env["telesales.wallet"].sudo().create({"account_id": account.id})
            account.sudo().write({"wallet_id": wallet.id})
        return accounts

    def ensure_active(self):
        self.ensure_one()
        if not self.active:
            raise ValidationError("This API account is inactive.")
        return self
