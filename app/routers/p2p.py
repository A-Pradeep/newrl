import sys
import uvicorn
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from starlette.requests import Request

from app.codes.chainscanner import download_chain, download_state, get_transaction
from app.codes.p2p.peers import add_peer, clear_peers, get_peers, init_bootstrap_nodes, update_peers
from app.codes.p2p.sync_chain import get_blocks, get_last_block_index, receive_block, sync_chain_from_node, sync_chain_from_peers
from app.codes.p2p.sync_mempool import get_mempool_transactions, list_mempool_transactions, sync_mempool_transactions
from app.constants import NEWRL_PORT
from app.migrations.init_db import clear_db, init_db
from .request_models import BlockAdditionRequest, BlockRequest, TransactionsRequest


router = APIRouter()

p2p_tag = 'p2p'

@router.post("/list-mempool-transactions", tags=[p2p_tag])
async def list_mempool_transactions_api():
    return list_mempool_transactions()

@router.post("/get-mempool-transactions", tags=[p2p_tag])
async def get_mempool_transactions_api(req: TransactionsRequest):
    return get_mempool_transactions(req.transaction_codes)

@router.post("/get-blocks", tags=[p2p_tag])
async def get_mempool_transactions_api(req: BlockRequest):
    return get_blocks(req.block_indexes)

@router.post("/receive-block", tags=[p2p_tag])
async def receive_block_api(req: BlockAdditionRequest):
    return receive_block(req.block)

@router.get("/get-last-block-index", tags=[p2p_tag])
async def get_last_block_index_api():
    return get_last_block_index()

@router.post("/sync-mempool-transactions", tags=[p2p_tag])
async def sync_mempool_transactions_api():
    return sync_mempool_transactions()

@router.post("/sync-chain-from-node", tags=[p2p_tag])
async def sync_chain_from_node_api(url: str = 'https://newrl-devnet1.herokuapp.com'):
    try:
        return sync_chain_from_node(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail='No more blocks')

@router.post("/sync-chain-from-peers", tags=[p2p_tag])
async def sync_chain_from_peers_api():
    return sync_chain_from_peers()

@router.post("/sync-chain-from-peers", tags=[p2p_tag])
async def sync_chain_from_peers_api():
    return sync_chain_from_peers()

@router.get("/get-transaction", tags=[p2p_tag])
async def get_transaction_api(transaction_code: str):
    return get_transaction(transaction_code)

@router.get("/download-chain", tags=[p2p_tag])
async def download_chain_api():
    return download_chain()

@router.get("/download-chain", tags=[p2p_tag])
async def download_chain_api():
    return download_chain()

@router.get("/download-state", tags=[p2p_tag])
async def download_state_api():
    return download_state()

@router.post("/clear-db-test-only", tags=[p2p_tag])
async def clear_db_api():
    """ For testing only. To be removed. Clear and initialise a fresh db """
    clear_db()
    init_db()
    return True

@router.get("/get-peers", tags=[p2p_tag])
async def get_peers_api():
    return get_peers()

@router.post("/add-peer", tags=[p2p_tag])
async def add_peer_api(req: Request):
    return await add_peer(req.client.host)

@router.post("/clear-peers", tags=[p2p_tag])
async def clear_peer_api(req: Request):
    return clear_peers()

@router.post("/initiate-peer-connection", tags=[p2p_tag])
async def initiate_peer_api(address: str):
    "Test only, used to first connect a client"
    return await add_peer(address)

import subprocess
@router.post("/update-software", tags=[p2p_tag])
async def update_software_api(should_update_peers: bool = False, bootstrap_again: bool = False):
    "Update the client software from repo"
    subprocess.call(["git", "pull"])
    if bootstrap_again:
        await init_bootstrap_nodes()
    if should_update_peers:
        await update_peers()
    return {'status': 'SUCCESS'}

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2 or sys.argv[1] != '--no-bootstrap':
            # init_bootstrap_nodes()
            pass
    except Exception as e:
        print('Bootstrap failed', str(e))
    uvicorn.run("p2p_main:app", host="0.0.0.0", port=NEWRL_PORT, reload=True)
