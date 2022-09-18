from substrateinterface import SubstrateInterface
from datetime import datetime
import requests
import json
import ssl


class DiscordWebhook:
    def __init__(self, url):
        """
        https://discord.com/developers/docs/resources/webhook#execute-webhook
        :param url:
        """
        self.webhook = url

    def make_request(self, data):
        try:
            response = requests.post(url=self.webhook, json=data)
            response_code = response.status_code

            if response_code == 204:
                return 'Message sent!'
            else:
                raise Exception(f'response  - {response_code}')
        except requests.exceptions.Timeout as timeout:
            raise SystemError(timeout)
        except requests.exceptions.TooManyRedirects as redirects:
            raise SystemError(redirects)
        except requests.exceptions.RequestException as error:
            raise SystemExit(error)

    def send(self, content: str, username: str):
        data = {
            'content': content,
            'username': username
        }
        self.make_request(data=data)

    def embeds(self, description, footer):
        data = {
            'content': '',
            'embeds': [{
                'description': description,
                "color": "	16756224",
                "timestamp": f"{datetime.now()}",
                "thumbnail": {
                    "url": "https://i.imgur.com/DDsE8v9.png"
                },
                "footer": {
                    "text": footer,
                }
            }]
        }
        self.make_request(data=data)


class DiscordAPI:
    def __init__(self, token: str, guild: str):
        """
        https://discord.com/developers/docs/getting-started
        :param token:
        :param guild:
        """
        self.token = token
        self.guild = guild
        self.headers = {'Authorization': f'Bot {self.token}'}
        self.base_url = 'https://discord.com/api'

    def get_user(self, username):
        req_users = requests.get(url=f'{self.base_url}/guilds/{self.guild}/members',
                                 headers=self.headers,
                                 params={"limit": 1000})

        if req_users.status_code == 200:
            for user in req_users.json():
                if username.split('#')[0] == user['user']['username']:
                    return user['user']['id']
            return username

        else:
            raise Exception(f'get_user() failed: {req_users.status_code}')


def current_time_period():
    CurrentTimePeriod = substrate.query(module='Currencies', storage_function='CurrentTimePeriod')
    options = ['Morning', 'Night']
    if CurrentTimePeriod.value in options:
        return True
    else:
        return False


def shortify(address):
    start, end = address[:6], address[-6:]
    return f"{start}...{end}"


def check_identity(address):
    """
    :param address:
    :return: Information that is pertinent to identify the entity behind an account.
    """
    result = substrate.query(
        module='Identity',
        storage_function='IdentityOf',
        params=[address]
    )
    result = result.value

    # return short address if result contains nothing
    if result is None:
        return shortify(address)
    else:
        display = result['info']['display']
        twitter = result['info']['twitter']
        additional = result['info']['additional']

    for info in additional:
        if 'discord' in str(info):
            return f"<@{discord.get_user(username=info[1]['Raw'])}>"

    if 'Raw' in twitter:
        if len(twitter['Raw']) > 0:
            return twitter['Raw']

    if 'Raw' in display:
        if len(display['Raw']) > 0:
            return display['Raw']

    return shortify(address)


def extrinsic_sniffer(blockhash: str, can_mint: bool):
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
            webhook.embeds(description=f"{check_identity(extrinsic['address'])}\n\nburned {extrinsic['call']['call_args'][0]['value'] / 10 ** 12} **$FREN**",
                           footer=f"{extrinsic['call']['call_module']}.{extrinsic['call']['call_function']}")

        # Batch_all calls: Currencies.burn_fren
        if extrinsic['call']['call_function'] == 'batch_all':
            burnAmount = 0
            for batch_calls in extrinsic['call']['call_args']:
                for call in batch_calls['value']:
                    if call['call_function'] == 'burn_fren':
                        burnAmount += call['call_args'][0]['value'] / 10 ** 12
                    else:
                        continue
            webhook.embeds(description=f"{check_identity(extrinsic['address'])}\n\nburned {burnAmount} **$FREN**",
                           footer=f"{extrinsic['call']['call_module']}.{extrinsic['call']['call_function']}")


def new_block(obj, update_nr, subscription_id):
    block = obj['header']['number']
    blockhash = obj['header']['parentHash']
    if blockhash not in previous_hash:
        if len(previous_hash) >= 1:
            previous_hash.pop(len(previous_hash) - 1)
        previous_hash.append(blockhash)

        print(f"Incoming block #{block}")
        extrinsic_sniffer(blockhash=blockhash, can_mint=current_time_period())
    else:
        pass


if __name__ == '__main__':
    previous_hash = []

    try:
        sslopt = {"cert_reqs": ssl.CERT_NONE}
        substrate = SubstrateInterface(
            url="wss://ws.gm.bldnodes.org",
            ws_options={'sslopt': sslopt}
        )
    except ConnectionRefusedError:
        print("⚠️ No local Substrate node running, try running 'start_local_substrate_node.sh' first")
        exit()

    discord = DiscordAPI(token='', guild='')
    webhook = DiscordWebhook( url='')
    substrate.subscribe_block_headers(new_block)
