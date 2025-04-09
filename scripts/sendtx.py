import os
import random
import asyncio
from web3 import Web3
from eth_account import Account
from colorama import init, Fore, Style

# Khởi tạo colorama
init(autoreset=True)

# Constants
NETWORK_URL = "https://testnet-rpc.monad.xyz/"
CHAIN_ID = 10143
EXPLORER_URL = "https://testnet.monadexplorer.com/tx/0x"

# Khởi tạo web3 provider
w3 = Web3(Web3.HTTPProvider(NETWORK_URL))

# Kiểm tra kết nối
if not w3.is_connected():
    raise Exception("Không thể kết nối đến mạng")

# Hàm đọc private key từ pvkey.txt
def load_private_keys(file_path):
    try:
        with open(file_path, 'r') as file:
            keys = [line.strip() for line in file.readlines() if len(line.strip()) in [64, 66]]
            if not keys:
                raise ValueError("Không tìm thấy private key hợp lệ trong file")
            return keys
    except FileNotFoundError:
        print(f"{Fore.RED}❌ Không tìm thấy file pvkey.txt{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.RED}❌ Lỗi đọc file pvkey.txt: {str(e)}{Style.RESET_ALL}")
        return None

# Add this function to get wallet balance
def get_wallet_balance(address):
    try:
        balance = w3.eth.get_balance(address)
        return balance
    except Exception as e:
        print(f"{Fore.RED}❌ Error getting balance: {str(e)}{Style.RESET_ALL}")
        return 0

# Add this function to get percentage input
def get_percentage_from_user(language):
    lang = {
        'vi': "PHẦN TRĂM SỐ DƯ / BALANCE PERCENTAGE",
        'en': "BALANCE PERCENTAGE"
    }
    error = {
        'vi': "Phần trăm phải từ 0.001 đến 100!",
        'en': "Percentage must be between 0.001 and 100!"
    }
    
    while True:
        try:
            print_border(lang[language], Fore.YELLOW)
            percentage_input = input(f"{Fore.GREEN}➤ {'Nhập % số dư (mặc định 0.1%): ' if language == 'vi' else 'Enter % of balance (default 0.1%): '}{Style.RESET_ALL}")
            percentage = float(percentage_input) if percentage_input.strip() else 0.1
            if 0.001 <= percentage <= 100:
                return percentage / 100  # Convert to decimal
            print(f"{Fore.RED}❌ {error[language]}{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}❌ {'Vui lòng nhập số hợp lệ!' if language == 'vi' else 'Please enter a valid number!'}{Style.RESET_ALL}")

# Hàm đọc địa chỉ từ address.txt
def load_addresses(file_path):
    try:
        with open(file_path, 'r') as file:
            addresses = [line.strip() for line in file if line.strip()]
            if not addresses:
                raise ValueError("Không tìm thấy địa chỉ hợp lệ trong file")
            return addresses
    except FileNotFoundError:
        print(f"{Fore.RED}❌ Không tìm thấy file address.txt{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.RED}❌ Lỗi đọc file address.txt: {str(e)}{Style.RESET_ALL}")
        return None

# Hàm hiển thị viền đẹp mắt
def print_border(text, color=Fore.MAGENTA, width=60):
    print(f"{color}╔{'═' * (width - 2)}╗{Style.RESET_ALL}")
    print(f"{color}║ {text:^56} ║{Style.RESET_ALL}")
    print(f"{color}╚{'═' * (width - 2)}╝{Style.RESET_ALL}")

# Hàm hiển thị bước
def print_step(step, message, lang):
    steps = {
        'vi': {'send': 'Gửi Giao Dịch'},
        'en': {'send': 'Send Transaction'}
    }
    step_text = steps[lang][step]
    print(f"{Fore.YELLOW}🔸 {Fore.CYAN}{step_text:<15}{Style.RESET_ALL} | {message}")

# Địa chỉ ngẫu nhiên với checksum
def get_random_address():
    random_address = '0x' + ''.join(random.choices('0123456789abcdef', k=40))
    return w3.to_checksum_address(random_address)

# Hàm gửi giao dịch
# Modify the send_transaction function to calculate amount based on percentage
async def send_transaction(private_key, to_address, percentage, language):
    account = Account.from_key(private_key)
    sender_address = account.address
    lang = {
        'vi': {'send': 'Đang gửi giao dịch...', 'success': 'Giao dịch thành công!', 'failure': 'Giao dịch thất bại'},
        'en': {'send': 'Sending transaction...', 'success': 'Transaction successful!', 'failure': 'Transaction failed'}
    }[language]

    try:
        # Get balance and calculate amount
        balance_wei = w3.eth.get_balance(sender_address)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        
        # Calculate amount to send based on percentage
        amount_wei = int(balance_wei * percentage)
        amount_eth = w3.from_wei(amount_wei, 'ether')
        
        # Make sure we have at least 0.000001 MONAD and enough for gas
        gas_reserve = w3.to_wei(0.0001, 'ether')  # Reserve for gas
        
        if amount_wei < w3.to_wei(0.000001, 'ether'):
            print(f"{Fore.YELLOW}⚠️ {'Số tiền quá nhỏ, sử dụng tối thiểu' if language == 'vi' else 'Amount too small, using minimum'}: 0.000001 MONAD{Style.RESET_ALL}")
            amount_wei = w3.to_wei(0.000001, 'ether')
            amount_eth = 0.000001
        
        if balance_wei < (amount_wei + gas_reserve):
            print(f"{Fore.RED}❌ {'Số dư không đủ' if language == 'vi' else 'Insufficient balance'}: {balance_eth:.6f} MONAD{Style.RESET_ALL}")
            return False
        
        nonce = w3.eth.get_transaction_count(sender_address)
        latest_block = w3.eth.get_block('latest')
        base_fee_per_gas = latest_block['baseFeePerGas']
        max_priority_fee_per_gas = w3.to_wei(2, 'gwei')
        max_fee_per_gas = base_fee_per_gas + max_priority_fee_per_gas

        tx = {
            'nonce': nonce,
            'to': w3.to_checksum_address(to_address),
            'value': amount_wei,
            'gas': 25000,
            'maxFeePerGas': max_fee_per_gas,
            'maxPriorityFeePerGas': max_priority_fee_per_gas,
            'chainId': CHAIN_ID,
        }

        print_step('send', f"{lang['send']} {amount_eth:.6f} MONAD ({percentage*100:.4f}%)", language)
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_link = f"{EXPLORER_URL}{tx_hash.hex()}"
        
        await asyncio.sleep(2)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
        
        if receipt.status == 1:
            print_step('send', f"{Fore.GREEN}✔ {lang['success']} Tx: {tx_link}{Style.RESET_ALL}", language)
            print(f"{Fore.YELLOW}Người gửi / Sender: {sender_address}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Người nhận / Receiver: {to_address}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Số lượng / Amount: {amount_eth:.6f} MONAD ({percentage*100:.4f}%){Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Gas: {receipt['gasUsed']}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Khối / Block: {receipt['blockNumber']}{Style.RESET_ALL}")
            new_balance = w3.from_wei(w3.eth.get_balance(sender_address), 'ether')
            print(f"{Fore.YELLOW}Số dư / Balance: {new_balance:.6f} MONAD{Style.RESET_ALL}")
            return True
        else:
            print_step('send', f"{Fore.RED}✘ {lang['failure']} Tx: {tx_link}{Style.RESET_ALL}", language)
            return False
    except Exception as e:
        print_step('send', f"{Fore.RED}✘ Thất bại / Failed: {str(e)}{Style.RESET_ALL}", language)
        return False

# Gửi giao dịch đến địa chỉ ngẫu nhiên
# Update the functions to use percentage
async def send_to_random_addresses(percentage, tx_count, private_keys, language):
    lang = {
        'vi': {'start': f'Bắt đầu gửi {tx_count} giao dịch ngẫu nhiên ({percentage*100:.4f}% số dư)'},
        'en': {'start': f'Starting {tx_count} random transactions ({percentage*100:.4f}% of balance)'}
    }[language]
    print_border(lang['start'], Fore.CYAN)
    
    count = 0
    for _ in range(tx_count):
        for private_key in private_keys:
            to_address = get_random_address()
            if await send_transaction(private_key, to_address, percentage, language):
                count += 1
            await asyncio.sleep(random.uniform(1, 3))  # Delay ngẫu nhiên 1-3 giây
    
    print(f"{Fore.YELLOW}Tổng giao dịch thành công / Total successful: {count}{Style.RESET_ALL}")
    return count

async def send_to_file_addresses(percentage, addresses, private_keys, language):
    lang = {
        'vi': {'start': f'Bắt đầu gửi giao dịch đến {len(addresses)} địa chỉ từ file ({percentage*100:.4f}% số dư)'},
        'en': {'start': f'Starting transactions to {len(addresses)} addresses from file ({percentage*100:.4f}% of balance)'}
    }[language]
    print_border(lang['start'], Fore.CYAN)
    
    count = 0
    for private_key in private_keys:
        for to_address in addresses:
            if await send_transaction(private_key, to_address, percentage, language):
                count += 1
            await asyncio.sleep(random.uniform(1, 3))  # Delay ngẫu nhiên 1-3 giây
    
    print(f"{Fore.YELLOW}Tổng giao dịch thành công / Total successful: {count}{Style.RESET_ALL}")
    return count

# Hàm chính
# Update the main run function
async def run(language):
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {'SEND TX - MONAD TESTNET':^56} │{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")

    private_keys = load_private_keys('pvkey.txt')
    if not private_keys:
        return

    print(f"{Fore.CYAN}👥 {'Tài khoản' if language == 'vi' else 'Accounts'}: {len(private_keys)}{Style.RESET_ALL}")

    # Get percentage input once
    percentage = get_percentage_from_user(language)

    while True:
        try:
            print_border("🔢 SỐ LƯỢNG GIAO DỊCH / NUMBER OF TRANSACTIONS", Fore.YELLOW)
            tx_count_input = input(f"{Fore.GREEN}➤ {'Nhập số (mặc định 5): ' if language == 'vi' else 'Enter number (default 5): '}{Style.RESET_ALL}")
            tx_count = int(tx_count_input) if tx_count_input.strip() else 5
            if tx_count <= 0:
                raise ValueError
            break
        except ValueError:
            print(f"{Fore.RED}❌ {'Vui lòng nhập số hợp lệ!' if language == 'vi' else 'Please enter a valid number!'}{Style.RESET_ALL}")

    while True:
        print_border("🔧 CHỌN LOẠI GIAO DỊCH / TRANSACTION TYPE", Fore.YELLOW)
        print(f"{Fore.CYAN}1. {'Gửi đến địa chỉ ngẫu nhiên' if language == 'vi' else 'Send to random address'}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}2. {'Gửi đến địa chỉ từ file (address.txt)' if language == 'vi' else 'Send to addresses from file (address.txt)'}{Style.RESET_ALL}")
        choice = input(f"{Fore.GREEN}➤ {'Nhập lựa chọn (1/2): ' if language == 'vi' else 'Enter choice (1/2): '}{Style.RESET_ALL}")

        if choice == '1':
            await send_to_random_addresses(percentage, tx_count, private_keys, language)
            break
        elif choice == '2':
            addresses = load_addresses('address.txt')
            if addresses:
                await send_to_file_addresses(percentage, addresses, private_keys, language)
            break
        else:
            print(f"{Fore.RED}❌ {'Lựa chọn không hợp lệ!' if language == 'vi' else 'Invalid choice!'}{Style.RESET_ALL}")

    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {'HOÀN TẤT' if language == 'vi' else 'ALL DONE'}: {tx_count} {'GIAO DỊCH CHO' if language == 'vi' else 'TRANSACTIONS FOR'} {len(private_keys)} {'TÀI KHOẢN' if language == 'vi' else 'ACCOUNTS'}{' ' * (32 - len(str(tx_count)) - len(str(len(private_keys))))}│{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")

# Chạy chương trình nếu là file chính
if __name__ == "__main__":
    asyncio.run(run('en'))
