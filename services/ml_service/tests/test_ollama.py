import os
import sys
import pytest

# ensure package imports from service
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import ollama


def test_generate_fallback(monkeypatch):
    # simulate network failure
    def bad_post(*args, **kwargs):
        raise Exception("network down")

    class Dummy:
        def __init__(self, *a, **k):
            pass
        def post(self, *a, **k):
            return bad_post()
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(ollama, 'httpx', type('M', (), {'Client': Dummy}))
    text = "hello"
    result = ollama.generate(text)
    assert "placeholder" in result


def test_generate_caching(monkeypatch):
    calls = []

    class DummyResp:
        def __init__(self, text):
            self._text = text
        def raise_for_status(self):
            pass
        def json(self):
            return {"choices": [{"text": self._text}]}

    class DummyClient:
        def __init__(self, timeout=None):
            pass
        def post(self, url, json):
            calls.append((url, json))
            return DummyResp("ok")
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(ollama, 'httpx', type('M', (), {'Client': DummyClient}))
    # first call should make HTTP request
    r1 = ollama.generate("foo")
    assert r1 == "ok"
    # second call with the same prompt should use cache (no new call)
    r2 = ollama.generate("foo")
    assert r2 == "ok"
    assert len(calls) == 1
