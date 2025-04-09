import os
import random
import asyncio
from web3 import Web3
from web3.exceptions import ContractLogicError
from colorama import init, Fore, Style

# Khởi tạo colorama
init(autoreset=True)

# Constants
RPC_URL = "https://testnet-rpc.monad.xyz/"
EXPLORER_URL = "https://testnet.monadexplorer.com/tx/0x"
KITSU_STAKING_CONTRACT = "0x07AabD925866E8353407E67C1D157836f7Ad923e"

# Hàm đọc nhiều private key từ pvkey.txt
def load_private_keys(file_path):
    try:
        with open(file_path, 'r') as file:
            keys = [line.strip() for line in file.readlines() if line.strip()]
            if not keys:
                raise ValueError("File pvkey.txt rỗng")
            return keys
    except FileNotFoundError:
        print(f"{Fore.RED}❌ Không tìm thấy file pvkey.txt{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.RED}❌ Lỗi đọc file pvkey.txt: {str(e)}{Style.RESET_ALL}")
        return None

# Khởi tạo web3 provider
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Kiểm tra kết nối
if not w3.is_connected():
    print(f"{Fore.RED}❌ Không kết nối được với RPC{Style.RESET_ALL}")
    exit(1)

# ABI cho staking contract
staking_abi = [
    {"name": "stake", "type": "function", "stateMutability": "payable", "inputs": [], "outputs": []},
    {"name": "withdraw", "type": "function", "stateMutability": "nonpayable", "inputs": [{"name": "amount", "type": "uint256"}], "outputs": [{"type": "bool"}]},
    {"name": "withdrawWithSelector", "type": "function", "stateMutability": "nonpayable", "inputs": [{"name": "amount", "type": "uint256"}], "outputs": [{"type": "bool"}], "selector": "0x30af6b2e"}
]

# Khởi tạo contract
contract = w3.eth.contract(address=KITSU_STAKING_CONTRACT, abi=staking_abi)

# Hàm hiển thị viền đẹp mắt
def print_border(text, color=Fore.MAGENTA, width=60):
    print(f"{color}╔{'═' * (width - 2)}╗{Style.RESET_ALL}")
    print(f"{color}║ {text:^56} ║{Style.RESET_ALL}")
    print(f"{color}╚{'═' * (width - 2)}╝{Style.RESET_ALL}")

# Hàm hiển thị bước với giao diện đẹp hơn
def print_step(step, message, lang):
    steps = {
        'vi': {'stake': 'Stake MON', 'unstake': 'Unstake sMON'},
        'en': {'stake': 'Stake MON', 'unstake': 'Unstake sMON'}
    }
    step_text = steps[lang][step]
    print(f"{Fore.YELLOW}🔸 {Fore.CYAN}{step_text:<15}{Style.RESET_ALL} | {message}")

# Tạo số lượng ngẫu nhiên (0.01 - 0.05 MON)
def get_random_amount():
    min_val = 0.01
    max_val = 0.05
    random_amount = random.uniform(min_val, max_val)
    return w3.to_wei(round(random_amount, 4), 'ether')

# Tạo delay ngẫu nhiên (1-3 phút)
def get_random_delay():
    return random.randint(10, 30)  # Trả về giây

# Hàm Stake MON
async def stake_mon(private_key, amount, language, cycle):
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:8] + "..."
        lang = {
            'vi': {
                'start': f"[Vòng {cycle}] Stake {w3.from_wei(amount, 'ether')} MON",
                'send': 'Đang gửi giao dịch stake...',
                'success': 'Stake thành công!'
            },
            'en': {
                'start': f"[Cycle {cycle}] Staking {w3.from_wei(amount, 'ether')} MON",
                'send': 'Sending stake transaction...',
                'success': 'Stake successful!'
            }
        }[language]

        print_border(f"{lang['start']} | {wallet}", Fore.MAGENTA)
        
        balance = w3.eth.get_balance(account.address)
        print_step('stake', f"Số dư: {Fore.CYAN}{w3.from_wei(balance, 'ether')} MON{Style.RESET_ALL}", language)
        if balance < amount:
            raise ValueError(f"Số dư không đủ: {w3.from_wei(balance, 'ether')} MON < {w3.from_wei(amount, 'ether')} MON")

        tx = contract.functions.stake().build_transaction({
            'from': account.address,
            'value': amount,
            'gas': 165000,  # Tăng gas limit lên 600,000
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
        })

        print_step('stake', lang['send'], language)
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print_step('stake', f"Tx Hash: {Fore.YELLOW}{EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}", language)
        await asyncio.sleep(2)  # Tăng thời gian chờ lên 2 giây
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)  # Tăng timeout lên 180 giây
        
        if receipt.status == 1:
            print_step('stake', f"{Fore.GREEN}✔ {lang['success']}{Style.RESET_ALL}", language)
            return amount
        else:
            raise Exception(f"Giao dịch thất bại: Status {receipt.status}, Data: {receipt.get('data', 'N/A')}")

    except ContractLogicError as cle:
        print_step('stake', f"{Fore.RED}✘ Thất bại / Failed: Contract reverted - {str(cle)}{Style.RESET_ALL}", language)
        raise
    except Exception as e:
        print_step('stake', f"{Fore.RED}✘ Thất bại / Failed: {str(e)}{Style.RESET_ALL}", language)
        raise

# Hàm Unstake sMON
async def unstake_mon(private_key, amount, language, cycle):
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:8] + "..."
        lang = {
            'vi': {
                'start': f"[Vòng {cycle}] Unstake {w3.from_wei(amount, 'ether')} sMON",
                'send': 'Đang gửi giao dịch unstake...',
                'success': 'Unstake thành công!'
            },
            'en': {
                'start': f"[Cycle {cycle}] Unstaking {w3.from_wei(amount, 'ether')} sMON",
                'send': 'Sending unstake transaction...',
                'success': 'Unstake successful!'
            }
        }[language]

        print_border(f"{lang['start']} | {wallet}", Fore.MAGENTA)
        
        tx = {
            'to': KITSU_STAKING_CONTRACT,
            'from': account.address,
            'data': "0x30af6b2e" + w3.to_hex(amount)[2:].zfill(64),
            'gas': 200000,  # Tăng gas limit lên 600,000
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
        }

        print_step('unstake', lang['send'], language)
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print_step('unstake', f"Tx Hash: {Fore.YELLOW}{EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}", language)
        await asyncio.sleep(2)  # Tăng thời gian chờ lên 2 giây
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)  # Tăng timeout lên 180 giây
        
        if receipt.status == 1:
            print_step('unstake', f"{Fore.GREEN}✔ {lang['success']}{Style.RESET_ALL}", language)
        else:
            raise Exception(f"Giao dịch thất bại: Status {receipt.status}, Data: {receipt.get('data', 'N/A')}")

    except ContractLogicError as cle:
        print_step('unstake', f"{Fore.RED}✘ Thất bại / Failed: Contract reverted - {str(cle)}{Style.RESET_ALL}", language)
        raise
    except Exception as e:
        print_step('unstake', f"{Fore.RED}✘ Thất bại / Failed: {str(e)}{Style.RESET_ALL}", language)
        raise

# Chạy vòng lặp staking cho từng private key
async def run_staking_cycle(cycles, private_keys, language):
    lang = {
        'vi': "VÒNG LẶP STAKING KITSU / KITSU STAKING CYCLE",
        'en': "KITSU STAKING CYCLE"
    }[language]

    for account_idx, private_key in enumerate(private_keys, 1):
        wallet = w3.eth.account.from_key(private_key).address[:8] + "..."
        print_border(f"🏦 TÀI KHOẢN / ACCOUNT {account_idx}/{len(private_keys)} | {wallet}", Fore.BLUE)

        for i in range(cycles):
            print_border(f"🔄 {lang} {i + 1}/{cycles} | {wallet}", Fore.CYAN)
            amount = get_random_amount()
            try:
                stake_amount = await stake_mon(private_key, amount, language, i + 1)
                delay = get_random_delay()
                print(f"\n{Fore.YELLOW}⏳ {'Đợi' if language == 'vi' else 'Waiting'} {delay / 60:.1f} {'phút trước khi unstake...' if language == 'vi' else 'minutes before unstaking...'}{Style.RESET_ALL}")
                await asyncio.sleep(delay)
                await unstake_mon(private_key, stake_amount, language, i + 1)
            except Exception as e:
                print(f"{Fore.RED}❌ Lỗi trong vòng {i + 1}: {str(e)}{Style.RESET_ALL}")
                continue
            
            if i < cycles - 1:
                delay = get_random_delay()
                print(f"\n{Fore.YELLOW}⏳ {'Đợi' if language == 'vi' else 'Waiting'} {delay / 60:.1f} {'phút trước vòng tiếp theo...' if language == 'vi' else 'minutes before next cycle...'}{Style.RESET_ALL}")
                await asyncio.sleep(delay)

        if account_idx < len(private_keys):
            delay = get_random_delay()
            print(f"\n{Fore.YELLOW}⏳ {'Đợi' if language == 'vi' else 'Waiting'} {delay / 60:.1f} {'phút trước tài khoản tiếp theo...' if language == 'vi' else 'minutes before next account...'}{Style.RESET_ALL}")
            await asyncio.sleep(delay)

    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {'HOÀN TẤT' if language == 'vi' else 'ALL DONE'}: {cycles} {'VÒNG LẶP CHO' if language == 'vi' else 'CYCLES FOR'} {len(private_keys)} {'TÀI KHOẢN' if language == 'vi' else 'ACCOUNTS'}{' ' * (32 - len(str(cycles)) - len(str(len(private_keys))))}│{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")

# Hàm chính
async def run(language):
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {'KITSU STAKING - MONAD TESTNET':^56} │{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")

    private_keys = load_private_keys('pvkey.txt')
    if not private_keys:
        return

    print(f"{Fore.CYAN}👥 {'Tài khoản' if language == 'vi' else 'Accounts'}: {len(private_keys)}{Style.RESET_ALL}")

    while True:
        try:
            print_border("🔢 SỐ VÒNG LẶP / NUMBER OF CYCLES", Fore.YELLOW)
            cycles_input = input(f"{Fore.GREEN}➤ {'Nhập số (mặc định 1): ' if language == 'vi' else 'Enter number (default 1): '}{Style.RESET_ALL}")
            cycles = int(cycles_input) if cycles_input.strip() else 1
            if cycles <= 0:
                raise ValueError
            break
        except ValueError:
            print(f"{Fore.RED}❌ {'Vui lòng nhập số hợp lệ!' if language == 'vi' else 'Please enter a valid number!'}{Style.RESET_ALL}")

    start_msg = f"Chạy {cycles} vòng staking Kitsu cho {len(private_keys)} tài khoản..." if language == 'vi' else f"Running {cycles} Kitsu staking cycles for {len(private_keys)} accounts..."
    print(f"{Fore.YELLOW}🚀 {start_msg}{Style.RESET_ALL}")
    await run_staking_cycle(cycles, private_keys, language)

if __name__ == "__main__":
    asyncio.run(run('en'))
