"""The browser Team probe must observe the owner boundary, not mock success."""

import json
from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e2e"))
import web_team_product_probe as probe  # noqa: E402


class Response:
    def __init__(self, status, *, data=None, error=None):
        self.status = status
        self.headers = {
            "cache-control": "private, no-store",
            "content-type": "application/json; charset=utf-8",
            "x-request-id": "req_team_1",
        }
        body = {
            "meta": {"request_id": "req_team_1"},
        }
        if status == 200:
            body["data"] = data
            body["meta"]["next_cursor"] = None
        else:
            body["error"] = {"code": error, "message": "Denied"}
        self.body = json.dumps(body).encode()


def authenticated_request(observed):
    def request(path, *, method="GET", json_body=None, origin=None):
        if path == "/api/team/members?limit=5" and method == "GET":
            observed.append(("GET", "/v1/team/members"))
            return Response(
                200,
                data=[
                    {
                        "member_id": "member-1",
                        "user_id": "user-me",
                        "roles": ["member"],
                    }
                ],
            )
        if path == "/api/team/roles?limit=5" and method == "GET":
            observed.append(("GET", "/v1/team/roles"))
            return Response(
                200,
                data=[
                    {
                        "name": "member",
                        "permissions": {"member": ["read"]},
                    }
                ],
            )
        if path == "/api/team/invitations?limit=5" and method == "GET":
            observed.append(("GET", "/v1/team/invitations"))
            return Response(403, error="FORBIDDEN")
        if path == "/api/team/invitations" and method == "POST":
            if origin == "https://evil.example.test":
                return Response(403, error="forbidden_origin")
            if "tenant_id" in json_body:
                return Response(400, error="invalid_team_request")
            observed.append(("POST", "/v1/team/invitations"))
            return Response(403, error="FORBIDDEN")
        raise AssertionError(f"unexpected browser request: {method} {path}")

    return request


class TeamProductProbeTests(unittest.TestCase):
    def test_anonymous_team_route_denies_before_bff(self):
        observed = []

        def request(path):
            self.assertEqual(path, "/api/team/members?limit=5")
            return Response(401, error="unauthenticated")

        probe.anonymous(request, observed)
        self.assertEqual(observed, [])

        def leaked_request(path):
            observed.append(("GET", "/v1/team/members"))
            return request(path)

        with self.assertRaises(probe.TeamProbeError):
            probe.anonymous(leaked_request, observed)

    def test_member_reads_cross_bff_once_and_web_guards_mutations(self):
        observed = []
        probe.authenticated(
            authenticated_request(observed),
            {"subject": "user-me"},
            observed,
            "https://web.example.test",
        )
        self.assertEqual(
            observed,
            [
                ("GET", "/v1/team/members"),
                ("GET", "/v1/team/roles"),
                ("GET", "/v1/team/invitations"),
            ],
        )

    def test_missing_subject_and_private_member_email_fail_closed(self):
        observed = []
        with self.assertRaises(probe.TeamProbeError):
            probe.authenticated(
                authenticated_request(observed),
                {},
                observed,
                "https://web.example.test",
            )
        self.assertEqual(observed, [])

        original = authenticated_request(observed)

        def leaked(path, **options):
            response = original(path, **options)
            if path == "/api/team/members?limit=5":
                value = json.loads(response.body)
                value["data"][0]["email"] = "secret@example.test"
                response.body = json.dumps(value).encode()
            return response

        with self.assertRaises(probe.TeamProbeError):
            probe.authenticated(
                leaked, {"subject": "user-me"}, observed, "https://web.example.test"
            )


if __name__ == "__main__":
    unittest.main()
