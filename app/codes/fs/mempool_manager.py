"""Temp file manager"""

import glob
import json

from ...constants import MEMPOOL_PATH, TMP_PATH

def get_receipts_from_storage(block_index, folder=MEMPOOL_PATH):
    """Returns a list of receipts matching a block index from mempool"""
    blocks = []
    for block_file in glob.glob(f'{folder}/receipt_{block_index}_*.json'):
        with open(block_file, 'r') as _file:
            block = json.load(_file)
            blocks.append(block)
    return blocks


def store_block_to_temp(block, folder=TMP_PATH):
    block_index = block['index']
    existing_files_for_block = glob.glob(f'{folder}/block_{block_index}_*.json')
    new_file_name = f'{folder}/block_{block_index}_{len(existing_files_for_block)}.json'
    with open(new_file_name, 'w') as _file:
        json.dump(block, _file)
    return new_file_name


def store_receipt_to_temp(receipt, folder=TMP_PATH):
    block_index = receipt['data']['block_index']
    existing_files_for_block = glob.glob(f'{folder}/receipt_{block_index}_*.json')
    new_file_name = f'{folder}/receipt_{block_index}_{len(existing_files_for_block)}.json'
    with open(new_file_name, 'w') as _file:
        json.dump(receipt, _file)
    return new_file_name


def append_receipt_to_block(block, new_receipt):
    if 'receipts' not in block:
        block['receipts'] = []
    
    receipt_already_exists = False
    for receipt in block['receipts']:
        if receipt['public_key'] == new_receipt['public_key']:
            receipt_already_exists = True
            break
    
    if not receipt_already_exists:
        block['receipts'].append(new_receipt)
        return True
    
    return False


def append_receipt_to_block_in_storage(receipt):
    block_folder=TMP_PATH
    block_index = receipt['data']['block_index']
    blocks = []
    for block_file in glob.glob(f'{block_folder}/block_{block_index}_*.json'):
        with open(block_file, 'r+') as _file:
            block = json.load(_file)
            if append_receipt_to_block(block):
                json.dump(block, _file)
                blocks.append(block)
    return blocks