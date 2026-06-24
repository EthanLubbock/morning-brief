from datetime import date, timedelta

from brief import bins


def test_collection_today(sandbox):
    sandbox.write_bins([{"date": date.today().isoformat(), "bin": "blue"}])
    assert bins.bin_line() == "Bin collection today — blue"


def test_bins_out_tonight(sandbox):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    sandbox.write_bins([{"date": tomorrow, "bin": "green"}])
    assert bins.bin_line() == "Bins out tonight — green"


def test_no_bin_line_when_nothing_due(sandbox):
    far = (date.today() + timedelta(days=10)).isoformat()
    sandbox.write_bins([{"date": far, "bin": "blue"}])
    assert bins.bin_line() is None


def test_expiry_warning_when_near(sandbox):
    near = (date.today() + timedelta(days=14)).isoformat()
    sandbox.write_bins([{"date": near, "bin": "blue"}])
    warn = bins.expiry_warning()
    assert warn is not None and "runs out" in warn


def test_no_expiry_warning_when_far(sandbox):
    far = (date.today() + timedelta(days=90)).isoformat()
    sandbox.write_bins([{"date": far, "bin": "blue"}])
    assert bins.expiry_warning() is None


def test_empty_schedule_warns(sandbox):
    sandbox.write_bins([])
    assert "empty" in bins.expiry_warning()