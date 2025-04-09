import os
import sys
import asyncio
import random
import time
from web3 import Web3
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

# Địa chỉ hợp đồng
ROUTER_CONTRACT = Web3.to_checksum_address("0x64Aff7245EbdAAECAf266852139c67E4D8DBa4de")
WMON_CONTRACT = Web3.to_checksum_address("0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701")
USDC_CONTRACT = Web3.to_checksum_address("0xf817257fed379853cde0fa4f97ab987181b1e5ea")
USDT_CONTRACT = Web3.to_checksum_address("0x88b8E2161DEDC77EF4ab7585569D2415a1C1055D")
WETH_CONTRACT = Web3.to_checksum_address("0xB5a30b0FDc5EA94A52fDc42e3E9760Cb8449Fb37")
WSOL_CONTRACT = Web3.to_checksum_address("0x5387C85A4965769f6B0Df430638a1388493486F1")
WBTC_CONTRACT = Web3.to_checksum_address("0xcf5a6076cfa32686c0Df13aBaDa2b40dec133F1d")
MAD_CONTRACT = Web3.to_checksum_address("0xC8527e96c3CB9522f6E35e95C0A28feAb8144f15")

# ABI cho các hợp đồng
ABI = {
    "router": [
        {
            "type": "function",
            "name": "swapExactETHForTokens",
            "inputs": [
                {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                {"internalType": "address[]", "name": "path", "type": "address[]"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"},
            ],
            "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
            "stateMutability": "payable",
        },
        {
            "type": "function",
            "name": "swapExactTokensForETH",
            "inputs": [
                {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                {"internalType": "address[]", "name": "path", "type": "address[]"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"},
            ],
            "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
            "stateMutability": "nonpayable",
        },
        {
            "type": "function",
            "name": "swapExactTokensForTokens",
            "inputs": [
                {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                {"internalType": "address[]", "name": "path", "type": "address[]"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"},
            ],
            "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
            "stateMutability": "nonpayable",
        },
        {
            "type": "function",
            "name": "getAmountsOut",
            "inputs": [
                {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                {"internalType": "address[]", "name": "path", "type": "address[]"},
            ],
            "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
            "stateMutability": "view",
        },
    ],
    "token": [
        {
            "type": "function",
            "name": "approve",
            "inputs": [
                {"name": "guy", "type": "address"},
                {"name": "wad", "type": "uint256"},
            ],
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
        },
        {
            "type": "function",
            "name": "balanceOf",
            "inputs": [{"name": "", "type": "address"}],
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
        },
        {
            "type": "function",
            "name": "decimals",
            "inputs": [],
            "outputs": [{"name": "", "type": "uint8"}],
            "stateMutability": "view",
        },
        {
            "type": "function",
            "name": "allowance",
            "inputs": [
                {"name": "", "type": "address"},
                {"name": "", "type": "address"},
            ],
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
        },
    ],
    "weth": [
        {
            "type": "function",
            "name": "deposit",
            "inputs": [],
            "outputs": [],
            "stateMutability": "payable",
        },
        {
            "type": "function",
            "name": "withdraw",
            "inputs": [{"name": "wad", "type": "uint256"}],
            "outputs": [],
            "stateMutability": "nonpayable",
        },
    ],
}

# Token khả dụng
AVAILABLE_TOKENS = {
    "MON": {"name": "MON", "address": None, "decimals": 18, "native": True},
    "WMON": {"name": "WMON", "address": WMON_CONTRACT, "decimals": 18, "native": False},
    "USDC": {"name": "USDC", "address": USDC_CONTRACT, "decimals": 6, "native": False},
    "USDT": {"name": "USDT", "address": USDT_CONTRACT, "decimals": 6, "native": False},
    "WETH": {"name": "WETH", "address": WETH_CONTRACT, "decimals": 18, "native": False},
    "WSOL": {"name": "WSOL", "address": WSOL_CONTRACT, "decimals": 18, "native": False},
    "WBTC": {"name": "WBTC", "address": WBTC_CONTRACT, "decimals": 8, "native": False},
    "MAD": {"name": "MAD", "address": MAD_CONTRACT, "decimals": 18, "native": False},
}

# Danh sách token chính để chọn
TOKEN_LIST = ["MON", "WMON", "USDC", "USDT", "WETH", "WSOL", "WBTC", "MAD"]

# Từ vựng song ngữ
LANG = {
    'vi': {
        'title': 'MADNESS SWAP - MONAD TESTNET',
        'info': 'Thông tin',
        'found': 'Tìm thấy',
        'wallets': 'ví',
        'processing_wallet': 'XỬ LÝ VÍ',
        'checking_balance': 'Kiểm tra số dư...',
        'insufficient_balance': 'Số dư không đủ',
        'preparing_tx': 'Chuẩn bị giao dịch...',
        'sending_tx': 'Đang gửi giao dịch...',
        'success': 'Swap {amount} {from_token} -> {expected_out} {to_token} thành công!',
        'failure': 'Swap thất bại',
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
        'approving': 'Đang phê duyệt {token}...',
        'approve_success': 'Phê duyệt {token} thành công!',
        'approve_failure': 'Phê duyệt {token} thất bại',
        'select_swap': 'Chọn token để swap từ [1-8]',
        'invalid_choice': 'Lựa chọn không hợp lệ, vui lòng chọn từ 1-{max}',
        'amount_prompt': 'Nhập số lượng {token} để swap',
        'invalid_amount': 'Số lượng không hợp lệ hoặc vượt quá số dư',
        'times_prompt': 'Nhập số lần swap',
        'invalid_times': 'Số lần không hợp lệ, vui lòng nhập số nguyên dương',
        'available_tokens': 'Token khả dụng',
        'swap_pairs': 'Cặp swap cho {token}',
        'select_pair': 'Chọn cặp swap [1-{max}]',
        'auto_selected': 'Đã chọn tự động',
        'no_balance': 'Không đủ số dư cho bất kỳ token nào',
    },
    'en': {
        'title': 'MADNESS SWAP - MONAD TESTNET',
        'info': 'Info',
        'found': 'Found',
        'wallets': 'wallets',
        'processing_wallet': 'PROCESSING WALLET',
        'checking_balance': 'Checking balance...',
        'insufficient_balance': 'Insufficient balance',
        'preparing_tx': 'Preparing transaction...',
        'sending_tx': 'Sending transaction...',
        'success': 'Successfully swapped {amount} {from_token} -> {expected_out} {to_token}!',
        'failure': 'Swap failed',
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
        'approving': 'Approving {token}...',
        'approve_success': 'Successfully approved {token}!',
        'approve_failure': 'Approval of {token} failed',
        'select_swap': 'Select token to swap from [1-8]',
        'invalid_choice': 'Invalid choice, please select from 1-{max}',
        'amount_prompt': 'Enter amount of {token} to swap',
        'invalid_amount': 'Invalid amount or exceeds balance',
        'times_prompt': 'Enter number of swaps',
        'invalid_times': 'Invalid number, please enter a positive integer',
        'available_tokens': 'Available Tokens',
        'swap_pairs': '{token} Swap Pairs',
        'select_pair': 'Select swap pair [1-{max}]',
        'auto_selected': 'Auto-selected',
        'no_balance': 'No sufficient balance for any token',
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

def select_random_swap_pair(w3, address, language):
    # Acak urutan token_list
    available_pairs = []
    
    # Pertama cek MON balance, ini paling penting
    mon_token = AVAILABLE_TOKENS["MON"]
    mon_balance = check_token_balance(w3, address, mon_token, language)
    
    # Cek token lain
    for from_token in TOKEN_LIST:
        from_token_data = AVAILABLE_TOKENS[from_token]
        from_balance = check_token_balance(w3, address, from_token_data, language)
        
        # Set minimal balance yang lebih masuk akal berdasarkan token
        min_balance = 0.01
        if from_token in ["USDC", "USDT"]:
            min_balance = 0.5  # Minimal 0.5 USDC/USDT
        elif from_token == "MON":
            min_balance = 0.05  # Minimal 0.05 MON
        elif from_token == "WBTC":
            min_balance = 0.0001  # WBTC memiliki nilai lebih tinggi
        
        if from_balance > min_balance:
            to_tokens = [t for t in TOKEN_LIST if t != from_token]
            
            # Hindari MON -> WMON dan WMON -> MON
            if from_token == "MON":
                to_tokens = [t for t in to_tokens if t != "WMON"]
            elif from_token == "WMON":
                to_tokens = [t for t in to_tokens if t != "MON"]
            
            # Jika tidak ada tujuan yang valid setelah filter, lewati
            if not to_tokens:
                continue
                
            # Prioritaskan pasangan dengan MON jika ada balance MON
            if from_token != "MON" and from_token != "WMON" and mon_balance > 0.05:
                to_tokens = ["MON"] + [t for t in to_tokens if t != "MON"]
            
            for to_token in to_tokens:
                # Tambahkan pasangan ke daftar dengan bobot berdasarkan saldo
                # Hindari pasangan MON-WMON
                if not (from_token == "MON" and to_token == "WMON") and not (from_token == "WMON" and to_token == "MON"):
                    weight = from_balance * 10 if from_token == "MON" or to_token == "MON" else from_balance
                    available_pairs.append((from_token, to_token, from_balance, weight))
    
    if not available_pairs:
        return None, None, 0
    
    # Urutkan berdasarkan weight dan pilih pasangan teratas
    available_pairs.sort(key=lambda x: x[3], reverse=True)
    
    # 70% chance ambil pasangan terbaik, 30% chance ambil random
    if random.random() < 0.7 and len(available_pairs) > 0:
        from_token, to_token, max_balance, _ = available_pairs[0]
    else:
        # Pilih secara acak tapi dengan mempertimbangkan weight
        total_weight = sum(pair[3] for pair in available_pairs)
        r = random.uniform(0, total_weight)
        cumulative_weight = 0
        from_token, to_token, max_balance, _ = available_pairs[0]  # Default jika loop tidak break
        for ft, tt, mb, weight in available_pairs:
            cumulative_weight += weight
            if cumulative_weight >= r:
                from_token, to_token, max_balance = ft, tt, mb
                break
    
    # Tentukan jumlah swap (30-80% dari saldo)
    swap_amount = max_balance * random.uniform(0.1, 0.2)
    
    # Pastikan jumlah tidak terlalu kecil
    min_amount = 0.001 if from_token == "MON" else 0.1
    if from_token == "WBTC":
        min_amount = 0.00001  # WBTC memiliki nilai lebih tinggi
    
    swap_amount = max(min_amount, min(swap_amount, max_balance * 0.95))
    
    # Round ke 4 desimal
    swap_amount = round(swap_amount, 4)
    
    return from_token, to_token, swap_amount

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

# Hàm kiểm tra số dư token
def check_token_balance(w3: Web3, address: str, token: dict, language: str = 'en') -> float:
    address = Web3.to_checksum_address(address)
    if token["native"]:
        try:
            balance_wei = w3.eth.get_balance(address)
            return float(w3.from_wei(balance_wei, "ether"))
        except Exception as e:
            print(f"{Fore.YELLOW}  ⚠ {LANG[language]['error']}: {str(e)}{Style.RESET_ALL}")
            return -1
    else:
        token_abi = ABI["token"]
        contract = w3.eth.contract(address=token['address'], abi=token_abi)
        try:
            balance = contract.functions.balanceOf(address).call()
            return balance / (10 ** token['decimals'])
        except Exception as e:
            print(f"{Fore.YELLOW}  ⚠ {LANG[language]['error']}: {str(e)}{Style.RESET_ALL}")
            return -1

# Hàm hiển thị số dư token
def display_token_balances(w3: Web3, address: str, language: str = 'en'):
    print_border(f"{LANG[language]['balance']}", Fore.CYAN)
    for symbol, token_data in AVAILABLE_TOKENS.items():
        balance = check_token_balance(w3, address, token_data, language)
        print(f"{Fore.YELLOW}  - {symbol:<6}: {balance:.6f}{Style.RESET_ALL}")

# Hàm hiển thị danh sách token khả dụng
def display_available_tokens(language: str = 'en'):
    print_border(f"{LANG[language]['select_swap']}", Fore.CYAN)
    print(f"{Fore.YELLOW}  {LANG[language]['available_tokens']}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}  {'-' * 16}{Style.RESET_ALL}")
    for idx, token in enumerate(TOKEN_LIST, 1):
        targets = " | ".join(t for t in TOKEN_LIST if t != token)
        print(f"{Fore.YELLOW}  {idx}. {token} ↔ {targets}{Style.RESET_ALL}")

# Hàm hiển thị cặp swap cho token đã chọn
def display_swap_pairs(from_token: str, language: str = 'en'):
    print_border(f"{LANG[language]['swap_pairs'].format(token=from_token)}", Fore.CYAN)
    print(f"{Fore.YELLOW}  {'-' * 12}{Style.RESET_ALL}")
    swap_pairs = [t for t in TOKEN_LIST if t != from_token]
    for idx, to_token in enumerate(swap_pairs, 1):
        print(f"{Fore.YELLOW}  {idx}. {from_token} → {to_token}{Style.RESET_ALL}")
    return swap_pairs

# Hàm phê duyệt token
async def approve_token(w3: Web3, private_key: str, token: dict, amount_wei: int, language: str = 'en') -> bool:
    account = Account.from_key(private_key)
    sender_address = Web3.to_checksum_address(account.address)
    token_abi = ABI["token"]
    contract = w3.eth.contract(address=token['address'], abi=token_abi)
    
    try:
        # Periksa allowance terlebih dahulu
        current_allowance = contract.functions.allowance(sender_address, ROUTER_CONTRACT).call()
        if current_allowance >= amount_wei:
            print(f"{Fore.GREEN}  ✔ {token['name']} already approved with {current_allowance/(10**token['decimals']):.4f} allowance{Style.RESET_ALL}")
            return True
        
        print(f"{Fore.CYAN}  > {LANG[language]['approving'].format(token=token['name'])}{Style.RESET_ALL}")
        nonce = w3.eth.get_transaction_count(sender_address)
        max_uint256 = 2**256 - 1  # Nilai maksimal untuk approval
        
        tx_params = contract.functions.approve(ROUTER_CONTRACT, max_uint256).build_transaction({
            'nonce': nonce,
            'from': sender_address,
            'chainId': CHAIN_ID,
            'gasPrice': int(w3.eth.gas_price * random.uniform(1.03, 1.1))
        })
        
        try:
            estimated_gas = w3.eth.estimate_gas(tx_params)
            tx_params['gas'] = int(estimated_gas * 1.2)
        except:
            tx_params['gas'] = 190000
            print(f"{Fore.YELLOW}    {LANG[language]['gas_estimation_failed']}. {LANG[language]['default_gas_used'].format(gas=190000)}{Style.RESET_ALL}")
        
        signed_tx = w3.eth.account.sign_transaction(tx_params, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_link = f"{EXPLORER_URL}{tx_hash.hex()}"
        
        try:
            receipt = await asyncio.get_event_loop().run_in_executor(None, lambda: w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180))
            
            if receipt.status == 1:
                print(f"{Fore.GREEN}  ✔ {LANG[language]['approve_success'].format(token=token['name'])} │ Tx: {tx_link}{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}  ✖ {LANG[language]['approve_failure'].format(token=token['name'])} │ Tx: {tx_link}{Style.RESET_ALL}")
                return False
        except Exception as receipt_error:
            print(f"{Fore.RED}  ✖ Failed to get receipt: {str(receipt_error)}{Style.RESET_ALL}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}  ✖ {LANG[language]['approve_failure'].format(token=token['name'])}: {str(e)}{Style.RESET_ALL}")
        return False

# Hàm thực hiện swap
async def swap_token(w3: Web3, private_key: str, wallet_index: int, from_token: str, to_token: str, amount: float, swap_times: int, language: str = 'en'):
    account = Account.from_key(private_key)
    sender_address = Web3.to_checksum_address(account.address)
    
    token_a = AVAILABLE_TOKENS.get(from_token)
    token_b = AVAILABLE_TOKENS.get(to_token)
    
    if not token_a or not token_b:
        print(f"{Fore.RED}  ✖ {LANG[language]['error']}: Invalid token symbols{Style.RESET_ALL}")
        return 0
    
    successful_swaps = 0
    
    for i in range(swap_times):
        try:
            print_border(f"Swap {i+1}/{swap_times}: {from_token} -> {to_token}", Fore.YELLOW)
            print(f"{Fore.CYAN}  > {LANG[language]['checking_balance']}{Style.RESET_ALL}")
            
            balance = check_token_balance(w3, sender_address, token_a, language)
            if balance < amount:
                print(f"{Fore.RED}  ✖ {LANG[language]['insufficient_balance']}: {balance:.4f} {token_a['name']} < {amount}{Style.RESET_ALL}")
                break
            
            amount_wei = int(amount * (10 ** token_a['decimals'])) if not token_a['native'] else w3.to_wei(amount, 'ether')
            
            if not token_a['native']:
                approval_success = await approve_token(w3, private_key, token_a, amount_wei, language)
                if not approval_success:
                    print(f"{Fore.RED}  ✖ Approval failed, skipping this swap{Style.RESET_ALL}")
                    continue  # Skip this swap but continue with the next one
            
            # Get updated nonce for each transaction
            nonce = w3.eth.get_transaction_count(sender_address, 'pending')
            
            print(f"{Fore.CYAN}  > {LANG[language]['preparing_tx']}{Style.RESET_ALL}")
            router_contract = w3.eth.contract(address=ROUTER_CONTRACT, abi=ABI['router'])
            
            path = [
                WMON_CONTRACT if token_a["native"] else token_a["address"],
                WMON_CONTRACT if token_b["native"] else token_b["address"],
            ]
            
            try:
                amounts_out = router_contract.functions.getAmountsOut(amount_wei, path).call()
                expected_out = amounts_out[-1]
                # Increase slippage tolerance to 10%
                min_amount_out = int(expected_out * 0.9)  
                deadline = int(time.time()) + 3600
            except Exception as e:
                print(f"{Fore.RED}  ✖ Failed to get amounts out: {str(e)}{Style.RESET_ALL}")
                continue  # Skip this swap
            
            try:
                if token_a['native']:
                    tx_func = router_contract.functions.swapExactETHForTokens(min_amount_out, path, sender_address, deadline)
                    tx_params = tx_func.build_transaction({
                        'nonce': nonce,
                        'from': sender_address,
                        'value': amount_wei,
                        'chainId': CHAIN_ID,
                        'gasPrice': int(w3.eth.gas_price * random.uniform(1.03, 1.1))
                    })
                elif token_b['native']:
                    tx_func = router_contract.functions.swapExactTokensForETH(amount_wei, min_amount_out, path, sender_address, deadline)
                    tx_params = tx_func.build_transaction({
                        'nonce': nonce,
                        'from': sender_address,
                        'chainId': CHAIN_ID,
                        'gasPrice': int(w3.eth.gas_price * random.uniform(1.03, 1.1))
                    })
                else:
                    tx_func = router_contract.functions.swapExactTokensForTokens(amount_wei, min_amount_out, path, sender_address, deadline)
                    tx_params = tx_func.build_transaction({
                        'nonce': nonce,
                        'from': sender_address,
                        'chainId': CHAIN_ID,
                        'gasPrice': int(w3.eth.gas_price * random.uniform(1.03, 1.1))
                    })
                
                try:
                    estimated_gas = w3.eth.estimate_gas(tx_params)
                    tx_params['gas'] = int(estimated_gas * 1.2)
                except Exception as gas_error:
                    tx_params['gas'] = 250000  # Increased default gas
                    print(f"{Fore.YELLOW}    {LANG[language]['gas_estimation_failed']}. {LANG[language]['default_gas_used'].format(gas=250000)}{Style.RESET_ALL}")
                
                print(f"{Fore.CYAN}  > {LANG[language]['sending_tx']}{Style.RESET_ALL}")
                signed_tx = w3.eth.account.sign_transaction(tx_params, private_key)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                tx_link = f"{EXPLORER_URL}{tx_hash.hex()}"
                
                try:
                    receipt = await asyncio.get_event_loop().run_in_executor(
                        None, 
                        lambda: w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
                    )
                    
                    if receipt.status == 1:
                        successful_swaps += 1
                        mon_balance = check_token_balance(w3, sender_address, AVAILABLE_TOKENS['MON'], language)
                        print(f"{Fore.GREEN}  ✔ {LANG[language]['success'].format(amount=amount, from_token=token_a['name'], expected_out=expected_out/(10**token_b['decimals']), to_token=token_b['name'])} │ Tx: {tx_link}{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}    {LANG[language]['address']:<12}: {sender_address}{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}    {LANG[language]['block']:<12}: {receipt['blockNumber']}{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}    {LANG[language]['gas']:<12}: {receipt['gasUsed']}{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}    {LANG[language]['balance']:<12}: {mon_balance:.4f} MON{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}  ✖ {LANG[language]['failure']} │ Tx: {tx_link}{Style.RESET_ALL}")
                except Exception as receipt_error:
                    print(f"{Fore.RED}  ✖ Failed to get receipt: {str(receipt_error)} │ Tx: {tx_link}{Style.RESET_ALL}")
                    
            except Exception as tx_error:
                print(f"{Fore.RED}  ✖ Transaction error: {str(tx_error)}{Style.RESET_ALL}")
                continue  # Skip to next swap
                
            if i < swap_times - 1:
                delay = random.uniform(5, 15)
                print(f"{Fore.YELLOW}    {LANG[language]['pausing']} {delay:.2f} {'giây' if language == 'vi' else 'seconds'}{Style.RESET_ALL}")
                await asyncio.sleep(delay)
                
        except Exception as general_error:
            print_border(f"{LANG[language]['error']}: {str(general_error)}", Fore.RED)
            continue  # Skip this swap but continue with the next one
    
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
        try:
            print_border(f"{LANG[language]['processing_wallet']} {profile_num} ({i}/{len(private_keys)})", Fore.MAGENTA)
            account = Account.from_key(private_key)
            print(f"{Fore.YELLOW}  {LANG[language]['address']}: {account.address}{Style.RESET_ALL}")
            display_token_balances(w3, account.address, language)
            print_separator()
            
            # Pilih pasangan swap dan jumlah secara otomatis
            from_token, to_token, amount = select_random_swap_pair(w3, account.address, language)
            if not from_token:
                print(f"{Fore.RED}  ✖ No sufficient balance for any token{Style.RESET_ALL}")
                continue
            
            # Pilih jumlah swap secara acak (1-2)
            swap_times = random.randint(1, 2)
            
            print(f"{Fore.CYAN}  Auto-selected: {from_token} → {to_token}, Amount: {amount:.4f}, Times: {swap_times}{Style.RESET_ALL}")
            
            # Lakukan swap
            swaps = await swap_token(w3, private_key, profile_num, from_token, to_token, amount, swap_times, language)
            successful_swaps += swaps
            total_swaps += swap_times

        except Exception as wallet_error:
            print_border(f"Wallet error: {str(wallet_error)}", Fore.RED)
            continue  # Lanjut ke wallet berikutnya
        
        # Jeda antar wallet
        if i < len(private_keys):
            delay = random.uniform(10, 30)
            print(f"{Fore.YELLOW}  ℹ {LANG[language]['pausing']} {delay:.2f} {'giây' if language == 'vi' else 'seconds'}{Style.RESET_ALL}")
            await asyncio.sleep(delay)
        print_separator()
    
    print()
    print_border(f"{LANG[language]['completed'].format(successful=successful_swaps, total=total_swaps)}", Fore.GREEN)
    print()

if __name__ == "__main__":
    asyncio.run(run('en'))
