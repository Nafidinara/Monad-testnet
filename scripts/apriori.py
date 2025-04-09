import os
from web3 import Web3
from colorama import init, Fore, Style
import random
import asyncio
import aiohttp

# Initialize colorama for colored console output
init()

# Constants
RPC_URL = "https://testnet-rpc.monad.xyz/"
EXPLORER_URL = "https://testnet.monadexplorer.com/tx/0x"
provider = Web3.HTTPProvider(RPC_URL)
w3 = Web3(provider)

contract_address = Web3.to_checksum_address("0xb2f82D0f38dc453D596Ad40A37799446Cc89274A")
gas_limit_stake = 150000
gas_limit_unstake = 160000
gas_limit_claim = 150000

# Minimal ABI
minimal_abi = [
    {
        "constant": True,
        "inputs": [{"name": "", "type": "address"}],
        "name": "getPendingUnstakeRequests",
        "outputs": [{"name": "", "type": "uint256[]"}],
        "type": "function"
    }
]

contract = w3.eth.contract(address=contract_address, abi=minimal_abi)

def get_random_amount():
    min_val = 0.01
    max_val = 0.05
    random_amount = random.uniform(min_val, max_val)
    return w3.to_wei(round(random_amount, 4), 'ether')

def get_random_delay():
    min_delay = 0.2 * 60 * 1000  # 1 minute in ms
    max_delay = 0.3 * 60 * 1000  # 3 minutes in ms
    return random.randint(min_delay, max_delay) / 1000

async def delay(ms):
    await asyncio.sleep(ms / 1000)

# Hàm hiển thị đường viền đẹp
def print_border(text, color=Fore.CYAN, width=60):
    print(f"{color}┌{'─' * (width - 2)}┐{Style.RESET_ALL}")
    print(f"{color}│ {text:<{width-4}} │{Style.RESET_ALL}")
    print(f"{color}└{'─' * (width - 2)}┘{Style.RESET_ALL}")

# Hàm hiển thị thông tin bước
def print_step(step, message, lang):
    messages = {
        'vi': {
            'stake': 'Stake MON',
            'unstake': 'Yêu cầu Unstake',
            'claim': 'Claim MON',
        },
        'en': {
            'stake': 'Stake MON',
            'unstake': 'Request Unstake',
            'claim': 'Claim MON',
        }
    }
    step_text = messages[lang][step]
    print(f"{Fore.YELLOW}➤ {Fore.CYAN}{step_text:<15}{Style.RESET_ALL} | {message}")

async def stake_mon(account, private_key, cycle_number, language):
    try:
        lang = {
            'vi': {
                'prep': f"Chuẩn bị stake MON - Cycle {cycle_number}",
                'amount': 'Số tiền stake',
                'sending': 'Đang gửi giao dịch...',
                'waiting': 'Đang chờ xác nhận...',
                'success': 'Stake thành công!',
                'fail': 'Stake thất bại'
            },
            'en': {
                'prep': f"Preparing to stake MON - Cycle {cycle_number}",
                'amount': 'Stake Amount',
                'sending': 'Sending transaction...',
                'waiting': 'Waiting for confirmation...',
                'success': 'Stake Successful!',
                'fail': 'Staking Failed'
            }
        }[language]

        print_border(f"{lang['prep']} | Tài khoản: {account.address[:8]}...")
        print_step('stake', f"{lang['amount']}: {Fore.GREEN}{w3.from_wei(get_random_amount(), 'ether')} MON{Style.RESET_ALL}", language)

        stake_amount = get_random_amount()
        function_selector = '0x6e553f65'
        data = Web3.to_bytes(hexstr=function_selector) + \
               w3.to_bytes(stake_amount).rjust(32, b'\0') + \
               w3.to_bytes(hexstr=account.address).rjust(32, b'\0')

        gas_price = w3.eth.gas_price
        tx = {
            'to': contract_address,
            'data': data,
            'gas': gas_limit_stake,
            'gasPrice': gas_price,
            'value': stake_amount,
            'nonce': w3.eth.get_transaction_count(account.address),
            'chainId': w3.eth.chain_id
        }

        print_step('stake', lang['sending'], language)
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print_step('stake', f"Tx: {Fore.YELLOW}{EXPLORER_URL}{w3.to_hex(tx_hash)}{Style.RESET_ALL}", language)
        print_step('stake', lang['waiting'], language)
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print_step('stake', f"{Fore.GREEN}{lang['success']}{Style.RESET_ALL}", language)

        return {'receipt': receipt, 'stake_amount': stake_amount}

    except Exception as e:
        print_step('stake', f"{Fore.RED}{lang['fail']}: {str(e)}{Style.RESET_ALL}", language)
        raise

async def request_unstake_apr_mon(account, private_key, amount_to_unstake, cycle_number, language):
    try:
        lang = {
            'vi': {
                'prep': f"Yêu cầu unstake - Cycle {cycle_number}",
                'amount': 'Số tiền unstake',
                'sending': 'Đang gửi yêu cầu...',
                'waiting': 'Đang chờ xác nhận...',
                'success': 'Yêu cầu unstake thành công!',
                'fail': 'Yêu cầu unstake thất bại'
            },
            'en': {
                'prep': f"Requesting unstake - Cycle {cycle_number}",
                'amount': 'Unstake Amount',
                'sending': 'Sending request...',
                'waiting': 'Waiting for confirmation...',
                'success': 'Unstake Request Successful!',
                'fail': 'Unstake Request Failed'
            }
        }[language]

        print_border(f"{lang['prep']} | Tài khoản: {account.address[:8]}...")
        print_step('unstake', f"{lang['amount']}: {Fore.GREEN}{w3.from_wei(amount_to_unstake, 'ether')} aprMON{Style.RESET_ALL}", language)

        function_selector = '0x7d41c86e'
        data = Web3.to_bytes(hexstr=function_selector) + \
               w3.to_bytes(amount_to_unstake).rjust(32, b'\0') + \
               w3.to_bytes(hexstr=account.address).rjust(32, b'\0') + \
               w3.to_bytes(hexstr=account.address).rjust(32, b'\0')

        gas_price = w3.eth.gas_price
        tx = {
            'to': contract_address,
            'data': data,
            'gas': gas_limit_unstake,
            'gasPrice': gas_price,
            'value': 0,
            'nonce': w3.eth.get_transaction_count(account.address),
            'chainId': w3.eth.chain_id
        }

        print_step('unstake', lang['sending'], language)
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print_step('unstake', f"Tx: {Fore.YELLOW}{EXPLORER_URL}{w3.to_hex(tx_hash)}{Style.RESET_ALL}", language)
        print_step('unstake', lang['waiting'], language)
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print_step('unstake', f"{Fore.GREEN}{lang['success']}{Style.RESET_ALL}", language)

        return receipt

    except Exception as e:
        print_step('unstake', f"{Fore.RED}{lang['fail']}: {str(e)}{Style.RESET_ALL}", language)
        raise

async def check_claimable_status(wallet_address, language):
    try:
        async with aiohttp.ClientSession() as session:
            api_url = f"https://liquid-staking-backend-prod-b332fbe9ccfe.herokuapp.com/withdrawal_requests?address={wallet_address}"
            async with session.get(api_url) as response:
                data = await response.json()

        claimable_request = next((r for r in data if not r['claimed'] and r['is_claimable']), None)
        
        if claimable_request:
            msg = 'Tìm thấy ID' if language == 'vi' else 'Found ID'
            print_step('claim', f"{msg}: {Fore.GREEN}{claimable_request['id']}{Style.RESET_ALL}", language)
            return {'id': claimable_request['id'], 'is_claimable': True}
        
        msg = 'Không có yêu cầu nào để claim' if language == 'vi' else 'No claimable requests'
        print_step('claim', msg, language)
        return {'id': None, 'is_claimable': False}

    except Exception as e:
        msg = 'Kiểm tra thất bại' if language == 'vi' else 'Check Failed'
        print_step('claim', f"{Fore.RED}{msg}: {str(e)}{Style.RESET_ALL}", language)
        return {'id': None, 'is_claimable': False}

async def claim_mon(account, private_key, cycle_number, language):
    try:
        lang = {
            'vi': {
                'prep': f"Kiểm tra claim - Cycle {cycle_number}",
                'prep_claim': 'Chuẩn bị claim ID',
                'sending': 'Đang gửi giao dịch...',
                'waiting': 'Đang chờ xác nhận...',
                'success': 'Claim thành công!',
                'fail': 'Claim thất bại'
            },
            'en': {
                'prep': f"Checking claim - Cycle {cycle_number}",
                'prep_claim': 'Preparing to claim ID',
                'sending': 'Sending transaction...',
                'waiting': 'Waiting for confirmation...',
                'success': 'Claim Successful!',
                'fail': 'Claim Failed'
            }
        }[language]

        print_border(f"{lang['prep']} | Tài khoản: {account.address[:8]}...")
        status = await check_claimable_status(account.address, language)
        
        if not status['is_claimable'] or not status['id']:
            return None

        print_step('claim', f"{lang['prep_claim']}: {Fore.GREEN}{status['id']}{Style.RESET_ALL}", language)

        function_selector = '0x492e47d2'
        data = Web3.to_bytes(hexstr=function_selector) + \
               Web3.to_bytes(hexstr='0x40').rjust(32, b'\0') + \
               w3.to_bytes(hexstr=account.address).rjust(32, b'\0') + \
               w3.to_bytes(1).rjust(32, b'\0') + \
               w3.to_bytes(int(status['id'])).rjust(32, b'\0')

        gas_price = w3.eth.gas_price
        tx = {
            'to': contract_address,
            'data': data,
            'gas': gas_limit_claim,
            'gasPrice': gas_price,
            'value': 0,
            'nonce': w3.eth.get_transaction_count(account.address),
            'chainId': w3.eth.chain_id
        }

        print_step('claim', lang['sending'], language)
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print_step('claim', f"Tx: {Fore.YELLOW}{EXPLORER_URL}{w3.to_hex(tx_hash)}{Style.RESET_ALL}", language)
        print_step('claim', lang['waiting'], language)
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print_step('claim', f"{Fore.GREEN}{lang['success']} ID: {status['id']}{Style.RESET_ALL}", language)

        return receipt

    except Exception as e:
        print_step('claim', f"{Fore.RED}{lang['fail']}: {str(e)}{Style.RESET_ALL}", language)
        raise

async def run_cycle(account, private_key, cycle_number, language):
    try:
        msg = f"BẮT ĐẦU CYCLE {cycle_number} | Tài khoản: {account.address[:8]}..." if language == 'vi' else f"STARTING CYCLE {cycle_number} | Account: {account.address[:8]}..."
        print(f"{Fore.CYAN}{'═' * 60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}│ {msg:<56} │{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'═' * 60}{Style.RESET_ALL}")
        
        result = await stake_mon(account, private_key, cycle_number, language)
        stake_amount = result['stake_amount']

        delay_time = get_random_delay()
        wait_msg = f"Đợi {delay_time} giây trước khi unstake..." if language == 'vi' else f"Waiting {delay_time} seconds before unstake..."
        print(f"\n{Fore.YELLOW}⏳ {wait_msg}{Style.RESET_ALL}")
        await delay(delay_time * 1000)

        await request_unstake_apr_mon(account, private_key, stake_amount, cycle_number, language)

        wait_msg = "Đợi 660 giây (11 phút) trước khi claim..." if language == 'vi' else "Waiting 660 seconds (11 minutes) before claim..."
        print(f"\n{Fore.YELLOW}⏳ {wait_msg}{Style.RESET_ALL}")
        await delay(660000)

        await claim_mon(account, private_key, cycle_number, language)

        success_msg = f"CYCLE {cycle_number} HOÀN THÀNH" if language == 'vi' else f"CYCLE {cycle_number} COMPLETED"
        print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}│ {success_msg:<56} │{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")

    except Exception as e:
        fail_msg = f"CYCLE {cycle_number} THẤT BẠI" if language == 'vi' else f"CYCLE {cycle_number} FAILED"
        print(f"{Fore.RED}{'═' * 60}{Style.RESET_ALL}")
        print(f"{Fore.RED}│ {fail_msg}: {str(e):<45} │{Style.RESET_ALL}")
        print(f"{Fore.RED}{'═' * 60}{Style.RESET_ALL}")
        raise

async def get_cycle_count(language):
    while True:
        try:
            msg = "Bạn muốn chạy bao nhiêu cycle?" if language == 'vi' else "How many cycles to run?"
            print_border(msg, Fore.YELLOW)
            answer = input(f"{Fore.GREEN}➤ Nhập số: {Style.RESET_ALL}")
            cycle_count = int(answer)
            if cycle_count <= 0:
                raise ValueError
            return cycle_count
        except ValueError:
            print(f"{Fore.RED}❌ Vui lòng nhập số nguyên dương!{Style.RESET_ALL}")

async def run(language):
    try:
        print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}│ {'STAKING APRIORI - MONAD TESTNET':^56} │{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")

        # Đọc private keys
        try:
            with open('pvkey.txt', 'r') as file:
                PRIVATE_KEYS = [line.strip() for line in file.readlines() if line.strip()]
            if not PRIVATE_KEYS:
                raise ValueError("Không có key nào trong pvkey.txt")
            ACCOUNTS = [w3.eth.account.from_key(pk) for pk in PRIVATE_KEYS]
        except FileNotFoundError:
            print(f"{Fore.RED}❌ {'Không tìm thấy pvkey.txt' if language == 'vi' else 'pvkey.txt not found'}{Style.RESET_ALL}")
            return
        except Exception as e:
            print(f"{Fore.RED}❌ {'Lỗi đọc key' if language == 'vi' else 'Error reading keys'}: {str(e)}{Style.RESET_ALL}")
            return

        print(f"{Fore.CYAN}👥 {'Tài khoản' if language == 'vi' else 'Accounts'}: {len(ACCOUNTS)}{Style.RESET_ALL}")
        
        cycle_count = await get_cycle_count(language)
        print(f"\n{Fore.YELLOW}🚀 {'Chạy' if language == 'vi' else 'Running'} {cycle_count} {'cycle cho' if language == 'vi' else 'cycles for'} {len(ACCOUNTS)} {'tài khoản' if language == 'vi' else 'accounts'}{Style.RESET_ALL}\n")

        for account_idx, (account, private_key) in enumerate(zip(ACCOUNTS, PRIVATE_KEYS), 1):
            print_border(f"XỬ LÝ TÀI KHOẢN {account_idx}/{len(ACCOUNTS)} | {account.address[:8]}...", Fore.CYAN)
            
            for i in range(1, cycle_count + 1):
                await run_cycle(account, private_key, i, language)

                if i < cycle_count:
                    delay_time = get_random_delay()
                    print(f"\n{Fore.YELLOW}⏳ {'Đợi' if language == 'vi' else 'Waiting'} {delay_time} {'giây trước cycle tiếp theo...' if language == 'vi' else 'seconds before next cycle...'}{Style.RESET_ALL}")
                    await delay(delay_time * 1000)

            print(f"\n{Fore.GREEN}✔ {'Hoàn thành' if language == 'vi' else 'Completed'} {account.address[:8]}...{Style.RESET_ALL}")

            if account_idx < len(ACCOUNTS):
                delay_time = get_random_delay()
                print(f"\n{Fore.YELLOW}⏳ {'Đợi' if language == 'vi' else 'Waiting'} {delay_time} {'giây trước tài khoản tiếp theo...' if language == 'vi' else 'seconds before next account...'}{Style.RESET_ALL}")
                await delay(delay_time * 1000)

        print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}│ {'HOÀN TẤT' if language == 'vi' else 'ALL DONE'}: {cycle_count} {'CYCLE' if language == 'vi' else 'CYCLES'} {'THÀNH CÔNG' if language == 'vi' else 'COMPLETED'}{'^' * (56 - len(str(cycle_count)) - 16)}│{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}{'═' * 60}{Style.RESET_ALL}")
        print(f"{Fore.RED}│ {'LỖI' if language == 'vi' else 'ERROR'}: {str(e):<52} │{Style.RESET_ALL}")
        print(f"{Fore.RED}{'═' * 60}{Style.RESET_ALL}")

if __name__ == "__main__":
    asyncio.run(run('en'))  # Chạy độc lập mặc định bằng tiếng Việt
