from odoo import fields, models
from odoo.exceptions import ValidationError


class TelesalesAllocationService(models.AbstractModel):
    _name = "telesales.allocation.service"
    _description = "Transactional Data Allocation"

    def create_redemption_request(self, account, data_type, quantity, idempotency_key):
        self.env.cr.execute("SELECT id FROM telesales_wallet WHERE id = %s FOR UPDATE", [account.wallet_id.id])
        existing = self.env["telesales.data.redemption.request"].sudo().search([
            ("account_id", "=", account.id), ("idempotency_key", "=", idempotency_key),
        ], limit=1)
        if existing:
            return existing, True
        values = self.env["telesales.data.redemption.request"].values_for_new_request(data_type, quantity)
        if account.wallet_id.get_balances()[2] < values["reserved_points"]:
            raise ValidationError("Insufficient available points.")
        return self.env["telesales.data.redemption.request"].sudo().create({
            "account_id": account.id,
            "data_type_id": data_type.id,
            "quantity": quantity,
            "idempotency_key": idempotency_key,
            **values,
        }), False

    def approve_redemption(self, request, approved_by):
        self.env.cr.execute(
            "SELECT id FROM telesales_data_redemption_request WHERE id = %s FOR UPDATE",
            [request.id],
        )
        request.invalidate_recordset()
        request = self.env["telesales.data.redemption.request"].browse(request.id)
        if request.state != "pending":
            raise ValidationError("Only pending redemption requests can be approved.")
        wallet = request.wallet_id
        if wallet.get_balances()[2] < 0:
            raise ValidationError("Wallet reservations exceed its posted balance.")

        self.env.cr.execute(
            """
            SELECT item.id
              FROM telesales_data_item AS item
              JOIN telesales_data_pool AS pool ON pool.id = item.pool_id
             WHERE item.state = 'available'
               AND pool.data_type_id = %s
               AND pool.active = true
             ORDER BY pool.pool_date, item.id
             FOR UPDATE OF item SKIP LOCKED
             LIMIT %s
            """,
            [request.data_type_id.id, request.quantity],
        )
        item_ids = [row[0] for row in self.env.cr.fetchall()]
        if len(item_ids) != request.quantity:
            raise ValidationError("Not enough data is available in the daily pool.")

        self.env["telesales.wallet.service"].sudo()._post_entry(
            wallet,
            -request.reserved_points,
            "redemption",
            "redemption:%s" % request.id,
        )
        self.env["telesales.data.item"].browse(item_ids).sudo().write({
            "state": "assigned",
            "redemption_request_id": request.id,
            "assigned_account_id": request.account_id.id,
        })
        request.sudo().write({
            "state": "approved",
            "approved_by": approved_by,
            "approved_at": fields.Datetime.now(),
        })
