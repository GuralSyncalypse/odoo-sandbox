from odoo import fields, models
from odoo.exceptions import ValidationError


class TelesalesWalletService(models.AbstractModel):
    _name = "telesales.wallet.service"
    _description = "Wallet Operations"

    def _post_entry(self, wallet, points, entry_type, reference):
        if not points:
            raise ValidationError("Ledger points cannot be zero.")
        return self.env["telesales.wallet.ledger"].sudo().create({
            "wallet_id": wallet.id,
            "points": points,
            "entry_type": entry_type,
            "reference": reference,
        })

    def credit_topup(self, request, approved_by):
        self._post_entry(request.wallet_id, request.points, "topup", "topup:%s" % request.id)
        request.sudo().write({
            "state": "approved",
            "approved_by": approved_by,
            "approved_at": fields.Datetime.now(),
        })

    def credit_refund(self, request, approved_by):
        redemption = request.redemption_request_id
        if redemption.account_id != request.account_id:
            raise ValidationError("Refund account must match the original redemption account.")
        if request.points > redemption.reserved_points:
            raise ValidationError("Refund cannot exceed the redeemed point amount.")
        self._post_entry(redemption.wallet_id, request.points, "refund", "refund:%s" % request.id)
        request.sudo().write({
            "state": "approved",
            "approved_by": approved_by,
            "approved_at": fields.Datetime.now(),
        })
        redemption.item_ids.filtered(lambda item: item.state == "assigned").sudo().write({"state": "refunded"})
