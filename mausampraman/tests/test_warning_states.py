import data.warning_store as WS


def test_active_warning(tmp_path, monkeypatch):
    monkeypatch.setattr(WS, "DIR", tmp_path)
    WS.save_warning("Nashik", "orange", "Heavy rain", "Stay in.", "2026-01-01")
    r = WS.get_warning("Nashik")
    assert r["status"] == "active_warning" and r["severity"] == "orange"


def test_no_warning_confirmed(tmp_path, monkeypatch):
    monkeypatch.setattr(WS, "DIR", tmp_path)
    WS.save_warning("Pune", "green", "Calm", "", "2026-01-01")
    assert WS.get_warning("Pune")["status"] == "no_warning_confirmed"


def test_district_not_covered(tmp_path, monkeypatch):
    monkeypatch.setattr(WS, "DIR", tmp_path)
    r = WS.get_warning("Nowhere")
    assert r["status"] == "district_not_covered" and r["severity"] == "green"


def test_data_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr(WS, "DIR", tmp_path / "missing-parent" / "unwritable")
    (tmp_path / "missing-parent").mkdir()
    (tmp_path / "missing-parent" / "unwritable").write_text("not a dir")
    assert WS.get_warning("X")["status"] == "warning_data_unavailable"


def test_status_texts_exact():
    assert WS.STATUS_TEXT["active_warning"] == "Official warning active"
    assert WS.STATUS_TEXT["no_warning_confirmed"] == "No active warning reported by the available source"
    assert WS.STATUS_TEXT["warning_data_unavailable"] == "Warning status unavailable"
    assert WS.STATUS_TEXT["district_not_covered"] == "Warning coverage unavailable for this location"
