

ledger_pool_handle = None


def get_pool_handle():
    global ledger_pool_handle
    return ledger_pool_handle

def set_pool_handle(pool_handle):
    global ledger_pool_handle
    ledger_pool_handle = pool_handle

    