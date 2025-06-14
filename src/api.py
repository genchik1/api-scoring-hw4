#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import uuid
from http.server import BaseHTTPRequestHandler
from typing import Any

from src.consts import (
    OK,
    BAD_REQUEST,
    NOT_FOUND,
    INTERNAL_ERROR,
    ERRORS,
    INVALID_REQUEST,
    FORBIDDEN,
)
from src.dto import MethodRequest, OnlineScoreRequest, ClientsInterestsRequest
from src.settings import ADMIN_SALT, SALT, get_logger
from src.utils import check_auth

logger = get_logger(__name__)


validate_per_method = {
    "online_score": OnlineScoreRequest,
    "clients_interests": ClientsInterestsRequest,
}


def method_handler(request: Any, ctx: Any, store: Any) -> tuple[dict[str, Any], int]:
    request_body = request["body"]

    try:
        request = MethodRequest(**request_body)
    except ValueError as err:
        logger.exception(str(err))
        return {"error": str(err)}, INVALID_REQUEST

    if not check_auth(request, ADMIN_SALT, SALT):
        logger.exception("Ошибка аутентификации")
        return {"error": "Ошибка аутентификации"}, FORBIDDEN

    if request.method == "online_score" and request.is_admin:
        return {"score": 42}, OK

    try:
        method_object = validate_per_method[request.method](**request.arguments)
    except ValueError as err:
        logger.exception(str(err))
        return {"error": str(err)}, INVALID_REQUEST

    method_object.set_context(ctx)

    return method_object.calculate(), OK


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {"method": method_handler}
    store = None

    def get_request_id(self, headers):
        return headers.get("HTTP_X_REQUEST_ID", uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers["Content-Length"]))
            request = json.loads(data_string)
        except Exception:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logger.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path](
                        {"body": request, "headers": self.headers}, context, self.store
                    )
                except Exception as e:
                    logger.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logger.info(context)
        self.wfile.write(json.dumps(r).encode("utf-8"))
        return
