import unittest

import inventory
from orders import reserve


class ReserveTests(unittest.TestCase):
    def setUp(self):
        inventory.STOCK.clear()
        inventory.STOCK.update({"SKU-1": 3, "SKU-2": 1})

    def test_inventory_lookup_normalizes_case_and_whitespace(self):
        self.assertEqual(inventory.available(" sku-1 "), 3)

    def test_reservation_uses_normalized_sku(self):
        self.assertTrue(reserve(" sku-1 ", 2))
        self.assertEqual(inventory.STOCK["SKU-1"], 1)

    def test_invalid_or_unavailable_reservation_does_not_mutate_stock(self):
        original = dict(inventory.STOCK)
        self.assertFalse(reserve("", 1))
        self.assertFalse(reserve("SKU-1", 0))
        self.assertFalse(reserve("SKU-1", -1))
        self.assertFalse(reserve("SKU-1", 1.5))
        self.assertFalse(reserve("SKU-1", True))
        self.assertFalse(reserve("SKU-1", 4))
        self.assertEqual(inventory.STOCK, original)


if __name__ == "__main__":
    unittest.main()
