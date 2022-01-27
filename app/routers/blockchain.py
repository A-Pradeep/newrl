import json
import logging
from types import new_class

from fastapi import APIRouter
from fastapi.datastructures import UploadFile
from fastapi.params import File
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from starlette.responses import FileResponse

from app.codes.transactionmanager import Transactionmanager

from .request_models import AddWalletRequest, BalanceRequest, BalanceType, CallSC, CreateTokenRequest, CreateWalletRequest, RunSmartContractRequest, TransferRequest, CreateSCRequest, TscoreRequest
from app.codes.chainscanner import Chainscanner, download_chain, download_state, get_transaction
from app.codes.kycwallet import add_wallet, generate_wallet_address, get_address_from_public_key, get_digest, generate_wallet
from app.codes.tokenmanager import create_token_transaction
from app.codes.transfermanager import Transfermanager
from app.codes.utils import save_file_and_get_path
from app.codes import validator
from app.codes import signmanager
from app.codes import updater
from app.codes.contracts.nusd1 import create_contract_address

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()

v1_tag = 'V1 For Humans'
v2_tag = 'V2 For Machines'

@router.post("/create-transfer", tags=[v1_tag])
async def create_transfer(transfer_request: TransferRequest):
    """Used to create a transfer file which can be signed and executed by /sign and /transfer respectively"""
    transfer_type = transfer_request.transfer_type
    trandata = {
        "transfer_type": transfer_type,
        "asset1_code": str(transfer_request.asset1_code),
        "asset2_code": str(transfer_request.asset2_code),
        "wallet1": transfer_request.wallet1_address,
        "wallet2": transfer_request.wallet2_address,
        "asset1_number": int(transfer_request.asset1_qty),
        "asset2_number": int(transfer_request.asset2_qty)
    }
    newtransfer = Transfermanager(trandata)
    transaction = newtransfer.loadandcreate()
#    with open("./transfernew.json","r") as tfile:
#        transferfile_path = save_file_and_get_path(tfile)
    # transferfile = FileResponse(file, filename="transferfile.json")
    return transaction


@router.post("/generate-wallet-transaction", tags=[v1_tag])
async def generate_wallet_api(req: CreateWalletRequest):
    """Generate a new wallet"""
    try:
        req = req.dict()
        add_wallet_transaction = generate_wallet(
            req['custodian_address'], req['kyc_docs'], 
            req['ownertype'], req['jurisdiction'], req['specific_data'])
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))

    return FileResponse(add_wallet_transaction, filename="add_wallet_transaction.json")

@router.post("/add-wallet-to-chain", tags=[v1_tag])
async def add_wallet_to_chain_api(req: AddWalletRequest):
    """Get a transaction file for adding an existing wallet to chain"""
    try:
        req_dict = req.dict()
        add_wallet_transaction = add_wallet(req.custodian_address, req_dict['kyc_docs'], req.ownertype, 
            req.jurisdiction, req.public_key, req.specific_data)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))
    return FileResponse(add_wallet_transaction, filename="add_wallet_transaction.json")

@router.post("/get-file-hash", tags=[v1_tag])
async def validate(transactionfile: UploadFile = File(...)):
    """Get hash code for a file. Ideally done at the application side"""
    file_tmp_path = save_file_and_get_path(transactionfile)
    return get_digest(file_tmp_path)


@router.post("/get-wallet-file", tags=[v1_tag])
async def get_wallet_file(transferfile: UploadFile = File(...)):
    """Returns the wallet file from the add_wallet_transaction.json"""
    f1 = save_file_and_get_path(transferfile)
    with open(f1, 'r+') as file:
        data = json.load(file)
        walletfile = data["transaction"]["specific_data"]["wallet_address"] + "_wallet.json"
    return FileResponse(walletfile, filename="walletfile.json")


@router.post("/sign", tags=[v1_tag])
async def sign(wallet_file: UploadFile = File(...), transactionfile: UploadFile = File(...)):
    """Custodian wallet file can be used to sign a transaction"""
    transactionfile_path = save_file_and_get_path(transactionfile)
    wallet_file = save_file_and_get_path(wallet_file)
    singed_transaction_file = signmanager.sign(
        wallet_file, transactionfile_path)
    return singed_transaction_file


@router.post("/validate", tags=[v1_tag])
async def validate(transactionfile: UploadFile = File(...)):
    """Validate a given transaction file if it's included in chain"""
    try:
        transactionfile_path = save_file_and_get_path(transactionfile)
        with open(transactionfile_path) as f:
            transaction = json.loads(f)
            response = validator.validate(transaction)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "SUCCESS", "response": response}


@router.post("/create-token", tags=[v1_tag])
async def create_token(
    request: CreateTokenRequest
):
    token_data = {
        "tokenname": request.token_name,
        "tokencode" : request.token_code,
        "tokentype": request.token_type,
        "tokenattributes": request.token_attributes,
        "first_owner": request.first_owner,
        "custodian": request.custodian,
        "legaldochash": request.legal_doc,
        "amount_created": request.amount_created,
        "value_created": request.value_created,
        "disallowed": request.disallowed_regions,
        "sc_flag": request.is_smart_contract_token
    }
    try:
        token_create_transaction_filename = create_token_transaction(token_data)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))
    response_file = FileResponse(token_create_transaction_filename, filename="token_create_transaction.json")
    return response_file


@router.post("/run-updater", tags=[v1_tag, v2_tag], response_class=HTMLResponse)
async def run_updater():
    try:
        log = updater.run_updater()
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))
    HTMLResponse(content=log, status_code=200)
    return log


@router.get("/get-transaction", tags=[v1_tag, v2_tag])
async def get_transaction_api(transaction_code: str):
    try:
        return get_transaction(transaction_code)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download-chain", tags=[v1_tag, v2_tag])
async def download_chain_api():
    return download_chain()


@router.get("/download-state", tags=[v1_tag, v2_tag])
async def download_state_api():
    return download_state()


@router.post("/get-balance", tags=[v1_tag, v2_tag])
async def get_balance(req: BalanceRequest):
    chain_scanner = Chainscanner()
    if req.balance_type == BalanceType.TOKEN_IN_WALLET:
        balance = chain_scanner.getbaladdtoken(
            req.wallet_address, str(req.token_code))
    elif req.balance_type == BalanceType.ALL_TOKENS_IN_WALLET:
        balance = chain_scanner.getbalancesbyaddress(req.wallet_address)
    elif req.balance_type == BalanceType.ALL_WALLETS_FOR_TOKEN:
        balance = chain_scanner.getbalancesbytoken(str(req.token_code))
    return {'balance': balance}

@router.get("/get-address-from-publickey", tags=[v1_tag, v2_tag])
async def get_address_from_public_key_api(public_key: str):
    try:
        address = get_address_from_public_key(public_key)
        return {'address': address}
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/generate-wallet-address", tags=[v1_tag, v2_tag])
async def generate_wallet_address_api():
    return generate_wallet_address()

# v2 APIs - JSON only

@router.get("/generate-contract-address", tags=[v1_tag, v2_tag])
async def generate_contract_address_api():
    return create_contract_address()

@router.post("/add-wallet", tags=[v2_tag])
async def add_wallet_api(req: AddWalletRequest):
    """Get a transaction file for adding an existing wallet to chain"""
    try:
        req_dict = req.dict()
        add_wallet_transaction = add_wallet(req.custodian_address, req_dict['kyc_docs'], req.ownertype, 
            req.jurisdiction, req.public_key, req.specific_data)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))
    
    with open(add_wallet_transaction) as f:
        return json.load(f)
    # return FileResponse(add_wallet_transaction, filename="add_wallet_transaction.json")

@router.post("/add-token", tags=[v2_tag])
async def add_token(
    request: CreateTokenRequest
):
    token_data = {
        "tokenname": request.token_name,
        "tokencode" : request.token_code,
        "tokentype": request.token_type,
        "tokenattributes": request.token_attributes,
        "first_owner": request.first_owner,
        "custodian": request.custodian,
        "legaldochash": request.legal_doc,
        "amount_created": request.amount_created,
        "value_created": request.value_created,
        "disallowed": request.disallowed_regions,
        "sc_flag": request.is_smart_contract_token
    }
    try:
        token_create_transaction_filename = create_token_transaction(token_data)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))
    with open(token_create_transaction_filename) as f:
        return json.load(f)

@router.post("/add-transfer", tags=[v2_tag])
async def add_transfer(transfer_request: TransferRequest):
    """Used to create a transfer file which can be signed and executed by /sign and /transfer respectively"""
    transfer_type = transfer_request.transfer_type
    trandata = {
        "transfer_type": transfer_type,
        "asset1_code": str(transfer_request.asset1_code),
        "asset2_code": str(transfer_request.asset2_code),
        "wallet1": transfer_request.wallet1_address,
        "wallet2": transfer_request.wallet2_address,
        "asset1_number": int(transfer_request.asset1_qty),
        "asset2_number": int(transfer_request.asset2_qty)
    }
    type = transfer_request.transfer_type
    fulltrandata = {
        "transaction": {
            "timestamp": "",
            "trans_code": "000000",
            "type": type,
            "currency": "INR",
            "fee": 0.0,
            "descr": "",
            "valid": 1,
            "block_index": 0,
            "specific_data": trandata
        },
        "signatures": []
    }
    with open("transfernew.json", 'w') as file:
        json.dump(fulltrandata, file)

    newtransfer = Transfermanager(transfer_data=fulltrandata)
    tdatanew = newtransfer.loadandcreate()
    return tdatanew
#    with open("./transfernew.json","r") as tfile:
#        transferfile_path = save_file_and_get_path(tfile)
#    transferfile = FileResponse(
#        "transfernew.json", filename="transferfile.json")
#    with open("transfernew.json") as f:
#        return json.load(f)

@router.post("/add-sc", tags=[v2_tag])
async def add_sc(sc_request: CreateSCRequest):
    """Used to create a sc object which can be used to set up and deploy a smart contract"""
    scdata = {
        "creator":sc_request.creator,
        "ts_init":None,
        "name":sc_request.sc_name,
        "version":sc_request.version,
        "actmode":sc_request.actmode,
        "status":0,
        "next_act_ts":None,
        "signatories":sc_request.signatories,
        "parent":None,
        "oracleids":None,
        "selfdestruct":1,
        "contractspecs":sc_request.contractspecs,
        "legalparams":sc_request.legalparams
        }

    txspecdata = {
        "address": sc_request.sc_address,
        "function" : "setup",
        "signers" : [sc_request.creator],
        "params" : scdata
    }

    fulltrandata = {
        "transaction": {
            "timestamp": "",
            "trans_code": "000000",
            "type": 3,
            "currency": "INR",
            "fee": 0.0,
            "descr": "",
            "valid": 1,
            "block_index": 0,
            "specific_data": txspecdata
        },
        "signatures": []
    }
#    with open("transfernew.json", 'w') as file:
#        json.dump(fulltrandata, file)
    newsc = Transactionmanager()
    tdatanew = newsc.transactioncreator(fulltrandata)
    return tdatanew

@router.post("/call-sc", tags=[v2_tag])
async def call_sc(sc_request: CallSC):
    """Used to create a sc object which can be used to set up and deploy a smart contract"""

    txspecdata = {
        "address": sc_request.sc_address,
        "function" : sc_request.function_called,
        "signers" : sc_request.signers,
        "params" : sc_request.params
    }

    fulltrandata = {
        "transaction": {
            "timestamp": "",
            "trans_code": "000000",
            "type": 3,
            "currency": "INR",
            "fee": 0.0,
            "descr": "",
            "valid": 1,
            "block_index": 0,
            "specific_data": txspecdata
        },
        "signatures": []
    }
#    with open("transfernew.json", 'w') as file:
#        json.dump(fulltrandata, file)
    newtx = Transactionmanager()
    tdatanew = newtx.transactioncreator(fulltrandata)
    return tdatanew

@router.post("/run-contract", tags=[v2_tag])
async def run_contract(req: RunSmartContractRequest):
    """Run a smart contract"""
    try:
        return contract_executor.run(req.contract_name, req.params)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-trustscore", tags=[v2_tag])
async def update_ts(ts_request: TscoreRequest):
    """Used to update trust score of person1 for person 2 """

    txspecdata = {
        "address1": ts_request.source_address,
        "address2": ts_request.destination_address,
        "new_score" : ts_request.tscore,
    }

    fulltrandata = {
        "transaction": {
            "timestamp": "",
            "trans_code": "000000",
            "type": 6,
            "currency": "INR",
            "fee": 0.0,
            "descr": "",
            "valid": 1,
            "block_index": 0,
            "specific_data": txspecdata
        },
        "signatures": []
    }
#    with open("transfernew.json", 'w') as file:
#        json.dump(fulltrandata, file)
    newtx = Transactionmanager()
    tdatanew = newtx.transactioncreator(fulltrandata)
    return tdatanew

@router.post("/sign-transaction", tags=[v2_tag])
async def sign_transaction(wallet_data: dict, transaction_data: dict):
    """Custodian wallet file can be used to sign a transaction"""
    # transactionfile_path = save_file_and_get_path(transactionfile)
    # wallet_file = save_file_and_get_path(wallet_file)
    singed_transaction_file = signmanager.sign_transaction(wallet_data, transaction_data)
    return singed_transaction_file

@router.post("/validate-transaction", tags=[v2_tag])
async def validate_transaction(transaction_data: dict):
    """Validate a given transaction file if it's included in chain"""
    try:
        response = validator.validate(transaction_data)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "SUCCESS", "response": response}
