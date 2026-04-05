import json
import os


def _get_auth_header(headers: dict | None) -> str:
    if not headers:
        return ""
    for key in ("authorization", "Authorization"):
        if key in headers:
            return headers.get(key, "")
    return ""


def _extract_token(auth_header: str) -> str:
    if not auth_header:
        return ""
    value = auth_header.strip()
    if value.lower().startswith("bearer "):
        return value.split(" ", 1)[1].strip()
    return value


def _is_valid_token(auth_header: str, expected_token: str) -> bool:
    token = _extract_token(auth_header)
    if not token:
        return False
    return token == expected_token


def _policy(effect: str, resource: str, principal_id: str) -> dict:
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": resource,
                }
            ],
        },
        "context": {
            "authorized": str(effect == "Allow").lower(),
        },
    }


def handler(event, context):
    expected_token = os.environ.get("AUTH_TOKEN", "my-secret-token")
    auth_header = _get_auth_header(event.get("headers"))
    if not auth_header:
        identity = event.get("identitySource")
        if isinstance(identity, list) and identity:
            auth_header = identity[0]
        elif isinstance(identity, str):
            auth_header = identity
        elif "authorizationToken" in event:
            auth_header = event.get("authorizationToken") or ""
    token = _extract_token(auth_header)
    is_authorized = token == expected_token if token else False

    print(
        json.dumps(
            {
                "route": event.get("routeArn") or event.get("methodArn"),
                "has_header": bool(auth_header),
                "token_prefix": auth_header[:12] if isinstance(auth_header, str) else "",
                "is_authorized": is_authorized,
            }
        )
    )

    resource = event.get("routeArn") or event.get("methodArn") or "*"
    effect = "Allow" if is_authorized else "Deny"
    return _policy(effect, resource, "devops-user")
