from __future__ import annotations

import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from server import (
    CONFIG_PATH,
    PlaygroundHandler,
    ThreadingHTTPServer,
    generate_svg_document,
)


class SvgPlaygroundTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    def test_builds_versioned_svg_contract_with_dynamic_bindings(self) -> None:
        document = generate_svg_document(self.config)

        self.assertEqual(document["format"], "lmmp-parametric-svg")
        self.assertEqual(document["version"], "1.0.0")
        self.assertIn('<svg xmlns="http://www.w3.org/2000/svg"', document["svg"])
        targets = {binding["target"] for binding in document["bindings"]}
        self.assertIn("rectangle-interface", targets)
        self.assertIn("rectangle-wetting-region", targets)
        self.assertIn("theta-label", targets)

    def test_rejects_invalid_contact_angle_order(self) -> None:
        self.config["angles"]["theta_receding"] = 50

        with self.assertRaises(ValueError):
            generate_svg_document(self.config)


class HttpApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        class QuietHandler(PlaygroundHandler):
            def log_message(self, *_args) -> None:
                pass

        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def setUp(self) -> None:
        self.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    def test_static_page_and_compiled_renderer_are_served(self) -> None:
        with urlopen(self.url + "/", timeout=4) as response:
            self.assertIn(b"Interfacial SVG Playground", response.read())
        with urlopen(self.url + "/typescript/renderers/svg/SvgRenderer.js", timeout=4) as response:
            self.assertIn("javascript", response.headers["Content-Type"])
            self.assertIn(b"class SvgRenderer", response.read())

    def test_http_endpoint_returns_svg_contract(self) -> None:
        request = Request(
            self.url + "/api/svg",
            method="POST",
            headers={"Content-Type": "application/json"},
            data=CONFIG_PATH.read_bytes(),
        )
        with urlopen(request, timeout=4) as response:
            self.assertEqual(response.status, 200)
            payload = json.load(response)
        self.assertEqual(payload["format"], "lmmp-parametric-svg")
        self.assertIn("<svg", payload["svg"])
        self.assertTrue(payload["bindings"])

    def test_http_endpoint_reports_invalid_domain_input(self) -> None:
        self.config["angles"]["theta_advancing"] = 10
        request = Request(
            self.url + "/api/svg",
            method="POST",
            headers={"Content-Type": "application/json"},
            data=json.dumps(self.config).encode("utf-8"),
        )
        with self.assertRaises(HTTPError) as captured:
            urlopen(request, timeout=4)
        self.assertEqual(captured.exception.code, 422)
        self.assertIn("error", json.loads(captured.exception.read()))


if __name__ == "__main__":
    unittest.main()
