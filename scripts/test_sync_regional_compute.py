#!/usr/bin/env python3
"""Regression checks for the regional map's Summary-table reader."""

import unittest

from sync_regional_compute import REGION_META, parse_values, update_index


def summary_rows():
    rows = [
        ["Last updated 2026-09-16"],
        ["Table S1: Headline estimate"],
        ["Region", "FP8 GB300e p10", "FP8 GB300e p50", "FP8 GB300e p90",
         "FP8 share p10", "FP8 share p50", "FP8 share p90",
         "FP4 GB300e p50", "FP4 share p50", "BW GB300e p50", "BW share p50"],
    ]
    for index, name in enumerate(REGION_META, 1):
        rows.append([name, 80 * index, 100 * index, 120 * index,
                     0.08, 0.1, 0.12, 50 * index, 0.1, 200 * index, 0.1])
    rows.extend([
        ["World total", 4500, 4500, 4500],
        [],
        ["Table S3: Share of world compute over time"],
        ["Region", "2023", "2024", "2025", "2026E"],
    ])
    rows.extend([[name, 0.1, 0.1, 0.1, 0.1] for name in REGION_META])
    return rows


class SummaryTableBoundaryTests(unittest.TestCase):
    def test_later_share_table_cannot_overwrite_headline_compute(self):
        updated, regions = parse_values(summary_rows())
        self.assertEqual(updated, "2026-09-16")
        self.assertEqual(len(regions), len(REGION_META))
        self.assertEqual([row["fp8"] for row in regions], list(range(100, 1000, 100)))
        self.assertEqual(regions[0]["fp8P10"], 80)
        self.assertEqual(regions[0]["fp8P90"], 120)

    def test_later_share_table_cannot_supply_missing_headline_region(self):
        rows = summary_rows()
        del rows[3]  # China is absent in S1 but still present in S3.
        with self.assertRaisesRegex(ValueError, "Missing expected regions.*China"):
            parse_values(rows)

    def test_source_date_and_cache_key_update_only_the_regional_map(self):
        original = ('<meta name="robots" content="noindex, nofollow">\n'
                    '<p>Other section (updated August 13, 2026)</p>\n'
                    'regional compute model, Summary tab</a> (updated August 13, 2026).\n'
                    '<script src="regional_data.js?v=old"></script>')
        result = update_index(original, "2026-09-16", "newhash")
        self.assertIn('content="noindex, nofollow"', result)
        self.assertIn('Other section (updated August 13, 2026)', result)
        self.assertIn('Summary tab</a> (updated September 16, 2026)', result)
        self.assertIn('regional_data.js?v=newhash', result)


if __name__ == "__main__":
    unittest.main()
