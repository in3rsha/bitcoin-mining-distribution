#!/usr/bin/env python3

"""
Prereqs:

sudo pip3 install python-bitcoinrpc
sudo apt install python3-electrum
"""

import pathlib

from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from electrum import bitcoin, segwit_addr

# Based on Electrum-NMC tests.
def tobtc(inp: str) -> str:
    """Given a Namecoin address or key, converts it to Bitcoin format"""

    # Handle bech32 segwit data first.
    if inp[:3] == "nc1":
        return convert_bech32(inp, "bc")
    if inp[:3] == "tn1":
        return convert_bech32(inp, "tb")

    # Otherwise, try to base58-decode it and then look at the version to
    # determine what it could have been.
    try:
        vch = bitcoin.DecodeBase58Check(inp)
        old_version = vch[0]

        if vch[0] == 52:  # P2PKH address
            new_version = 0
        elif vch[0] == 13:  # P2SH address
            new_version = 5
        else:
            raise AssertionError(f"Unknown Bitcoin base58 version: {old_version}")

        new_vch = bytes([new_version]) + vch[1:]
        outp = bitcoin.EncodeBase58Check(new_vch)

        return outp
    except bitcoin.InvalidChecksum:
        # This is not base58 data, maybe try something else.
        pass

    raise AssertionError(f"Invalid input for format conversion: {inp}")


def convert_bech32(inp: str, new_hrp: str) -> str:
    """Converts a bech32 input to another HRP"""

    _, data = segwit_addr.bech32_decode(inp)
    if data is None:
        raise AssertionError(f"Invalid bech32 for conversion: {inp}")

    return segwit_addr.bech32_encode(new_hrp, data)


rpc_user, rpc_password = "user", "password"

# rpc_user and rpc_password are set in the namecoin.conf file
rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8336"%(rpc_user, rpc_password))

block_count = rpc_connection.getblockcount()

pathlib.Path("./data").mkdir(parents=True, exist_ok=True)

batch_size = 100

min_height = 0
max_height = min_height + batch_size

with open("data/all.csv", "w") as f:

    f.write("height,time,bits,coinbase,address\n")

    while True:
        commands = [ [ "getblockhash", height] for height in range(min_height, max_height) ]
        block_hashes = rpc_connection.batch_(commands)

        blocks = rpc_connection.batch_([ [ "getblock", h ] for h in block_hashes ])

        for block in blocks:
            height = block["height"]
            time = block["time"]
            bits = block["bits"]

            coinbase = ""
            address = ""

            if "auxpow" in block:
                coinbase = block["auxpow"]["tx"]["vin"][0]["coinbase"]
                # P2PK outputs were common long ago, and they don't have an
                # address field.
                if "addresses" in block["auxpow"]["tx"]["vout"][0]["scriptPubKey"]:
                    namecoin_address = block["auxpow"]["tx"]["vout"][0]["scriptPubKey"]["addresses"][0]
                    address = tobtc(namecoin_address)

            f.write("{},{},{},{},{}\n".format(height, time, bits, coinbase, address))

        min_height += batch_size
        max_height += batch_size

        if min_height > block_count:
            break
        max_height = min(block_count, max_height)

