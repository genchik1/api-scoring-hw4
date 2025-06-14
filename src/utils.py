import datetime
import hashlib


def check_auth(request, admin_salt: str, salt: str) -> bool:
    if request.is_admin:
        digest = hashlib.sha512(
            (datetime.datetime.now().strftime("%Y%m%d%H") + admin_salt).encode("utf-8")
        ).hexdigest()
    else:
        digest = hashlib.sha512(
            (request.account + request.login + salt).encode("utf-8")
        ).hexdigest()
    return digest == request.token
