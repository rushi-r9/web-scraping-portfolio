import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scraper import scrape_dataset, export_rows
ROOT=Path(__file__).resolve().parents[1]
class ScraperTests(unittest.TestCase):
    def test_all_fixture_datasets_have_rows_and_follow_pages(self):
        for name in ('products','properties','jobs','businesses'):
            with self.subTest(dataset=name):
                rows, report=scrape_dataset(name, ROOT/'fixtures')
                self.assertGreater(len(rows), 0)
                self.assertGreater(report['pages_read'], 1)
                self.assertEqual(len(rows), len({r[next(k for k in r if k.endswith('_id') or k=='sku')] for r in rows}))
    def test_product_fixture_deduplicates_to_120(self):
        rows, report=scrape_dataset('products', ROOT/'fixtures')
        self.assertEqual(len(rows),120)
        self.assertEqual(report['pages_read'],6)
    def test_exports_csv_json_quality_and_sqlite(self):
        rows, report=scrape_dataset('jobs', ROOT/'fixtures')
        with tempfile.TemporaryDirectory() as tmp:
            export_rows('jobs', rows, report, Path(tmp))
            for name in ('jobs.csv','jobs.json','jobs-quality-report.json','portfolio_demo.sqlite'):
                self.assertTrue((Path(tmp)/name).exists(), name)
if __name__=='__main__': unittest.main()
