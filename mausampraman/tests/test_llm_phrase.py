import os
import time

import httpx
import pytest

from phrasing.llm_phrase import phrase

HAS_KEY = bool(os.environ.get("SARVAM_API_KEY"))
needs_key = pytest.mark.skipif(not HAS_KEY, reason="no live SARVAM_API_KEY")

EN = {"grade": "B", "action": "Delay pesticide spray.", "rationale": "Models disagree on rain.", "values": {"temp_c": 28.5, "rain_mm": 12.0}}
HI = {"grade": "C", "action": "Delay harvest prep.", "rationale": "Models disagree on rain.", "values": {"temp_c": 31.0, "rain_mm": 4.5}}
WARN = {"grade": "D", "action": "Stay indoors.", "rationale": "Orange alert.", "warning_text": "Heavy rainfall likely.", "values": {"rain_mm": 66.5}}


@needs_key
def test_1_english_live():
    out = phrase(EN, "en")
    assert isinstance(out, str) and out and "12.0" in out


@needs_key
def test_2_hindi_live():
    out = phrase(HI, "hi")
    assert isinstance(out, str) and out and "4.5" in out


def test_3_missing_key_fallback(monkeypatch):
    monkeypatch.delenv("SARVAM_API_KEY", raising=False)
    t = time.time()
    out = phrase(EN, "en")
    assert time.time() - t < 3
    assert "Delay pesticide spray" in out


def test_4_invalid_key_fallback(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "bogus-key")
    out = phrase(EN, "en")
    assert "Delay pesticide spray" in out


def test_5_timeout_fallback(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "x")
    def boom(*a, **k):
        raise httpx.TimeoutException("slow")
    monkeypatch.setattr(httpx, "post", boom)
    assert "Delay pesticide spray" in phrase(EN, "en")


class _BadResp:
    def raise_for_status(self):
        pass
    def json(self):
        return {"nope": []}


def test_6_malformed_fallback(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "x")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _BadResp())
    assert "Delay pesticide spray" in phrase(EN, "en")


def test_7_warning_preserved(monkeypatch):
    monkeypatch.delenv("SARVAM_API_KEY", raising=False)
    out = phrase(WARN, "en")
    assert out.startswith("Heavy rainfall likely.")


def test_8_exact_values_sent(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "x")
    seen = {}
    class _Ok:
        def raise_for_status(self):
            pass
        def json(self):
            return {"choices": [{"message": {"content": "ok Delay pesticide spray Models disagree on rain 28.5 12.0"}}]}
    def spy(*a, **k):
        seen.update(k.get("json") or {})
        seen["headers"] = k.get("headers") or {}
        return _Ok()
    monkeypatch.setattr(httpx, "post", spy)
    assert phrase(EN, "en").startswith("ok Delay pesticide spray Models")
    assert seen["headers"].get("api-subscription-key") == "x"
    user_text = seen["messages"][1]["content"]
    assert "28.5" in user_text and "12.0" in user_text
    assert seen["messages"][0]["role"] == "system"


class _Text:
    def __init__(self, t):
        self.t = t
    def raise_for_status(self):
        pass
    def json(self):
        return {"choices": [{"message": {"content": self.t}}]}


def test_10_numbers_kept(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "x")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _Text("Delay pesticide spray. Models disagree on rain. Expect 28.5C and 12.0mm rain."))
    assert phrase(EN, "en").startswith("Delay pesticide")


def test_12_grounded_hindi_kept(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "x")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _Text("तापमान 31.0, बारिश 4.5 मिलीमीटर।"))
    assert phrase(HI, "hi").startswith("तापमान")


def test_13_invented_number_discarded(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "x")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _Text("Delay pesticide spray. Models disagree on rain. Expect 28.5C, 12.0mm and 99.9mm more."))
    assert phrase(EN, "en").startswith("Grade B")


def test_14_changed_number_discarded(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "x")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _Text("Delay pesticide spray. Models disagree on rain. Expect 28.5C and 12.5mm rain."))
    assert phrase(EN, "en").startswith("Grade B")


def test_15_warning_grounded_kept(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "x")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _Text("Stay indoors. Orange alert. Heavy rainfall likely with 66.5mm rain."))
    assert phrase(WARN, "en").startswith("Stay indoors")


def test_16_softened_warning_discarded(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "x")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _Text("Stay indoors. Orange alert. Heavy rainfall likely, might be slight, 66.5mm rain."))
    assert phrase(WARN, "en").startswith("Heavy rainfall")


def test_17_contradicted_warning_discarded(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "x")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _Text("Stay indoors. No rain expected today, 66.5mm."))
    assert phrase(WARN, "en").startswith("Heavy rainfall")


def test_18_long_response_discarded(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "x")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _Text("Delay pesticide spray. Models disagree on rain. 28.5C 12.0mm. " + "filler " * 100))
    assert phrase(EN, "en").startswith("Grade B")


def test_11_dropped_number_discarded(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "x")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _Text("Delay spray, heavy rain."))
    out = phrase(EN, "en")
    assert out.startswith("Grade B") and "28.5" in out


def test_9_never_raises(monkeypatch):
    monkeypatch.delenv("SARVAM_API_KEY", raising=False)
    assert isinstance(phrase(None, "en"), str)
    assert isinstance(phrase({}, "xx"), str)
    assert isinstance(phrase({"values": None}, "hi"), str)
    monkeypatch.setenv("SARVAM_API_KEY", "x")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: 1 / 0)
    assert isinstance(phrase(EN, "en"), str)
