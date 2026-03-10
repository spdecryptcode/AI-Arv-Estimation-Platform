import os
import sys
import csv
import tempfile
import pathlib
import pytest

# make the services directory importable so we can import our package
ws_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(ws_root)
import data_pipeline.extractors as extractors
import data_pipeline.transformers as transformers


def test_csv_extractor(tmp_path):
    # create a small CSV file
    p = tmp_path / "data.csv"
    with open(p, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["a", "b"])
        writer.writerow(["1", "x"])
        writer.writerow(["2", "y"])

    extractor = extractors.CSVExtractor(str(p))
    rows = list(extractor.extract())
    assert len(rows) == 2
    assert rows[0]["a"] == "1"
    assert rows[1]["b"] == "y"


def test_address_normalizer():
    rec = {"Name": " Alice ", "Age": 30}
    out = transformers.AddressNormalizer.normalize(rec)
    assert "name" in out and out["name"] == "Alice"
    assert out["age"] == 30


def test_property_normalizer():
    rec = {"addr": "123 Main", "zip_code": "12345", "ownername": "Bob"}
    out = transformers.PropertyNormalizer.normalize(rec)
    assert out["address"] == "123 Main"
    assert out["zip"] == "12345"
    assert out["owner"] == "Bob"


def test_amenity_scorer():
    rec = {"amenities": ["park", "school"]}
    assert transformers.AmenityScorer.score(rec) == 2.0
    assert transformers.AmenityScorer.score({}) == 0.0


def test_geocoder_and_enricher():
    loc = transformers.Geocoder.geocode("somewhere")
    assert loc["lat"] == 0.0 and loc["lon"] == 0.0
    rec = {"foo": "bar"}
    enr = transformers.GeoEnricher.enrich(rec)
    assert enr.get("neighborhood") == "unknown"
