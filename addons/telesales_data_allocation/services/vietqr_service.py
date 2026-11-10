import hashlib
import hmac

from odoo import models
from odoo.exceptions import ValidationError


class TelesalesVietqrService(models.AbstractModel):
    _name = "telesales.vietqr.service"
    _description = "VietQR Callback Verification"

    def verify_callback(self, payload):
        required = ("transactionId", "amount", "transactionTime", "orderId", "signature")
        missing = [field for field in required if not payload.get(field)]
        if missing:
            raise ValidationError("Missing VietQR callback fields: %s." % ", ".join(missing))
        try:
            amount = int(payload["amount"])
        except (TypeError, ValueError):
            raise ValidationError("VietQR amount must be an integer.")
        if amount <= 0:
            raise ValidationError("VietQR amount must be positive.")
        secret = self.env["ir.config_parameter"].sudo().get_param(
            "telesales_data_allocation.vietqr_secret_key"
        )
        if not secret:
            raise ValidationError("VietQR secret key is not configured.")
        message = "%s%010d%s%s" % (
            payload["transactionId"], amount, payload["transactionTime"], payload["orderId"],
        )
        expected = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected.lower(), str(payload["signature"]).lower()):
            raise ValidationError("Invalid VietQR callback signature.")
        return amount
