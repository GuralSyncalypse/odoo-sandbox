from odoo import fields, models


class TelesalesJwtRevocation(models.Model):
    _name = "telesales.jwt.revocation"
    _description = "Revoked Website JWT"

    jti = fields.Char(required=True, index=True)
    expires_at = fields.Datetime(required=True)
    reason = fields.Char()

    _jti_unique = models.Constraint("UNIQUE(jti)", "JWT ID already exists.")
