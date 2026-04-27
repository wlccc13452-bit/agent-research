import json
import os
import unittest
import urllib.error
import urllib.request
NVIDIA_TOKEN ="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"

def _get_nvidia_token() -> str | None:
    return NVIDIA_TOKEN


def _request_json(url: str, token: str, timeout_s: float = 20.0) -> tuple[int, dict]:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "nvida_api_test/1.0",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            status = int(getattr(resp, "status", 200))
            body_bytes = resp.read()
    except urllib.error.HTTPError as e:
        status = int(getattr(e, "code", 0) or 0)
        body_bytes = e.read() if hasattr(e, "read") else b""
    body_text = body_bytes.decode("utf-8", errors="replace").strip()
    payload = json.loads(body_text) if body_text else {}
    return status, payload


class TestNvidiaToken(unittest.TestCase):
    def test_models_list(self) -> None:
        token = _get_nvidia_token()
        if not token:
            self.skipTest("Set NVIDIA_API_KEY or NVIDIA_TOKEN to run this test.")

        status, payload = _request_json("https://integrate.api.nvidia.com/v1/models", token=token)
        self.assertEqual(status, 200, msg=f"status={status} payload={payload}")
        self.assertIsInstance(payload, dict)
        self.assertIn("data", payload, msg=f"payload keys={sorted(payload.keys())}")
