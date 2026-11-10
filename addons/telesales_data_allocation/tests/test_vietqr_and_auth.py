import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase


def b64url(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


class TestVietqrAndAuth(TransactionCase):
    def setUp(self):
        super().setUp()
        self.env["ir.config_parameter"].sudo().set_param("telesales_data_allocation.vietqr_secret_key", "secret")

    def test_vietqr_hmac_verification(self):
        payload = {
            "transactionId": "tx-1", "amount": "100000", "transactionTime": "2026-01-01T01:00:00",
            "orderId": "order-1",
        }
        signing_data = "tx-100001000002026-01-01T01:00:00order-1"
        payload["signature"] = hmac.new(b"secret", signing_data.encode(), hashlib.sha256).hexdigest()
        self.assertEqual(self.env["telesales.vietqr.service"].verify_callback(payload), 100000)
        payload["signature"] = "invalid"
        with self.assertRaises(ValidationError):
            self.env["telesales.vietqr.service"].verify_callback(payload)

    def test_rs256_jwt_is_verified(self):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_pem = private_key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("telesales_data_allocation.jwt_public_key", public_pem)
        params.set_param("telesales_data_allocation.jwt_issuer", "website")
        params.set_param("telesales_data_allocation.jwt_audience", "odoo")
        self.env["telesales.api.account"].create({"external_user_id": "subject-1"})
        now = datetime.now(timezone.utc)
        header = b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
        claims = b64url(json.dumps({
            "sub": "subject-1", "jti": "jti-1", "iss": "website", "aud": "odoo",
            "nbf": int(now.timestamp()), "exp": int((now + timedelta(minutes=5)).timestamp()),
        }).encode())
        message = (header + "." + claims).encode()
        signature = b64url(private_key.sign(message, padding.PKCS1v15(), hashes.SHA256()))
        account, _claims = self.env["telesales.api.auth"].authenticate("Bearer " + header + "." + claims + "." + signature)
        self.assertEqual(account.external_user_id, "subject-1")
        with self.assertRaises(AccessError):
            self.env["telesales.api.auth"].authenticate("Bearer invalid")
