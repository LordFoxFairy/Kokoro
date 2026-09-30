"""Fail-closed guards for the Skill browser prerequisite (not a UI PASS)."""

import importlib.util
from pathlib import Path
import unittest
import subprocess
from unittest.mock import Mock, patch

PATH = (
    Path(__file__).resolve().parents[1] / "e2e/run_web_skill_publish_chromium_smoke.py"
)
spec = importlib.util.spec_from_file_location("web_skill_publish", PATH)
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


class BrowserPrerequisiteTests(unittest.TestCase):
    def test_origin_rejects_remote_credentials_paths_and_reserved_port(self):
        for origin in (
            "http://127.0.0.1:4444",
            "https://evil.test:4444",
            "https://u:p@127.0.0.1:4444",
            "https://127.0.0.1:3310",
            "https://127.0.0.1:4444/a",
            "https://127.0.0.1:4444?x=1",
        ):
            with self.subTest(origin=origin), self.assertRaises(smoke.SmokeError):
                smoke.https_origin(origin)
        self.assertEqual(
            smoke.https_origin("https://127.0.0.1:4444"), "https://127.0.0.1:4444"
        )

    def test_actual_owned_web_host_is_accepted_without_wildcard(self):
        origin = "https://web-" + "a" * 24 + ".example.test:4444"
        self.assertEqual(smoke.https_origin(origin), origin)
        for bad in (
            "https://web-short.example.test:4444",
            "https://web-" + "a" * 24 + ".example.test.evil:4444",
        ):
            with self.subTest(origin=bad), self.assertRaises(smoke.SmokeError):
                smoke.https_origin(bad)

    def test_cors_is_exact_and_read_back(self):
        s3 = Mock()
        rule = smoke.cors_configuration("https://127.0.0.1:4444")
        s3.get_bucket_cors.return_value = {**rule, "ResponseMetadata": {}}
        smoke.configure_cors(s3, "owned", "https://127.0.0.1:4444")
        s3.put_bucket_cors.assert_called_once_with(
            Bucket="owned", CORSConfiguration=rule
        )
        self.assertEqual(
            rule,
            {
                "CORSRules": [
                    {
                        "AllowedOrigins": ["https://127.0.0.1:4444"],
                        "AllowedMethods": ["PUT"],
                        "AllowedHeaders": ["content-type"],
                        "MaxAgeSeconds": 0,
                    }
                ]
            },
        )

    def test_wildcard_cors_readback_fails(self):
        s3 = Mock()
        s3.get_bucket_cors.return_value = smoke.cors_configuration(
            "https://127.0.0.1:4444"
        )
        s3.get_bucket_cors.return_value["CORSRules"][0]["AllowedOrigins"] = ["*"]
        with self.assertRaises(smoke.SmokeError):
            smoke.configure_cors(s3, "owned", "https://127.0.0.1:4444")

    def test_unsupported_cors_is_typed_without_secret_exception(self):
        s3 = Mock()
        error = Exception("secret signed URL")
        error.response = {
            "Error": {"Code": "NotImplemented"},
            "ResponseMetadata": {"HTTPStatusCode": 501},
        }
        s3.put_bucket_cors.side_effect = error
        with self.assertRaisesRegex(
            smoke.SmokeError, r"bucket CORS unsupported: NotImplemented \(501\)"
        ) as result:
            smoke.configure_cors(s3, "owned", "https://127.0.0.1:4444")
        self.assertNotIn("secret", str(result.exception))

    def test_unsupported_cors_cleans_owned_bucket_and_closes_client(self):
        env = {
            "KOKORO_OBJECT_STORE_ENDPOINT": "http://127.0.0.1:39190",
            "KOKORO_OBJECT_STORE_REGION": "us-east-1",
            "KOKORO_OBJECT_STORE_ACCESS_KEY_ID": "test",
            "KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY": "test-secret",
            "KOKORO_OBJECT_STORE_PROFILE": "custom",
            "KOKORO_OBJECT_STORE_FORCE_PATH_STYLE": "true",
        }
        s3 = Mock()
        error = Exception("secret")
        error.response = {
            "Error": {"Code": "NotImplemented"},
            "ResponseMetadata": {"HTTPStatusCode": 501},
        }
        s3.put_bucket_cors.side_effect = error
        with (
            patch.object(smoke.storage, "_s3", return_value=s3),
            patch.object(smoke.sandbox, "require_bucket_absent") as absent,
            patch.object(smoke.sandbox, "delete_owned_bucket") as delete,
            patch.object(
                subprocess,
                "Popen",
                side_effect=AssertionError("no process before CORS"),
            ) as start,
        ):
            with self.assertRaisesRegex(smoke.SmokeError, "NotImplemented"):
                smoke.probe_bucket_cors(env, "https://127.0.0.1:4444")
            bucket = s3.create_bucket.call_args.kwargs["Bucket"]
            self.assertRegex(bucket, r"^kokoro-skill-browser-[a-f0-9]{24}$")
            delete.assert_called_once_with(s3, bucket, smoke.storage)
            self.assertEqual(absent.call_count, 2)
            start.assert_not_called()
            s3.close.assert_called_once()

    def test_failed_create_does_not_delete_unowned_bucket(self):
        env = {
            "KOKORO_OBJECT_STORE_ENDPOINT": "http://127.0.0.1:39190",
            "KOKORO_OBJECT_STORE_REGION": "us-east-1",
            "KOKORO_OBJECT_STORE_ACCESS_KEY_ID": "test",
            "KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY": "test-secret",
            "KOKORO_OBJECT_STORE_PROFILE": "custom",
            "KOKORO_OBJECT_STORE_FORCE_PATH_STYLE": "true",
        }
        s3 = Mock()
        s3.create_bucket.side_effect = RuntimeError("create failed")
        with (
            patch.object(smoke.storage, "_s3", return_value=s3),
            patch.object(smoke.sandbox, "require_bucket_absent"),
            patch.object(smoke.sandbox, "delete_owned_bucket") as delete,
            patch.object(
                subprocess,
                "Popen",
                side_effect=AssertionError("no process before CORS"),
            ) as start,
        ):
            with self.assertRaises(RuntimeError):
                smoke.probe_bucket_cors(env, "https://127.0.0.1:4444")
            delete.assert_not_called()
            start.assert_not_called()
            s3.put_bucket_cors.assert_not_called()
            s3.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
