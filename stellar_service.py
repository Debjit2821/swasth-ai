import os

from stellar_sdk import (

    Asset,
    Server,

    Keypair,

    TransactionBuilder,

    Network
)

# STELLAR TESTNET SERVER

server = Server(
    "https://horizon-testnet.stellar.org"
)

# LOAD KEYS FROM ENV

secret_key = os.getenv(
    "STELLAR_SECRET_KEY"
)

public_key = os.getenv(
    "STELLAR_PUBLIC_KEY"
)

# CREATE KEYPAIR

keypair = Keypair.from_secret(
    secret_key
)

# STORE HASH ON BLOCKCHAIN

def store_hash(report_hash):

    try:

        # LOAD ACCOUNT

        source_account = (
            server.load_account(
                public_key
            )
        )

        # CREATE TRANSACTION

        transaction = (

            TransactionBuilder(

                source_account=(
                    source_account
                ),

                network_passphrase=(
                    Network
                    .TESTNET_NETWORK_PASSPHRASE
                ),

                base_fee=100
            )

            .append_payment_op(

                destination=public_key,

                amount="0.0000001",

                asset=Asset("XLM")
            )

            .add_text_memo(

                report_hash[:28]
            )

            .build()
        )

        # SIGN TRANSACTION

        transaction.sign(
            keypair
        )

        # SUBMIT

        response = (
            server.submit_transaction(
                transaction
            )
        )

        print(
            "BLOCKCHAIN SUCCESS:",
            response["hash"]
        )

        return response["hash"]

    except Exception as e:

        print(
            "BLOCKCHAIN ERROR:",
            e
        )

        return None