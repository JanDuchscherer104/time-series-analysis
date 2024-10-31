import unittest

import pandas as pd
from darts import TimeSeries
from darts.models import NaiveSeasonal
from tsa_helpers.multi_index import MITimeSeries


class TestMultiIndex(unittest.TestCase):

    def setUp(self):
        data = {
            "date": pd.date_range(start="2020-01-01", periods=10, freq="D"),
            "key": ["A"] * 5 + ["B"] * 5,
            "value": range(10),
        }
        self.sample_dataframe = pd.DataFrame(data)
        self.mits = MITimeSeries(
            df=self.sample_dataframe, key_col="key", value_cols="value"
        )

    def test_initialization(self):
        self.assertEqual(len(self.mits), 2)
        self.assertIn(("A",), self.mits.keys_list())
        self.assertIn(("B",), self.mits.keys_list())

    def test_getitem(self):
        ts_a = self.mits[("A",)]
        self.assertIsInstance(ts_a, TimeSeries)
        self.assertEqual(len(ts_a), 5)

    def test_setitem(self):
        new_ts = TimeSeries.from_dataframe(
            self.sample_dataframe[self.sample_dataframe["key"] == "A"],
            value_cols="value",
        )
        self.mits[("C",)] = new_ts
        self.assertIn(("C",), self.mits.keys_list())
        self.assertEqual(len(self.mits), 3)

    def test_keys_list(self):
        keys = self.mits.keys_list()
        self.assertEqual(len(keys), 2)
        self.assertIn(("A",), keys)
        self.assertIn(("B",), keys)

    def test_items_list(self):
        items = self.mits.items_list()
        self.assertEqual(len(items), 2)
        self.assertIsInstance(items[0][1], TimeSeries)

    def test_to_df(self):
        df = self.mits.to_df()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 10)

    def test_attach_and_fit(self):
        model = NaiveSeasonal()
        self.mits.attach_and_fit(model)
        self.assertTrue(hasattr(self.mits, "_MITimeSeries__models"))

    def test_predict(self):
        model = NaiveSeasonal()
        self.mits.attach_and_fit(model)
        predictions = self.mits.predict(forecast_horizon=3)
        self.assertIsInstance(predictions, MITimeSeries)
        self.assertEqual(len(predictions), 2)

    def test_head(self):
        head_df = self.mits.head(3)
        self.assertEqual(len(head_df), 3)

    def test_apply(self):
        def add_one(ts):
            return ts + 1

        new_mits = self.mits.apply(add_one)
        self.assertIsInstance(new_mits, MITimeSeries)
        self.assertEqual(len(new_mits), 2)

        # Compare the values
        for key in self.mits.keys_list():
            original_ts = self.mits[key]
            new_ts = new_mits[key]

            # Convert to pandas DataFrames
            original_df = original_ts.pd_dataframe()
            new_df = new_ts.pd_dataframe()

            # Compute the difference
            diff = new_df - original_df

            # Assert that all differences are 1
            self.assertTrue((diff.values == 1).all())

    def test_info(self):
        self.mits.info()  # This should print the information without errors


if __name__ == "__main__":
    unittest.main()
