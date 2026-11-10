import base64
import json
from datetime import datetime, timezone

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from odoo import fields, models
from odoo.exceptions import AccessError, ValidationError


def _b64url_decode(value):
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


class TelesalesApiAuthService(models.AbstractModel):
    _name = "telesales.api.auth"
    _description = "Website JWT Authentication"

    def authenticate(self, authorization, require_admin=False):
        if not authorization or not authorization.startswith("Bearer "):
            raise AccessError("Bearer token is required.")
        claims = self._decode_and_verify(authorization[7:])
        account = self.env["telesales.api.account"].sudo().search(
            [("external_user_id", "=", claims["sub"])], limit=1
        )
        if not account:
            raise AccessError("API account was not found.")
        account.ensure_active()
        if require_admin and (not account.is_admin or claims.get("admin") is not True):
            raise AccessError("Admin access is required.")
        return account, claims

    def _decode_and_verify(self, token):
        parts = token.split(".")
        if len(parts) != 3:
            raise AccessError("Malformed JWT.")
        try:
            header = json.loads(_b64url_decode(parts[0]))
            claims = json.loads(_b64url_decode(parts[1]))
            signature = _b64url_decode(parts[2])
        except (ValueError, json.JSONDecodeError):
            raise AccessError("Malformed JWT encoding.")
        if header.get("alg") != "RS256":
            raise AccessError("Only RS256 JWTs are accepted.")
        params = self.env["ir.config_parameter"].sudo()
        public_key_pem = params.get_param("telesales_data_allocation.jwt_public_key")
        issuer = params.get_param("telesales_data_allocation.jwt_issuer")
        audience = params.get_param("telesales_data_allocation.jwt_audience")
        if not public_key_pem or not issuer or not audience:
            raise ValidationError("JWT validation settings are incomplete.")
        try:
            public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
            public_key.verify(
                signature,
                (parts[0] + "." + parts[1]).encode("ascii"),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
        except (ValueError, TypeError, InvalidSignature):
            raise AccessError("Invalid JWT signature.")
        now = datetime.now(timezone.utc).timestamp()
        for claim in ("sub", "jti", "exp", "nbf"):
            if claim not in claims:
                raise AccessError("JWT claim %s is required." % claim)
        if claims.get("iss") != issuer:
            raise AccessError("Invalid JWT issuer.")
        token_audience = claims.get("aud")
        if audience not in (token_audience if isinstance(token_audience, list) else [token_audience]):
            raise AccessError("Invalid JWT audience.")
        try:
            if float(claims["exp"]) <= now or float(claims["nbf"]) > now:
                raise AccessError("JWT is expired or not active yet.")
        except (TypeError, ValueError):
            raise AccessError("Invalid JWT time claims.")
        revoked = self.env["telesales.jwt.revocation"].sudo().search_count([
            ("jti", "=", claims["jti"]), ("expires_at", ">", fields.Datetime.now()),
        ])
        if revoked:
            raise AccessError("JWT has been revoked.")
        return claims
