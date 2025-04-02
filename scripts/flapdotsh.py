import os
import sys
import asyncio
import random
import time
from web3 import Web3
from web3.exceptions import ContractLogicError
from eth_account import Account
from colorama import init, Fore, Style

# Khởi tạo colorama
init(autoreset=True)

# Độ rộng viền
BORDER_WIDTH = 80

# Constants
RPC_URL = "https://testnet-rpc.monad.xyz/"
EXPLORER_URL = "https://testnet.monadexplorer.com/tx/0x"
CHAIN_ID = 10143  # Monad testnet chain ID
SWAP_CONTRACT_ADDRESS = Web3.to_checksum_address("0x4267F317adee7C6478a5EE92985c2BD5D855E274")  # Router
TOKEN_ADDRESS = Web3.to_checksum_address("0x8b9b9f63652be021efbe96d834a631b2a5fb82f7")  # Token muốn mua
DEFAULT_GAS = 300000  # Gas mặc định

# Từ vựng song ngữ
LANG = {
    'vi': {
        'title': 'FLAPSH SWAP - MONAD TESTNET',
        'info': 'Thông tin',
        'found': 'Tìm thấy',
        'wallets': 'ví',
        'processing_wallet': 'XỬ LÝ VÍ',
        'checking_balance': 'Kiểm tra số dư...',
        'insufficient_balance': 'Số dư không đủ',
        'preparing_tx': 'Chuẩn bị giao dịch...',
        'sending_tx': 'Đang gửi giao dịch...',
        'success': 'Mua thành công {amount} MON từ contract!',
        'failure': 'Mua thất bại: {reason}',
        'address': 'Địa chỉ',
        'amount': 'Số lượng',
        'gas': 'Gas',
        'block': 'Khối',
        'balance': 'Số dư',
        'pausing': 'Tạm nghỉ',
        'completed': 'HOÀN THÀNH: {successful}/{total} GIAO DỊCH THÀNH CÔNG',
        'error': 'Lỗi',
        'connect_success': 'Thành công: Đã kết nối mạng Monad Testnet',
        'connect_error': 'Không thể kết nối RPC',
        'web3_error': 'Kết nối Web3 thất bại',
        'pvkey_not_found': 'File pvkey.txt không tồn tại',
        'pvkey_empty': 'Không tìm thấy private key hợp lệ',
        'pvkey_error': 'Đọc pvkey.txt thất bại',
        'invalid_key': 'không hợp lệ, bỏ qua',
        'warning_line': 'Cảnh báo: Dòng',
        'gas_estimation_failed': 'Không thể ước lượng gas',
        'default_gas_used': 'Sử dụng gas mặc định: {gas}',
        'tx_rejected': 'Giao dịch bị từ chối bởi hợp đồng hoặc mạng',
        'amount_prompt': 'Nhập số lượng MON để mua từ contract',
        'invalid_amount': 'Số lượng không hợp lệ hoặc vượt quá số dư',
        'times_prompt': 'Nhập số lần mua',
        'invalid_times': 'Số lần không hợp lệ, vui lòng nhập số nguyên dương',
    },
    'en': {
        'title': 'FLAPSH SWAP - MONAD TESTNET',
        'info': 'Info',
        'found': 'Found',
        'wallets': 'wallets',
        'processing_wallet': 'PROCESSING WALLET',
        'checking_balance': 'Checking balance...',
        'insufficient_balance': 'Insufficient balance',
        'preparing_tx': 'Preparing transaction...',
        'sending_tx': 'Sending transaction...',
        'success': 'Successfully bought {amount} MON from contract!',
        'failure': 'Buy failed: {reason}',
        'address': 'Address',
        'amount': 'Amount',
        'gas': 'Gas',
        'block': 'Block',
        'balance': 'Balance',
        'pausing': 'Pausing',
        'completed': 'COMPLETED: {successful}/{total} TRANSACTIONS SUCCESSFUL',
        'error': 'Error',
        'connect_success': 'Success: Connected to Monad Testnet',
        'connect_error': 'Failed to connect to RPC',
        'web3_error': 'Web3 connection failed',
        'pvkey_not_found': 'pvkey.txt file not found',
        'pvkey_empty': 'No valid private keys found',
        'pvkey_error': 'Failed to read pvkey.txt',
        'invalid_key': 'is invalid, skipped',
        'warning_line': 'Warning: Line',
        'gas_estimation_failed': 'Failed to estimate gas',
        'default_gas_used': 'Using default gas: {gas}',
        'tx_rejected': 'Transaction rejected by contract or network',
        'amount_prompt': 'Enter amount of MON to buy from contract',
        'invalid_amount': 'Invalid amount or exceeds balance',
        'times_prompt': 'Enter number of buys',
        'invalid_times': 'Invalid number, please enter a positive integer',
    }
}

# Hàm hiển thị viền đẹp mắt
def print_border(text: str, color=Fore.CYAN, width=BORDER_WIDTH):
    text = text.strip()
    if len(text) > width - 4:
        text = text[:width - 7] + "..."
    padded_text = f" {text} ".center(width - 2)
    print(f"{color}┌{'─' * (width - 2)}┐{Style.RESET_ALL}")
    print(f"{color}│{padded_text}│{Style.RESET_ALL}")
    print(f"{color}└{'─' * (width - 2)}┘{Style.RESET_ALL}")

# Hàm hiển thị phân cách
def print_separator(color=Fore.MAGENTA):
    print(f"{color}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")

# Hàm kiểm tra private key hợp lệ
def is_valid_private_key(key: str) -> bool:
    key = key.strip()
    if not key.startswith('0x'):
        key = '0x' + key
    try:
        bytes.fromhex(key.replace('0x', ''))
        return len(key) == 66
    except ValueError:
        return False

# Hàm đọc private keys từ file pvkey.txt
def load_private_keys(file_path: str = "pvkey.txt", language: str = 'en') -> list:
    try:
        if not os.path.exists(file_path):
            print(f"{Fore.RED}  ✖ {LANG[language]['pvkey_not_found']}{Style.RESET_ALL}")
            with open(file_path, 'w') as f:
                f.write("# Add private keys here, one per line\n# Example: 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef\n")
            sys.exit(1)
        
        valid_keys = []
        with open(file_path, 'r') as f:
            for i, line in enumerate(f, 1):
                key = line.strip()
                if key and not key.startswith('#'):
                    if is_valid_private_key(key):
                        if not key.startswith('0x'):
                            key = '0x' + key
                        valid_keys.append((i, key))
                    else:
                        print(f"{Fore.YELLOW}  ⚠ {LANG[language]['warning_line']} {i} {LANG[language]['invalid_key']}: {key}{Style.RESET_ALL}")
        
        if not valid_keys:
            print(f"{Fore.RED}  ✖ {LANG[language]['pvkey_empty']}{Style.RESET_ALL}")
            sys.exit(1)
        
        return valid_keys
    except Exception as e:
        print(f"{Fore.RED}  ✖ {LANG[language]['pvkey_error']}: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

# Hàm kết nối Web3
def connect_web3(language: str = 'en'):
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not w3.is_connected():
            print(f"{Fore.RED}  ✖ {LANG[language]['connect_error']}{Style.RESET_ALL}")
            sys.exit(1)
        print(f"{Fore.GREEN}  ✔ {LANG[language]['connect_success']} │ Chain ID: {w3.eth.chain_id}{Style.RESET_ALL}")
        return w3
    except Exception as e:
        print(f"{Fore.RED}  ✖ {LANG[language]['web3_error']}: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

# Hàm kiểm tra số dư MON
def check_balance(w3: Web3, address: str, language: str = 'en') -> float:
    try:
        balance_wei = w3.eth.get_balance(Web3.to_checksum_address(address))
        return float(w3.from_wei(balance_wei, "ether"))
    except Exception as e:
        print(f"{Fore.YELLOW}  ⚠ {LANG[language]['error']}: {str(e)}{Style.RESET_ALL}")
        return -1

# Hàm thực hiện mua từ contract
async def buy_from_contract(w3: Web3, private_key: str, amount: float, swap_times: int, language: str = 'en'):
    account = Account.from_key(private_key)
    sender_address = Web3.to_checksum_address(account.address)
    
    successful_swaps = 0
    nonce = w3.eth.get_transaction_count(sender_address, 'pending')
    
    for i in range(swap_times):
        print_border(f"Buy {i+1}/{swap_times}: {TOKEN_ADDRESS}", Fore.YELLOW)
        print(f"{Fore.CYAN}  > {LANG[language]['checking_balance']}{Style.RESET_ALL}")
        
        balance = check_balance(w3, sender_address, language)
        gas_price = w3.eth.gas_price
        gas_cost_estimate = float(w3.from_wei(gas_price * DEFAULT_GAS, "ether"))
        if balance < amount + gas_cost_estimate:
            print(f"{Fore.RED}  ✖ {LANG[language]['insufficient_balance']}: {balance:.4f} MON < {amount + gas_cost_estimate:.4f}{Style.RESET_ALL}")
            break
        
        amount_wei = w3.to_wei(amount, "ether")
        
        print(f"{Fore.CYAN}  > {LANG[language]['preparing_tx']}{Style.RESET_ALL}")
        # Hàm buy: tokenAddress, recipient, amountOutMin
        function_selector = "0x153e66e6"
        token_param = TOKEN_ADDRESS.replace("0x", "").zfill(64)  # Token muốn mua
        recipient_param = sender_address.replace("0x", "").zfill(64)
        min_amount_param = "0".zfill(64)  # Số lượng tối thiểu token nhận
        
        data = function_selector + token_param + recipient_param + min_amount_param
        
        tx_params = {
            "from": sender_address,
            "to": SWAP_CONTRACT_ADDRESS,  # Router
            "value": amount_wei,  # Số MON gửi
            "gasPrice": int(w3.eth.gas_price * random.uniform(1.03, 1.1)),
            "nonce": nonce,
            "data": data,
            "chainId": CHAIN_ID,
        }
        
        try:
            estimated_gas = w3.eth.estimate_gas(tx_params)
            tx_params['gas'] = int(estimated_gas * 1.2)
        except Exception as e:
            tx_params['gas'] = DEFAULT_GAS
            print(f"{Fore.YELLOW}    {LANG[language]['gas_estimation_failed']}: {str(e)}. {LANG[language]['default_gas_used'].format(gas=DEFAULT_GAS)}{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}  > {LANG[language]['sending_tx']}{Style.RESET_ALL}")
        signed_tx = w3.eth.account.sign_transaction(tx_params, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_link = f"{EXPLORER_URL}{tx_hash.hex()}"
        
        try:
            receipt = await asyncio.get_event_loop().run_in_executor(None, lambda: w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180))
            if receipt.status == 1:
                successful_swaps += 1
                mon_balance = check_balance(w3, sender_address, language)
                print(f"{Fore.GREEN}  ✔ {LANG[language]['success'].format(amount=amount)} │ Tx: {tx_link}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}    {LANG[language]['address']:<12}: {sender_address}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}    {LANG[language]['block']:<12}: {receipt['blockNumber']}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}    {LANG[language]['gas']:<12}: {receipt['gasUsed']}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}    {LANG[language]['balance']:<12}: {mon_balance:.4f} MON{Style.RESET_ALL}")
            else:
                reason = "Transaction reverted"  # Cần ABI để decode revert reason
                print(f"{Fore.RED}  ✖ {LANG[language]['failure'].format(reason=reason)} │ Tx: {tx_link}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}  ✖ {LANG[language]['failure'].format(reason=str(e))} │ Tx: {tx_link}{Style.RESET_ALL}")
            break
        
        nonce += 1
        if i < swap_times - 1:
            delay = random.uniform(5, 15)
            print(f"{Fore.YELLOW}    {LANG[language]['pausing']} {delay:.2f} {'giây' if language == 'vi' else 'seconds'}{Style.RESET_ALL}")
            await asyncio.sleep(delay)
    
    return successful_swaps

# Hàm chính
async def run(language: str = 'en'):
    print()
    print_border(LANG[language]['title'], Fore.CYAN)
    print()

    private_keys = load_private_keys('pvkey.txt', language)
    print(f"{Fore.YELLOW}  ℹ {LANG[language]['info']}: {LANG[language]['found']} {len(private_keys)} {LANG[language]['wallets']}{Style.RESET_ALL}")
    print()

    if not private_keys:
        return

    w3 = connect_web3(language)
    print()

    total_swaps = 0
    successful_swaps = 0

    random.shuffle(private_keys)
    for i, (profile_num, private_key) in enumerate(private_keys, 1):
        print_border(f"{LANG[language]['processing_wallet']} {profile_num} ({i}/{len(private_keys)})", Fore.MAGENTA)
        account = Account.from_key(private_key)
        print(f"{Fore.YELLOW}  {LANG[language]['address']}: {account.address}{Style.RESET_ALL}")
        balance = check_balance(w3, account.address, language)
        print(f"{Fore.YELLOW}  {LANG[language]['balance']}: {balance:.4f} MON{Style.RESET_ALL}")
        print_separator()

        print()
        while True:
            gas_price = w3.eth.gas_price
            gas_cost_estimate = float(w3.from_wei(gas_price * DEFAULT_GAS, "ether"))
            print(f"{Fore.CYAN}{LANG[language]['amount_prompt']} {Fore.YELLOW}(Max: {balance - gas_cost_estimate:.4f} MON):{Style.RESET_ALL}")
            try:
                amount_input = float(input(f"{Fore.GREEN}  > {Style.RESET_ALL}"))
                if amount_input > 0 and amount_input <= balance - gas_cost_estimate:
                    amount = amount_input
                    break
                print(f"{Fore.RED}  ✖ {LANG[language]['invalid_amount']} (bao gồm phí gas ước tính: {gas_cost_estimate:.4f} MON){Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}  ✖ {LANG[language]['invalid_amount']}{Style.RESET_ALL}")

        print()
        while True:
            print(f"{Fore.CYAN}{LANG[language]['times_prompt']}:{Style.RESET_ALL}")
            try:
                swap_times = int(input(f"{Fore.GREEN}  > {Style.RESET_ALL}"))
                if swap_times > 0:
                    break
                print(f"{Fore.RED}  ✖ {LANG[language]['invalid_times']}{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}  ✖ {LANG[language]['invalid_times']}{Style.RESET_ALL}")

        print()
        swaps = await buy_from_contract(w3, private_key, amount, swap_times, language)
        successful_swaps += swaps
        total_swaps += swap_times

        if i < len(private_keys):
            delay = random.uniform(10, 30)
            print(f"{Fore.YELLOW}  ℹ {LANG[language]['pausing']} {delay:.2f} {'giây' if language == 'vi' else 'seconds'}{Style.RESET_ALL}")
            await asyncio.sleep(delay)
        print_separator()
    
    print()
    print_border(f"{LANG[language]['completed'].format(successful=successful_swaps, total=total_swaps)}", Fore.GREEN)
    print()

if __name__ == "__main__":
    asyncio.run(run_flapdotsh('en'))
