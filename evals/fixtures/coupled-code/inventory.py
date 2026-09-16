STOCK = {"SKU-1": 3, "SKU-2": 1}


def canonical_sku(sku):
    return sku


def available(sku):
    return STOCK.get(canonical_sku(sku), 0)


def decrement(sku, quantity):
    key = canonical_sku(sku)
    STOCK[key] -= quantity
