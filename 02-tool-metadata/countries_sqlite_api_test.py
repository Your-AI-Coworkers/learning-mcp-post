from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
import unittest

import countries_sqlite_api as api


class CountriesSqliteApiTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp_path = Path(tempfile.mkdtemp())
        self.csv_path = tmp_path / "countries.csv"
        self.db_path = tmp_path / "countries.sqlite"
        shutil.copy2(api.CSV_PATH, self.csv_path)

        self._orig_csv_path = api.CSV_PATH
        self._orig_db_path = api.DB_PATH
        api.CSV_PATH = self.csv_path
        api.DB_PATH = self.db_path
        self.addCleanup(self._restore_paths)

    def _restore_paths(self) -> None:
        api.CSV_PATH = self._orig_csv_path
        api.DB_PATH = self._orig_db_path

    def test_builds_sqlite_database(self) -> None:
        api._build_db()
        self.assertTrue(self.db_path.exists())
        self.assertGreater(self.db_path.stat().st_size, 0)
        self.assertEqual(api.country_count(), 227)

    def test_search_countries_matches_country_name(self) -> None:
        api._build_db()
        rows = api.search_countries("Afghan")
        self.assertGreaterEqual(len(rows), 1)
        self.assertEqual(rows[0]["Country"].strip(), "Afghanistan")

    def test_get_country_returns_exact_match(self) -> None:
        api._build_db()
        row = api.get_country("Albania")
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row["Country"].strip(), "Albania")
        self.assertEqual(row["Region"].strip(), "EASTERN EUROPE")


if __name__ == "__main__":
    unittest.main()
