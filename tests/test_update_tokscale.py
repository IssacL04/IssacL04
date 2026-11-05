import copy
import unittest

from scripts.update_tokscale import END, START, render_models, replace_models


class ModelTableTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "user": {"username": "IssacL04"},
            "period": "month",
            "dateRange": {"start": "2026-10-07", "end": "2026-11-05"},
            "modelUsage": [
                {"model": "small", "tokens": 1, "cost": 0},
                {"model": "large|<tag>", "tokens": 1234, "cost": 2.125},
            ],
        }

    def test_formats_and_sorts_models_without_injecting_markup(self):
        table = render_models(self.data)
        self.assertIn("2026-10-07 to 2026-11-05", table)
        self.assertIn("large\\|&lt;tag&gt; | 1,234 | $2.12", table)
        self.assertIn("small | 1 | $0.00", table)
        self.assertLess(table.index("large"), table.index("small"))
        self.assertNotIn("<tag>", table)

    def test_rejects_wrong_account_period_and_date_window(self):
        for field, value in (("period", "all"), ("user", {"username": "someone"}),
                             ("dateRange", {"start": "2026-10-01", "end": "2026-11-05"})):
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                data[field] = value
                with self.assertRaises(ValueError):
                    render_models(data)

    def test_rejects_invalid_metrics_and_handles_empty_usage(self):
        for field, value in (("tokens", -1), ("tokens", True), ("cost", float("nan")),
                             ("cost", -1), ("model", "")):
            with self.subTest(field=field, value=value):
                data = copy.deepcopy(self.data)
                data["modelUsage"][0][field] = value
                with self.assertRaises(ValueError):
                    render_models(data)
        self.data["modelUsage"] = []
        self.assertIn("No model usage in this window", render_models(self.data))

    def test_preserves_handwritten_content_and_requires_valid_markers(self):
        readme = f"intro\n{START}\nold table\n{END}\nfooter\n"
        self.assertEqual(replace_models(readme, "new table"),
                         f"intro\n{START}\nnew table\n{END}\nfooter\n")
        for broken in ("no markers", readme + START, END + START):
            with self.subTest(readme=broken), self.assertRaises(ValueError):
                replace_models(broken, "new table")


if __name__ == "__main__":
    unittest.main()
