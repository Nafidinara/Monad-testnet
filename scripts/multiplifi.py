import os
import sys
import asyncio
import random
import time
from web3 import Web3
from web3.exceptions import TransactionNotFound
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
USDC_CONTRACT_ADDRESS = Web3.to_checksum_address("0x924F1Bf31b19a7f9695F3FC6c69C2BA668Ea4a0a")
USDT_CONTRACT_ADDRESS = Web3.to_checksum_address("0x9eBcD0Ab11D930964F8aD66425758E65c53A7DF1")
STAKING_CONTRACT_ADDRESS = Web3.to_checksum_address("0xBCF1415BD456eDb3a94c9d416F9298ECF9a2cDd0")
FAUCET_CONTRACT_ADDRESS = Web3.to_checksum_address("0x181579497d5c4EfEC2424A21095907ED7d91ac9A")
DEFAULT_GAS = 300000

# Từ vựng song ngữ
LANG = {
    'vi': {
        'title': 'MULTIPLIFI STAKING - MONAD TESTNET',
        'info': 'Thông tin',
        'found': 'Tìm thấy',
        'wallets': 'ví',
        'processing_wallet': 'XỬ LÝ VÍ',
        'checking_balance': 'Kiểm tra số dư...',
        'insufficient_balance': 'Số dư không đủ',
        'preparing_tx': 'Chuẩn bị giao dịch...',
        'sending_tx': 'Đang gửi giao dịch...',
        'success_faucet': 'Nhận token {token} thành công!',
        'success_approve': 'Phê duyệt {token} thành công!',
        'success_deposit': 'Stake {amount} {token} thành công!',
        'failure': 'Thất bại: {reason}',
        'address': 'Địa chỉ',
        'amount': 'Số lượng',
        'gas': 'Gas',
        'block': 'Khối',
        'balance': 'Số dư',
        'usdc_balance': 'Số dư USDC',
        'usdt_balance': 'Số dư USDT',
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
        'choice_prompt': 'Chọn hành động [1: Faucet USDC | 2: Faucet USDT | 3: Stake USDC | 4: Stake USDT]:',
        'invalid_choice': 'Lựa chọn không hợp lệ',
        'auto_selected': 'Đã chọn tự động',
        'already_fauceted': 'Ví này đã faucet rồi! Vui lòng không thực hiện lại.',
    },
    'en': {
        'title': 'MULTIPLIFI STAKING - MONAD TESTNET',
        'auto_selected': 'Auto-selected',
        'info': 'Info',
        'found': 'Found',
        'wallets': 'wallets',
        'processing_wallet': 'PROCESSING WALLET',
        'checking_balance': 'Checking balance...',
        'insufficient_balance': 'Insufficient balance',
        'preparing_tx': 'Preparing transaction...',
        'sending_tx': 'Sending transaction...',
        'success_faucet': 'Successfully claimed {token} tokens!',
        'success_approve': 'Successfully approved {token}!',
        'success_deposit': 'Successfully staked {amount} {token}!',
        'failure': 'Failed: {reason}',
        'address': 'Address',
        'amount': 'Amount',
        'gas': 'Gas',
        'block': 'Block',
        'balance': 'Balance',
        'usdc_balance': 'USDC Balance',
        'usdt_balance': 'USDT Balance',
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
        'choice_prompt': 'Choose action [1: Faucet USDC | 2: Faucet USDT | 3: Stake USDC | 4: Stake USDT]:',
        'invalid_choice': 'Invalid choice',
        'already_fauceted': 'This wallet has already fauceted! Please do not repeat.',
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

# Hàm kiểm tra số dư token (USDC/USDT)
def check_token_balance(w3: Web3, address: str, token_address: str, decimals: int = 6, language: str = 'en') -> tuple:
    try:
        erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function",
            }
        ]
        contract = w3.eth.contract(address=token_address, abi=erc20_abi)
        balance_wei = contract.functions.balanceOf(address).call()
        balance = float(w3.from_wei(balance_wei, 'mwei'))  # 6 decimals
        return balance_wei, balance
    except Exception as e:
        print(f"{Fore.YELLOW}  ⚠ {LANG[language]['error']}: {str(e)}{Style.RESET_ALL}")
        return 0, 0

def get_auto_action(w3, address, language):
    # Cek balance token
    usdc_balance_wei, usdc_balance = check_token_balance(w3, address, USDC_CONTRACT_ADDRESS, language=language)
    usdt_balance_wei, usdt_balance = check_token_balance(w3, address, USDT_CONTRACT_ADDRESS, language=language)

    available_actions = []
    
    # Jika balance token sangat rendah, prioritaskan faucet
    if usdc_balance < 0.1:
        available_actions.append(1)  # Faucet USDC
    if usdt_balance < 0.1:
        available_actions.append(2)  # Faucet USDT
    
    # Jika ada balance, pertimbangkan untuk stake
    if usdc_balance > 0:
        available_actions.append(3)  # Stake USDC
    if usdt_balance > 0:
        available_actions.append(4)  # Stake USDT
    
    # Jika tidak ada action yang tersedia (sangat jarang terjadi), default ke faucet
    if not available_actions:
        available_actions = [1, 2]
    
    # Pilih acak dari action yang tersedia
    action = random.choice(available_actions)
    
    action_names = {
        1: "Faucet USDC",
        2: "Faucet USDT",
        3: f"Stake {usdc_balance:.4f} USDC",
        4: f"Stake {usdt_balance:.4f} USDT"
    }
    
    return action, action_names[action]

# Hàm thực hiện faucet
async def faucet(w3: Web3, private_key: str, token_type: str, language: str = 'en'):
    try:
        account = Account.from_key(private_key)
        sender_address = Web3.to_checksum_address(account.address)
        
        token_name = "USDC" if token_type == "USDC" else "USDT"
        
        print_border(f"Faucet {token_name}: {FAUCET_CONTRACT_ADDRESS}", Fore.YELLOW)
        print(f"{Fore.CYAN}  > {LANG[language]['preparing_tx']}{Style.RESET_ALL}")
        
        payload = ("0x32f289cf000000000000000000000000924f1bf31b19a7f9695f3fc6c69c2ba668ea4a0a" if token_type == "USDC" else
                  "0x32f289cf0000000000000000000000009ebcd0ab11d930964f8ad66425758e65c53a7df1")
        nonce = w3.eth.get_transaction_count(sender_address, 'pending')
        
        tx_params = {
            "from": sender_address,
            "to": FAUCET_CONTRACT_ADDRESS,
            "value": 0,
            "gasPrice": int(w3.eth.gas_price * random.uniform(1.03, 1.1)),
            "nonce": nonce,
            "data": payload,
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
                print(f"{Fore.GREEN}  ✔ {LANG[language]['success_faucet'].format(token=token_name)} │ Tx: {tx_link}{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}  ✖ {LANG[language]['already_fauceted']} │ Tx: {tx_link}{Style.RESET_ALL}")
                return False
        except Exception as e:
            print(f"{Fore.RED}  ✖ {LANG[language]['failure'].format(reason=str(e))} │ Tx: {tx_link}{Style.RESET_ALL}")
            return False
    except Exception as general_error:
        print(f"{Fore.RED}  ✖ {LANG[language]['error']}: {str(general_error)}{Style.RESET_ALL}")
        return False


# Hàm stake token (USDC hoặc USDT)
async def stake_token(w3: Web3, private_key: str, token_type: str, language: str = 'en'):
    try:
        account = Account.from_key(private_key)
        sender_address = Web3.to_checksum_address(account.address)
        
        token_address = USDC_CONTRACT_ADDRESS if token_type == "USDC" else USDT_CONTRACT_ADDRESS
        token_name = "USDC" if token_type == "USDC" else "USDT"
        
        # Kiểm tra số dư token
        print_border(f"Stake {token_name}: {token_address}", Fore.YELLOW)
        print(f"{Fore.CYAN}  > {LANG[language]['checking_balance']}{Style.RESET_ALL}")
        balance_wei, balance = check_token_balance(w3, sender_address, token_address, language=language)
        if balance == 0:
            print(f"{Fore.RED}  ✖ {LANG[language]['insufficient_balance']}: 0 {token_name}{Style.RESET_ALL}")
            return False
        print(f"{Fore.YELLOW}    {LANG[language][f'{token_name.lower()}_balance']}: {balance:.6f} {token_name}{Style.RESET_ALL}")
        
        # Step 1: Approve
        print(f"{Fore.CYAN}  > {LANG[language]['preparing_tx']} (Approve){Style.RESET_ALL}")
        approve_payload = "0x095ea7b3000000000000000000000000bcf1415bd456edb3a94c9d416f9298ecf9a2cdd0ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        nonce = w3.eth.get_transaction_count(sender_address, 'pending')
        
        tx_params = {
            "from": sender_address,
            "to": token_address,
            "value": 0,
            "gasPrice": int(w3.eth.gas_price * random.uniform(1.03, 1.1)),
            "nonce": nonce,
            "data": approve_payload,
            "chainId": CHAIN_ID,
        }
        
        try:
            estimated_gas = w3.eth.estimate_gas(tx_params)
            tx_params['gas'] = int(estimated_gas * 1.2)
        except Exception as e:
            tx_params['gas'] = DEFAULT_GAS
            print(f"{Fore.YELLOW}    {LANG[language]['gas_estimation_failed']}: {str(e)}. {LANG[language]['default_gas_used'].format(gas=DEFAULT_GAS)}{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}  > {LANG[language]['sending_tx']} (Approve){Style.RESET_ALL}")
        signed_tx = w3.eth.account.sign_transaction(tx_params, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_link = f"{EXPLORER_URL}{tx_hash.hex()}"
        
        try:
            receipt = await asyncio.get_event_loop().run_in_executor(None, lambda: w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180))
            if receipt.status != 1:
                print(f"{Fore.RED}  ✖ {LANG[language]['failure'].format(reason='Approve failed')} │ Tx: {tx_link}{Style.RESET_ALL}")
                return False
            print(f"{Fore.GREEN}  ✔ {LANG[language]['success_approve'].format(token=token_name)} │ Tx: {tx_link}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}  ✖ {LANG[language]['failure'].format(reason=str(e))} │ Tx: {tx_link}{Style.RESET_ALL}")
            return False
        
        # Tạm nghỉ trước khi deposit
        delay = random.uniform(5, 15)
        print(f"{Fore.YELLOW}    {LANG[language]['pausing']} {delay:.2f} {'giây' if language == 'vi' else 'seconds'}{Style.RESET_ALL}")
        await asyncio.sleep(delay)
        
        # Step 2: Deposit
        try:
            print(f"{Fore.CYAN}  > {LANG[language]['preparing_tx']} (Deposit){Style.RESET_ALL}")
            amount_hex = hex(int(balance_wei))[2:].zfill(64)
            deposit_payload = (f"0x47e7ef24000000000000000000000000{token_address[2:].lower()}{amount_hex}" if token_type == "USDC" else
                            f"0x47e7ef240000000000000000000000009ebcd0ab11d930964f8ad66425758e65c53a7df1{amount_hex}")
            
            tx_params = {
                "from": sender_address,
                "to": STAKING_CONTRACT_ADDRESS,
                "value": 0,
                "gasPrice": int(w3.eth.gas_price * random.uniform(1.03, 1.1)),
                "nonce": nonce + 1,
                "data": deposit_payload,
                "chainId": CHAIN_ID,
            }
            
            try:
                estimated_gas = w3.eth.estimate_gas(tx_params)
                tx_params['gas'] = int(estimated_gas * 1.2)
            except Exception as e:
                tx_params['gas'] = DEFAULT_GAS
                print(f"{Fore.YELLOW}    {LANG[language]['gas_estimation_failed']}: {str(e)}. {LANG[language]['default_gas_used'].format(gas=DEFAULT_GAS)}{Style.RESET_ALL}")
            
            print(f"{Fore.CYAN}  > {LANG[language]['sending_tx']} (Deposit){Style.RESET_ALL}")
            signed_tx = w3.eth.account.sign_transaction(tx_params, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_link = f"{EXPLORER_URL}{tx_hash.hex()}"
            
            try:
                receipt = await asyncio.get_event_loop().run_in_executor(None, lambda: w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180))
                if receipt.status == 1:
                    print(f"{Fore.GREEN}  ✔ {LANG[language]['success_deposit'].format(amount=balance, token=token_name)} │ Tx: {tx_link}{Style.RESET_ALL}")
                    return True
                else:
                    print(f"{Fore.RED}  ✖ {LANG[language]['failure'].format(reason='Deposit failed')} │ Tx: {tx_link}{Style.RESET_ALL}")
                    return False
            except Exception as e:
                print(f"{Fore.RED}  ✖ {LANG[language]['failure'].format(reason=str(e))} │ Tx: {tx_link}{Style.RESET_ALL}")
                return False
        except Exception as deposit_error:
            print(f"{Fore.RED}  ✖ {LANG[language]['failure'].format(reason=f'Deposit error: {str(deposit_error)}')}{Style.RESET_ALL}")
            return False
    except Exception as general_error:
        print(f"{Fore.RED}  ✖ {LANG[language]['error']}: {str(general_error)}{Style.RESET_ALL}")
        return False

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

    total_actions = 0
    successful_actions = 0

    random.shuffle(private_keys)
    for i, (profile_num, private_key) in enumerate(private_keys, 1):
        try:
            print_border(f"{LANG[language]['processing_wallet']} {profile_num} ({i}/{len(private_keys)})", Fore.MAGENTA)
            account = Account.from_key(private_key)
            print(f"{Fore.YELLOW}  {LANG[language]['address']}: {account.address}{Style.RESET_ALL}")
            
            # Tampilkan saldo
            _, usdc_balance = check_token_balance(w3, account.address, USDC_CONTRACT_ADDRESS, language=language)
            _, usdt_balance = check_token_balance(w3, account.address, USDT_CONTRACT_ADDRESS, language=language)
            print(f"{Fore.YELLOW}  USDC {LANG[language]['balance']}: {usdc_balance:.6f}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}  USDT {LANG[language]['balance']}: {usdt_balance:.6f}{Style.RESET_ALL}")
            print_separator()

            # Otomatis memilih action
            action, action_name = get_auto_action(w3, account.address, language)
            print(f"{Fore.CYAN}  Auto-selected: {action_name}{Style.RESET_ALL}")
            print()

            total_actions += 1
            if action == 1:
                if await faucet(w3, private_key, "USDC", language):
                    successful_actions += 1
            elif action == 2:
                if await faucet(w3, private_key, "USDT", language):
                    successful_actions += 1
            elif action == 3:
                if await stake_token(w3, private_key, "USDC", language):
                    successful_actions += 1
            elif action == 4:
                if await stake_token(w3, private_key, "USDT", language):
                    successful_actions += 1

        except Exception as wallet_error:
            print_border(f"Wallet error: {str(wallet_error)}", Fore.RED)
            continue  # Lanjut ke wallet berikutnya
            
        if i < len(private_keys):
            delay = random.uniform(10, 30)
            print(f"{Fore.YELLOW}  ℹ {LANG[language]['pausing']} {delay:.2f} {'giây' if language == 'vi' else 'seconds'}{Style.RESET_ALL}")
            await asyncio.sleep(delay)
        print_separator()
    
    print()
    print_border(f"{LANG[language]['completed'].format(successful=successful_actions, total=total_actions)}", Fore.GREEN)
    print()

if __name__ == "__main__":
    asyncio.run(run('en'))
