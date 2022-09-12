from substrateinterface import SubstrateInterface
import ssl

try:
    sslopt = {"cert_reqs": ssl.CERT_NONE}
    substrate = SubstrateInterface(
        url="wss://ws.gm.bldnodes.org",
        ws_options={'sslopt': sslopt}
    )
except ConnectionRefusedError:
    print("⚠️ No local Substrate node running, try running 'start_local_substrate_node.sh' first")
    exit()


def extrinsic_sniffer(blockhash):
    burn_list = []
    block_details = substrate.get_block(block_hash=blockhash)
    # start at -1 as extrinsic_id is numbered from 0 upwards:
    # [block-0, block-1, block-2, block-3]
    extrinsic_counter = -1

    for extrinsic in block_details['extrinsics']:
        extrinsic = extrinsic.value
        extrinsic_counter += 1

        # pass over unsigned extrinsics
        if extrinsic['extrinsic_hash'] is None:
            continue

        # Individual calls: Currencies.burn_fren
        if extrinsic['call']['call_function'] == 'burn_fren':
            burn_list.append(f"{extrinsic['address']} burned {extrinsic['call']['call_args'][0]['value'] / 10 ** 12} $FREN")

        # Batch_all calls: Currencies.burn_fren
        if extrinsic['call']['call_function'] == 'batch_all':
            burnAmount = 0
            for batch_calls in extrinsic['call']['call_args']:
                for call in batch_calls['value']:
                    if call['call_function'] == 'burn_fren':
                        burnAmount += call['call_args'][0]['value'] / 10 ** 12
                    else:
                        continue
            burn_list.append(f"{extrinsic['address']} burned {burnAmount} $FREN")
    return burn_list


def new_block(obj, update_nr, subscription_id):
    block = obj['header']['number']
    blockhash = obj['header']['parentHash']

    if blockhash not in previous_hash:
        if len(previous_hash) >= 1:
            previous_hash.pop(len(previous_hash) - 1)
        previous_hash.append(blockhash)

        print(f"Incoming block #{block - 50}")
        print(extrinsic_sniffer(blockhash))
        print("----")
    else:
        pass


if __name__ == '__main__':
    previous_hash = []
    substrate.subscribe_block_headers(new_block)