import json

from odoo import fields, http
from odoo.exceptions import AccessError, ValidationError
from odoo.http import request


class TelesalesApiV1(http.Controller):
    def _body(self):
        try:
            return json.loads(request.httprequest.get_data(as_text=True) or "{}")
        except json.JSONDecodeError:
            raise ValidationError("Request body must be JSON.")

    def _json(self, payload, status=200):
        return request.make_json_response(payload, status=status)

    def _error(self, error, status=400):
        return self._json({"error": str(error)}, status)

    def _account(self, admin=False):
        return request.env["telesales.api.auth"].sudo().authenticate(
            request.httprequest.headers.get("Authorization"), require_admin=admin
        )[0]

    def _idempotency_key(self):
        key = request.httprequest.headers.get("Idempotency-Key")
        if not key:
            raise ValidationError("Idempotency-Key header is required.")
        return key

    @staticmethod
    def _date(value):
        return fields.Datetime.to_string(value) if value else False

    def _admin_domain(self, model):
        state = request.httprequest.args.get("state")
        return [("state", "=", state)] if state else []

    def _admin_limit(self):
        try:
            return min(max(int(request.httprequest.args.get("limit", 50)), 1), 200)
        except ValueError:
            raise ValidationError("limit must be an integer.")

    def _account_payload(self, account):
        posted, reserved, available = account.wallet_id.get_balances()
        return {
            "id": account.id,
            "external_user_id": account.external_user_id,
            "active": account.active,
            "is_admin": account.is_admin,
            "wallet": {"posted_balance": posted, "reserved_balance": reserved, "available_balance": available},
        }

    def _topup_payload(self, topup):
        callback = topup.callback_id
        return {
            "id": topup.id, "account": topup.account_id.external_user_id, "order_id": topup.order_id,
            "points": topup.points, "expected_amount": topup.expected_amount, "state": topup.state,
            "approval_method": topup.approval_method or False, "approved_by": topup.approved_by or False,
            "approved_at": self._date(topup.approved_at),
            "callback": {
                "transaction_id": callback.transaction_id, "amount": callback.amount,
                "received_at": self._date(callback.received_at), "state": callback.state,
            } if callback else False,
        }

    def _redemption_payload(self, redemption):
        return {
            "id": redemption.id, "account": redemption.account_id.external_user_id,
            "data_type": redemption.data_type_id.code, "quantity": redemption.quantity,
            "point_price": redemption.point_price, "reserved_points": redemption.reserved_points,
            "state": redemption.state, "approved_by": redemption.approved_by or False,
            "approved_at": self._date(redemption.approved_at),
        }

    def _refund_payload(self, refund):
        return {
            "id": refund.id, "account": refund.account_id.external_user_id,
            "redemption_request_id": refund.redemption_request_id.id, "points": refund.points,
            "reason": refund.reason, "state": refund.state, "approved_by": refund.approved_by or False,
            "approved_at": self._date(refund.approved_at),
        }

    def _user_topup_payload(self, topup):
        return {
            "id": topup.id, "order_id": topup.order_id, "points": topup.points,
            "expected_amount": topup.expected_amount, "state": topup.state,
            "approval_method": topup.approval_method or False,
            "approved_at": self._date(topup.approved_at),
        }

    def _user_redemption_payload(self, redemption):
        return {
            "id": redemption.id, "data_type": redemption.data_type_id.code,
            "quantity": redemption.quantity, "reserved_points": redemption.reserved_points,
            "state": redemption.state, "approved_at": self._date(redemption.approved_at),
        }

    def _user_refund_payload(self, refund):
        return {
            "id": refund.id, "redemption_request_id": refund.redemption_request_id.id,
            "points": refund.points, "reason": refund.reason, "state": refund.state,
            "approved_at": self._date(refund.approved_at),
        }

    @http.route("/api/v1/wallet", type="http", auth="public", methods=["GET"], csrf=False)
    def wallet(self, **_kwargs):
        try:
            account = self._account()
            wallet = account.wallet_id
            posted, reserved, available = wallet.get_balances()
            return self._json({
                "external_user_id": account.external_user_id,
                "posted_balance": posted,
                "reserved_balance": reserved,
                "available_balance": available,
            })
        except (AccessError, ValidationError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/data-types", type="http", auth="public", methods=["GET"], csrf=False)
    def data_types(self, **_kwargs):
        try:
            self._account()
            result = []
            for data_type in request.env["telesales.data.type"].sudo().search([( "active", "=", True)]):
                result.append({"code": data_type.code, "name": data_type.name, "price_points": data_type.get_price_points()})
            return self._json({"data": result})
        except (AccessError, ValidationError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/topup-requests", type="http", auth="public", methods=["POST"], csrf=False)
    def create_topup_request(self, **_kwargs):
        try:
            account = self._account()
            body = self._body()
            key = self._idempotency_key()
            order_id = body.get("order_id")
            if not order_id:
                raise ValidationError("order_id is required.")
            existing = request.env["telesales.point.topup.request"].sudo().search([
                "|", ("order_id", "=", order_id),
                "&", ("account_id", "=", account.id), ("idempotency_key", "=", key),
            ], limit=1)
            if existing:
                return self._json({"id": existing.id, "state": existing.state, "idempotent": True})
            topup = request.env["telesales.point.topup.request"].sudo().create({
                "account_id": account.id,
                "order_id": order_id,
                "points": int(body["points"]),
                "expected_amount": int(body["expected_amount"]),
                "idempotency_key": key,
            })
            return self._json({"id": topup.id, "state": topup.state, "idempotency_key": key}, 201)
        except (AccessError, ValidationError, KeyError, ValueError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/topup-requests", type="http", auth="public", methods=["GET"], csrf=False)
    def list_topup_requests(self, **_kwargs):
        try:
            account = self._account()
            records = request.env["telesales.point.topup.request"].sudo().search([( "account_id", "=", account.id)])
            return self._json({"data": [self._user_topup_payload(record) for record in records]})
        except (AccessError, ValidationError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/redemption-requests", type="http", auth="public", methods=["POST"] , csrf=False)
    def create_redemption_request(self, **_kwargs):
        try:
            account = self._account()
            body = self._body()
            key = self._idempotency_key()
            data_type = request.env["telesales.data.type"].sudo().search([( "code", "=", body.get("data_type_code")), ("active", "=", True)], limit=1)
            if not data_type:
                raise ValidationError("Unknown data type.")
            quantity = int(body.get("quantity", 1))
            if quantity <= 0:
                raise ValidationError("quantity must be positive.")
            redemption, idempotent = request.env["telesales.allocation.service"].sudo().create_redemption_request(
                account, data_type, quantity, key
            )
            status = 200 if idempotent else 201
            return self._json({
                "id": redemption.id, "state": redemption.state,
                "reserved_points": redemption.reserved_points, "idempotent": idempotent,
            }, status)
        except (AccessError, ValidationError, ValueError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/redemption-requests/<int:request_id>", type="http", auth="public", methods=["GET"], csrf=False)
    def get_redemption_request(self, request_id, **_kwargs):
        try:
            account = self._account()
            redemption = request.env["telesales.data.redemption.request"].sudo().search([
                ("id", "=", request_id), ("account_id", "=", account.id),
            ], limit=1)
            if not redemption:
                return self._error("Not found.", 404)
            return self._json({"id": redemption.id, "state": redemption.state, "reserved_points": redemption.reserved_points})
        except (AccessError, ValidationError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/redemption-requests", type="http", auth="public", methods=["GET"], csrf=False)
    def list_redemption_requests(self, **_kwargs):
        try:
            account = self._account()
            records = request.env["telesales.data.redemption.request"].sudo().search([( "account_id", "=", account.id)])
            return self._json({"data": [self._user_redemption_payload(record) for record in records]})
        except (AccessError, ValidationError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/allocations", type="http", auth="public", methods=["GET"], csrf=False)
    def allocations(self, **_kwargs):
        try:
            account = self._account()
            items = request.env["telesales.data.item"].sudo().search([( "assigned_account_id", "=", account.id)])
            return self._json({"data": [{"id": item.id, "payload": item.payload, "state": item.state} for item in items]})
        except (AccessError, ValidationError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/refund-requests", type="http", auth="public", methods=["POST"], csrf=False)
    def create_refund_request(self, **_kwargs):
        try:
            account = self._account()
            body = self._body()
            key = self._idempotency_key()
            existing = request.env["telesales.refund.request"].sudo().search([
                ("account_id", "=", account.id), ("idempotency_key", "=", key),
            ], limit=1)
            if existing:
                return self._json({"id": existing.id, "state": existing.state, "idempotent": True})
            redemption = request.env["telesales.data.redemption.request"].sudo().search([
                ("id", "=", int(body["redemption_request_id"])), ("account_id", "=", account.id), ("state", "=", "approved"),
            ], limit=1)
            if not redemption:
                raise ValidationError("Approved redemption request not found.")
            refund = request.env["telesales.refund.request"].sudo().create({
                "account_id": account.id,
                "redemption_request_id": redemption.id,
                "points": int(body.get("points", redemption.reserved_points)),
                "reason": body["reason"],
                "idempotency_key": key,
            })
            return self._json({"id": refund.id, "state": refund.state}, 201)
        except (AccessError, ValidationError, KeyError, ValueError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/refund-requests", type="http", auth="public", methods=["GET"], csrf=False)
    def list_refund_requests(self, **_kwargs):
        try:
            account = self._account()
            records = request.env["telesales.refund.request"].sudo().search([( "account_id", "=", account.id)])
            return self._json({"data": [self._user_refund_payload(record) for record in records]})
        except (AccessError, ValidationError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/payments/vietqr/callback", type="http", auth="public", methods=["POST"], csrf=False)
    def vietqr_callback(self, **_kwargs):
        try:
            body = self._body()
            callback_model = request.env["telesales.payment.callback"].sudo()
            duplicate = callback_model.search([( "provider", "=", "vietqr"), ("transaction_id", "=", body.get("transactionId"))], limit=1)
            if duplicate:
                return self._json({"error": False, "errorReason": "000", "toastMessage": duplicate.transaction_id, "messageError": "Success"})
            amount = request.env["telesales.vietqr.service"].sudo().verify_callback(body)
            callback = callback_model.create({
                "transaction_id": body["transactionId"], "order_id": body["orderId"], "transaction_time": body["transactionTime"],
                "amount": amount, "reference_number": body.get("referencenumber"), "bank_account": body.get("bankAccount"),
                "transaction_type": body.get("transType"), "signature": body["signature"], "payload": body,
            })
            return self._json({"error": False, "errorReason": "000", "toastMessage": callback.transaction_id, "messageError": "Success"})
        except ValidationError as error:
            return self._json({"error": True, "errorReason": "002", "toastMessage": "", "messageError": str(error)}, 400)

    @http.route("/api/v1/admin/topup-requests/<int:topup_id>/approve", type="http", auth="public", methods=["POST"], csrf=False)
    def approve_topup(self, topup_id, **_kwargs):
        try:
            admin = self._account(admin=True)
            topup = request.env["telesales.point.topup.request"].sudo().browse(topup_id).exists()
            if not topup:
                return self._error("Not found.", 404)
            callback = request.env["telesales.payment.callback"].sudo().search([
                ("order_id", "=", topup.order_id), ("amount", "=", topup.expected_amount), ("state", "=", "verified"),
            ], limit=1)
            if callback:
                topup.sudo().write({"callback_id": callback.id})
            topup.action_approve(admin.external_user_id)
            return self._json({"id": topup.id, "state": topup.state, "approval_method": topup.approval_method})
        except (AccessError, ValidationError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/admin/accounts", type="http", auth="public", methods=["GET"], csrf=False)
    def list_accounts(self, **_kwargs):
        try:
            self._account(admin=True)
            accounts = request.env["telesales.api.account"].sudo().search([], limit=self._admin_limit())
            return self._json({"data": [self._account_payload(account) for account in accounts]})
        except (AccessError, ValidationError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/admin/accounts/<int:account_id>", type="http", auth="public", methods=["PATCH"], csrf=False)
    def update_account(self, account_id, **_kwargs):
        try:
            self._account(admin=True)
            account = request.env["telesales.api.account"].sudo().browse(account_id).exists()
            if not account:
                return self._error("Not found.", 404)
            body = self._body()
            values = {key: body[key] for key in ("active", "is_admin") if key in body}
            if not values or any(not isinstance(value, bool) for value in values.values()):
                raise ValidationError("active or is_admin boolean is required.")
            account.write(values)
            return self._json(self._account_payload(account))
        except (AccessError, ValidationError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/admin/redemption-requests/<int:redemption_id>/approve", type="http", auth="public", methods=["POST"], csrf=False)
    def approve_redemption(self, redemption_id, **_kwargs):
        try:
            admin = self._account(admin=True)
            redemption = request.env["telesales.data.redemption.request"].sudo().browse(redemption_id).exists()
            if not redemption:
                return self._error("Not found.", 404)
            redemption.action_approve(admin.external_user_id)
            return self._json({"id": redemption.id, "state": redemption.state})
        except (AccessError, ValidationError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/admin/refund-requests/<int:refund_id>/approve", type="http", auth="public", methods=["POST"], csrf=False)
    def approve_refund(self, refund_id, **_kwargs):
        try:
            admin = self._account(admin=True)
            refund = request.env["telesales.refund.request"].sudo().browse(refund_id).exists()
            if not refund:
                return self._error("Not found.", 404)
            refund.action_approve(admin.external_user_id)
            return self._json({"id": refund.id, "state": refund.state})
        except (AccessError, ValidationError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/admin/accounts", type="http", auth="public", methods=["POST"], csrf=False)
    def create_account(self, **_kwargs):
        try:
            self._account(admin=True)
            body = self._body()
            account = request.env["telesales.api.account"].sudo().create({
                "external_user_id": body["external_user_id"],
                "is_admin": bool(body.get("is_admin", False)),
            })
            return self._json({"id": account.id, "external_user_id": account.external_user_id}, 201)
        except (AccessError, ValidationError, KeyError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/admin/data-types", type="http", auth="public", methods=["POST"], csrf=False)
    def create_data_type(self, **_kwargs):
        try:
            self._account(admin=True)
            body = self._body()
            data_type = request.env["telesales.data.type"].sudo().create({
                "name": body["name"], "code": body["code"],
            })
            price = int(body["price_points"])
            if price <= 0:
                raise ValidationError("price_points must be positive.")
            request.env["ir.config_parameter"].sudo().set_param(
                "telesales_data_allocation.price.%s" % data_type.code, price
            )
            return self._json({"id": data_type.id, "code": data_type.code, "price_points": price}, 201)
        except (AccessError, ValidationError, KeyError, ValueError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/admin/data-types", type="http", auth="public", methods=["GET"], csrf=False)
    def list_admin_data_types(self, **_kwargs):
        try:
            self._account(admin=True)
            data_types = request.env["telesales.data.type"].sudo().search([], limit=self._admin_limit())
            return self._json({"data": [{
                "id": data_type.id, "name": data_type.name, "code": data_type.code,
                "active": data_type.active, "price_points": data_type.get_price_points(),
            } for data_type in data_types]})
        except (AccessError, ValidationError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/admin/data-types/<string:code>/price", type="http", auth="public", methods=["PUT"], csrf=False)
    def set_data_type_price(self, code, **_kwargs):
        try:
            self._account(admin=True)
            price = int(self._body()["price_points"])
            if price <= 0:
                raise ValidationError("price_points must be positive.")
            data_type = request.env["telesales.data.type"].sudo().search([( "code", "=", code)], limit=1)
            if not data_type:
                return self._error("Not found.", 404)
            request.env["ir.config_parameter"].sudo().set_param(
                "telesales_data_allocation.price.%s" % code, price
            )
            return self._json({"code": code, "price_points": price})
        except (AccessError, ValidationError, KeyError, ValueError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/admin/data-pools", type="http", auth="public", methods=["POST"], csrf=False)
    def create_data_pool(self, **_kwargs):
        try:
            self._account(admin=True)
            body = self._body()
            data_type = request.env["telesales.data.type"].sudo().search([( "code", "=", body["data_type_code"])], limit=1)
            if not data_type:
                raise ValidationError("Unknown data type.")
            payloads = body.get("items", [])
            if not isinstance(payloads, list) or not payloads:
                raise ValidationError("items must be a non-empty array.")
            pool = request.env["telesales.data.pool"].sudo().create({
                "name": body["name"], "pool_date": body["pool_date"], "data_type_id": data_type.id,
            })
            request.env["telesales.data.item"].sudo().create([
                {"pool_id": pool.id, "payload": payload} for payload in payloads
            ])
            return self._json({"id": pool.id, "item_count": len(payloads)}, 201)
        except (AccessError, ValidationError, KeyError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/admin/data-pools", type="http", auth="public", methods=["GET"], csrf=False)
    def list_data_pools(self, **_kwargs):
        try:
            self._account(admin=True)
            pools = request.env["telesales.data.pool"].sudo().search([], limit=self._admin_limit())
            return self._json({"data": [{
                "id": pool.id, "name": pool.name, "pool_date": str(pool.pool_date),
                "data_type": pool.data_type_id.code, "active": pool.active, "item_count": len(pool.item_ids),
            } for pool in pools]})
        except (AccessError, ValidationError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/admin/topup-requests", type="http", auth="public", methods=["GET"], csrf=False)
    def list_topup_requests(self, **_kwargs):
        try:
            self._account(admin=True)
            records = request.env["telesales.point.topup.request"].sudo().search(self._admin_domain("topup"), limit=self._admin_limit())
            return self._json({"data": [self._topup_payload(record) for record in records]})
        except (AccessError, ValidationError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/admin/redemption-requests", type="http", auth="public", methods=["GET"], csrf=False)
    def list_redemption_requests(self, **_kwargs):
        try:
            self._account(admin=True)
            records = request.env["telesales.data.redemption.request"].sudo().search(self._admin_domain("redemption"), limit=self._admin_limit())
            return self._json({"data": [self._redemption_payload(record) for record in records]})
        except (AccessError, ValidationError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/admin/refund-requests", type="http", auth="public", methods=["GET"], csrf=False)
    def list_refund_requests(self, **_kwargs):
        try:
            self._account(admin=True)
            records = request.env["telesales.refund.request"].sudo().search(self._admin_domain("refund"), limit=self._admin_limit())
            return self._json({"data": [self._refund_payload(record) for record in records]})
        except (AccessError, ValidationError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)

    @http.route("/api/v1/admin/<string:model_name>/<int:record_id>/reject", type="http", auth="public", methods=["POST"], csrf=False)
    def reject_request(self, model_name, record_id, **_kwargs):
        try:
            self._account(admin=True)
            models_by_name = {
                "topup-requests": "telesales.point.topup.request",
                "redemption-requests": "telesales.data.redemption.request",
                "refund-requests": "telesales.refund.request",
            }
            model = models_by_name.get(model_name)
            if not model:
                return self._error("Not found.", 404)
            record = request.env[model].sudo().browse(record_id).exists()
            if not record:
                return self._error("Not found.", 404)
            if record.state != "pending":
                raise ValidationError("Only pending requests can be rejected.")
            record.write({"state": "rejected"})
            return self._json({"id": record.id, "state": record.state})
        except (AccessError, ValidationError) as error:
            return self._error(error, 401 if isinstance(error, AccessError) else 400)
