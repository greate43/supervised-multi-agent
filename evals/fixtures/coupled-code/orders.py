from inventory import available, decrement


def reserve(sku, quantity):
    if available(sku) < quantity:
        return False
    decrement(sku, quantity)
    return True
