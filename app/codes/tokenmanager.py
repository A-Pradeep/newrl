# Python programm to create object that enables addition of a block

import datetime

from .transactionmanager import Transactionmanager


def create_token_transaction(token_data):
    transaction = {
        'timestamp': str(datetime.datetime.now()),
        'type': 2,
        'currency': "INR",
        'fee': 0.0,
        'descr': "New token creation",
        'valid': 1,
        'block_index': 0,
        'specific_data': token_data
    }

    trans = Transactionmanager()
    transaction_data = {'transaction': transaction, 'signatures': []}
    trans.transactioncreator(transaction_data)
    transaction_file = trans.save_transaction_to_mempool()
    return transaction_file
