import sqlite3

db_path = 'newrl.db'

def clear_db():
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute('DROP TABLE IF EXISTS wallets')
    cur.execute('DROP TABLE IF EXISTS tokens')
    cur.execute('DROP TABLE IF EXISTS balances')
    cur.execute('DROP TABLE IF EXISTS blocks')
    cur.execute('DROP TABLE IF EXISTS transactions')
    cur.execute('DROP TABLE IF EXISTS transfers')
    con.commit()
    con.close()

def init_db():
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute('''
                    CREATE TABLE IF NOT EXISTS wallets
                    (wallet_address text NOT NULL PRIMARY KEY, 
                    wallet_public text,
                    wallet_private text,
                    custodian_wallet text,
                    kyc_docs text,
                    owner_type integer,
                    jurisdiction integer,
                    specific_data text)
                    ''')

    cur.execute('''
                    CREATE TABLE IF NOT EXISTS tokens
                    (tokencode integer  NOT NULL PRIMARY KEY, 
                    tokenname text,
                    tokentype integer,
                    first_owner text,
                    custodian text,
                    legaldochash text,
                    amount_created real,
                    value_created real,
                    sc_flag integer,
                    disallowed text,
                    parent_transaction_code text,
                    token_attributes text)
                    ''')

    cur.execute('''
                    CREATE TABLE IF NOT EXISTS balances
                    (wallet_address text, 
                    tokencode integer,
                    balance real, UNIQUE (wallet_address, tokencode))
                    ''')

    cur.execute('''
                    CREATE TABLE IF NOT EXISTS blocks
                    (block_index integer PRIMARY KEY,
                    timestamp text,
                    proof integer,
                    previous_hash text,
                    hash text,
                    transactions_hash text)
                    ''')

    cur.execute('''
                    CREATE TABLE IF NOT EXISTS transactions
                    (
                    transaction_code text PRIMARY KEY,
                    block_index integer,
                    timestamp text,
                    type integer,
                    currency text,
                    fee real,
                    description text,
                    valid integer,
                    specific_data text)
                    ''')

    cur.execute('''
                    CREATE TABLE IF NOT EXISTS transfers
                    (transaction_code text,
                    asset1_code integer,
                    asset2_code integer,
                    wallet1 text,
                    wallet2 text,
                    asset1_number real
                    asset2_number real)
                    ''')

    con.commit()
    con.close()


if __name__ == '__main__':
    db_path = '../' + db_path
    clear_db()
    init_db()
