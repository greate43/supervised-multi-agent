# Coupled-code fixture

Run `python3 -m unittest test_orders.py` from this directory. The fixture intentionally fails before the requested change; it should pass only after the task is completed correctly.

The task requires SKU normalization at the inventory API boundary, so callers of both `inventory.py` and `orders.py` receive the same behavior. A correct change preserves valid reservations and leaves stock unchanged for invalid or unavailable reservations.
