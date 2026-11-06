"""Fixtures compartilhadas: servidor local da página e navegador."""
import functools
import http.server
import threading
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent


class _Silencioso(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def base_url():
    handler = functools.partial(_Silencioso, directory=str(RAIZ))
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{servidor.server_port}/"
    servidor.shutdown()


@pytest.fixture(scope="session")
def navegador():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        yield browser
        browser.close()
