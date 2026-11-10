from odoo import api, fields, models


class TelesalesWallet(models.Model):
    _name = "telesales.wallet"
    _description = "Point Wallet"
    _rec_name = "account_id"

    account_id = fields.Many2one("telesales.api.account", required=True, ondelete="cascade", index=True)
    posted_balance = fields.Integer(compute="_compute_balances", string="Posted balance")
    reserved_balance = fields.Integer(compute="_compute_balances", string="Reserved balance")
    available_balance = fields.Integer(compute="_compute_balances", string="Available balance")

    _account_unique = models.Constraint("UNIQUE(account_id)", "An API account can only have one wallet.")

    def get_balances(self):
        self.ensure_one()
        self.env["telesales.wallet.ledger"].flush_model(["wallet_id", "state", "points"])
        self.env["telesales.data.redemption.request"].flush_model(["wallet_id", "state", "reserved_points"])
        self.env.cr.execute(
            "SELECT COALESCE(SUM(points), 0) FROM telesales_wallet_ledger WHERE wallet_id = %s AND state = 'posted'",
            [self.id],
        )
        posted = int(self.env.cr.fetchone()[0])
        self.env.cr.execute(
            "SELECT COALESCE(SUM(reserved_points), 0) FROM telesales_data_redemption_request WHERE wallet_id = %s AND state = 'pending'",
            [self.id],
        )
        reserved = int(self.env.cr.fetchone()[0])
        return posted, reserved, posted - reserved

    def _compute_balances(self):
        for wallet in self:
            posted, reserved, available = wallet.get_balances()
            wallet.posted_balance = posted
            wallet.reserved_balance = reserved
            wallet.available_balance = available
