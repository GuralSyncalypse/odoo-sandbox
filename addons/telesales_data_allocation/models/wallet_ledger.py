from odoo import fields, models
from odoo.exceptions import UserError


class TelesalesWalletLedger(models.Model):
    _name = "telesales.wallet.ledger"
    _description = "Immutable Wallet Ledger"
    _order = "id desc"

    wallet_id = fields.Many2one("telesales.wallet", required=True, ondelete="restrict", index=True)
    points = fields.Integer(required=True, help="Signed: positive for credit and negative for debit.")
    entry_type = fields.Selection(
        [("topup", "Top up"), ("redemption", "Redemption"), ("refund", "Refund")],
        required=True,
    )
    state = fields.Selection([("posted", "Posted")], default="posted", required=True)
    reference = fields.Char(required=True, index=True)
    created_at = fields.Datetime(default=fields.Datetime.now, required=True, readonly=True)

    _reference_unique = models.Constraint("UNIQUE(reference)", "Ledger reference must be unique.")

    def write(self, vals):
        raise UserError("Wallet ledger entries are immutable.")

    def unlink(self):
        raise UserError("Wallet ledger entries cannot be removed.")
