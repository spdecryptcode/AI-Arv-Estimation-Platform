"""Stub implementations of data extraction classes described in docs."""
from abc import ABC, abstractmethod
import csv
from typing import Iterator, Dict, Any


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self) -> Iterator[Dict[str, Any]]:
        """Pull data from a source and return an iterator of records."""


class SocrataExtractor(BaseExtractor):
    def __init__(self, dataset_id: str, app_token: str | None = None):
        self.dataset_id = dataset_id
        self.app_token = app_token

    def extract(self) -> Iterator[Dict[str, Any]]:
        # this is still a stub; real implementation would talk to the Socrata
        # API using ``sodapy`` and handle paging.  here we simply raise for now
        raise NotImplementedError("SocrataExtractor.extract not implemented")


class CSVExtractor(BaseExtractor):
    def __init__(self, filepath: str, delimiter: str = ","):
        self.filepath = filepath
        self.delimiter = delimiter

    def extract(self) -> Iterator[Dict[str, Any]]:
        """Stream rows from a CSV file as dictionaries.

        Example usage::

            for row in CSVExtractor("data.csv").extract():
                process(row)

        The extractor does not load the entire file into memory.
        """
        with open(self.filepath, newline="") as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)
            for row in reader:
                yield row


class OSMExtractor(BaseExtractor):
    def __init__(self, bbox: tuple):
        self.bbox = bbox

    def extract(self) -> Iterator[Dict[str, Any]]:
        # Real implementation would query OpenStreetMap Overpass API.
        raise NotImplementedError("OSMExtractor.extract not implemented")
