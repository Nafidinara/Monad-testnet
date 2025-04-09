import os
import random
import time
from colorama import init, Fore, Style
from web3 import Web3

# Khởi tạo colorama
init(autoreset=True)

# Constants
RPC_URL = "https://testnet-rpc.monad.xyz/"
EXPLORER_URL = "https://testnet.monadexplorer.com/tx/0x"
WMON_CONTRACT = "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701"

# Hàm hiển thị viền đẹp
def print_border(text, color=Fore.CYAN, width=60):
    print(f"{color}┌{'─' * (width - 2)}┐{Style.RESET_ALL}")
    print(f"{color}│ {text:^19} │{Style.RESET_ALL}")
    print(f"{color}└{'─' * (width - 2)}┘{Style.RESET_ALL}")

# Hàm hiển thị bước
def print_step(step, message, lang):
    steps = {
        'vi': {'wrap': 'Wrap MON', 'unwrap': 'Unwrap WMON'},
        'en': {'wrap': 'Wrap MON', 'unwrap': 'Unwrap WMON'}
    }
    step_text = steps[lang][step]
    print(f"{Fore.YELLOW}➤ {Fore.CYAN}{step_text:<15}{Style.RESET_ALL} | {message}")

def get_wallet_balance(address):
    try:
        balance = w3.eth.get_balance(address)
        return balance
    except Exception as e:
        print(f"{Fore.RED}❌ Error getting balance: {str(e)}{Style.RESET_ALL}")
        return 0

# Load private keys từ prkeys.txt
def load_private_keys(file_path):
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"{Fore.RED}❌ Lỗi đọc file: {str(e)}{Style.RESET_ALL}")
        return None

# Khởi tạo web3 provider
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Smart contract ABI
contract_abi = [
    {"constant": False, "inputs": [], "name": "deposit", "outputs": [], "payable": True, "stateMutability": "payable", "type": "function"},
    {"constant": False, "inputs": [{"name": "amount", "type": "uint256"}], "name": "withdraw", "outputs": [], "payable": False, "stateMutability": "nonpayable", "type": "function"},
]

# Khởi tạo contract
contract = w3.eth.contract(address=WMON_CONTRACT, abi=contract_abi)

# Nhập số lượng MON từ người dùng
def get_percentage_from_user(language):
    lang = {
        'vi': "Nhập phần trăm số dư để swap (1-100): ",
        'en': "Enter percentage of balance to swap (1-100): "
    }
    error = {
        'vi': "Phần trăm phải từ 1 đến 100 / Nhập lại số hợp lệ!",
        'en': "Percentage must be 1-100 / Enter a valid number!"
    }
    while True:
        try:
            print_border(lang[language], Fore.YELLOW)
            percentage = float(input(f"{Fore.GREEN}➤ {Style.RESET_ALL}"))
            if 1 <= percentage <= 100:
                return percentage / 100  # Convert to decimal
            print(f"{Fore.RED}❌ {error[language]}{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}❌ {error[language]}{Style.RESET_ALL}")

# Thời gian delay ngẫu nhiên (60-180 giây)
def get_random_delay():
    return random.randint(10, 30)

# Wrap MON thành WMON
def wrap_mon(private_key, amount, language):
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:8] + "..."
        lang = {
            'vi': {
                'start': f"Wrap {w3.from_wei(amount, 'ether')} MON → WMON | {wallet}",
                'send': 'Đang gửi giao dịch...',
                'success': 'Wrap thành công!'
            },
            'en': {
                'start': f"Wrap {w3.from_wei(amount, 'ether')} MON → WMON | {wallet}",
                'send': 'Sending transaction...',
                'success': 'Wrap successful!'
            }
        }[language]

        print_border(lang['start'])
        tx = contract.functions.deposit().build_transaction({
            'from': account.address,
            'value': amount,
            'gas': 200000,
            'gasPrice': w3.to_wei('60', 'gwei'),
            'nonce': w3.eth.get_transaction_count(account.address),
        })

        print_step('wrap', lang['send'], language)
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print_step('wrap', f"Tx: {Fore.YELLOW}{EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}", language)
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print_step('wrap', f"{Fore.GREEN}{lang['success']}{Style.RESET_ALL}", language)

    except Exception as e:
        print_step('wrap', f"{Fore.RED}Thất bại / Failed: {str(e)}{Style.RESET_ALL}", language)
        raise

# Unwrap WMON về MON
def unwrap_mon(private_key, amount, language):
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:8] + "..."
        lang = {
            'vi': {
                'start': f" unwrap {w3.from_wei(amount, 'ether')} WMON → MON | {wallet}",
                'send': 'Đang gửi giao dịch...',
                'success': 'Unwrap thành công!'
            },
            'en': {
                'start': f"Unwrap {w3.from_wei(amount, 'ether')} WMON → MON | {wallet}",
                'send': 'Sending transaction...',
                'success': 'Unwrap successful!'
            }
        }[language]

        print_border(lang['start'])
        tx = contract.functions.withdraw(amount).build_transaction({
            'from': account.address,
            'gas': 200000,
            'gasPrice': w3.to_wei('50', 'gwei'),
            'nonce': w3.eth.get_transaction_count(account.address),
        })

        print_step('unwrap', lang['send'], language)
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print_step('unwrap', f"Tx: {Fore.YELLOW}{EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}", language)
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print_step('unwrap', f"{Fore.GREEN}{lang['success']}{Style.RESET_ALL}", language)

    except Exception as e:
        print_step('unwrap', f"{Fore.RED}Thất bại / Failed: {str(e)}{Style.RESET_ALL}", language)
        raise

# Chạy vòng lặp swap
# Modify run_swap_cycle to use percentage
def run_swap_cycle(cycles, private_keys, percentage, language):
    for cycle in range(1, cycles + 1):
        for pk in private_keys:
            account = w3.eth.account.from_key(pk)
            wallet = account.address[:8] + "..."
            
            # Get wallet balance and calculate amount based on percentage
            balance = get_wallet_balance(account.address)
            # Leave some for gas
            amount = int(balance * percentage * 0.95)  # 95% of the percentage to leave room for gas
            
            if amount <= 0:
                print(f"{Fore.RED}❌ {'Số dư không đủ' if language == 'vi' else 'Insufficient balance'}: {wallet}{Style.RESET_ALL}")
                continue
                
            msg = f"CYCLE {cycle}/{cycles} | Tài khoản / Account: {wallet}"
            print(f"{Fore.CYAN}{'═' * 60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}│ {msg:^56} │{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'═' * 60}{Style.RESET_ALL}")
            
            print_step('wrap', f"{'Số dư' if language == 'vi' else 'Balance'}: {Fore.GREEN}{w3.from_wei(balance, 'ether')} MON{Style.RESET_ALL}", language)
            print_step('wrap', f"{'Số tiền swap' if language == 'vi' else 'Swap amount'}: {Fore.GREEN}{w3.from_wei(amount, 'ether')} MON ({percentage*100}%){Style.RESET_ALL}", language)

            wrap_mon(pk, amount, language)
            unwrap_mon(pk, amount, language)

            if cycle < cycles or pk != private_keys[-1]:
                delay = get_random_delay()
                wait_msg = f"Đợi {delay} giây..." if language == 'vi' else f"Waiting {delay} seconds..."
                print(f"\n{Fore.YELLOW}⏳ {wait_msg}{Style.RESET_ALL}")
                time.sleep(delay)

# Hàm chính tương thích với main.py
# Update the run function
def run(language):
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {'BEBOP SWAP - MONAD TESTNET':^56} │{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")

    # Load private keys
    private_keys = load_private_keys('pvkey.txt')
    if not private_keys:
        print(f"{Fore.RED}❌ Không tìm thấy pvkey.txt / pvkey.txt not found{Style.RESET_ALL}")
        return

    print(f"{Fore.CYAN}👥 {'Tài khoản' if language == 'vi' else 'Accounts'}: {len(private_keys)}{Style.RESET_ALL}")

    # Get percentage input once
    percentage = get_percentage_from_user(language)
    
    # Nhập số cycle
    while True:
        try:
            print_border("SỐ VÒNG LẶP / NUMBER OF CYCLES", Fore.YELLOW)
            cycles = input(f"{Fore.GREEN}➤ {'Nhập số (mặc định 1): ' if language == 'vi' else 'Enter number (default 1): '}{Style.RESET_ALL}")
            cycles = int(cycles) if cycles else 1
            if cycles > 0:
                break
            print(f"{Fore.RED}❌ Số phải lớn hơn 0 / Number must be > 0{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}❌ Nhập số hợp lệ / Enter a valid number{Style.RESET_ALL}")

    # Chạy script with percentage
    start_msg = f"Chạy {cycles} vòng hoán đổi với {percentage*100}% số dư..." if language == 'vi' else f"Running {cycles} swap cycles with {percentage*100}% of balance..."
    print(f"{Fore.YELLOW}🚀 {start_msg}{Style.RESET_ALL}")
    run_swap_cycle(cycles, private_keys, percentage, language)

    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {'HOÀN TẤT / ALL DONE':^19} │{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")

if __name__ == "__main__":
    run('en')  # Chạy độc lập với ngôn ngữ mặc định là Tiếng Việt
