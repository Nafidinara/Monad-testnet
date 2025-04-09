import os
import random
import asyncio
import time
from web3 import Web3
from colorama import init, Fore, Style

# Khởi tạo colorama
init(autoreset=True)

# Constants
RPC_URLS = [
    "https://testnet-rpc.monorail.xyz",
    "https://testnet-rpc.monad.xyz",
    "https://monad-testnet.drpc.org"
]
EXPLORER_URL = "https://testnet.monadexplorer.com/tx/0x"
ROUTER_ADDRESS = "0xCa810D095e90Daae6e867c19DF6D9A8C56db2c89"
WMON_ADDRESS = "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701"

# Danh sách token hỗ trợ
TOKENS = {
    "USDC": {
        "address": "0x62534E4bBD6D9ebAC0ac99aeaa0aa48E56372df0",
        "symbol": "USDC",
        "name": "USD Coin",
        "minAmount": 0.01,
        "maxAmount": 1,
        "decimals": 6,
    },
    "USDT": {
        "address": "0x88b8e2161dedc77ef4ab7585569d2415a1c1055d",
        "symbol": "USDT",
        "name": "Tether USD",
        "minAmount": 0.01,
        "maxAmount": 1,
        "decimals": 6,
    },
    "BEAN": {
        "address": "0x268E4E24E0051EC27b3D27A95977E71cE6875a05",
        "symbol": "BEAN",
        "name": "Bean Token",
        "minAmount": 0.01,
        "maxAmount": 1,
        "decimals": 6,
    },
    "JAI": {
        "address": "0x70F893f65E3C1d7f82aad72f71615eb220b74D10",
        "symbol": "JAI",
        "name": "Jai Token",
        "minAmount": 0.01,
        "maxAmount": 1,
        "decimals": 6,
    },
}

# ABI cho ERC20 token
# Update ERC20_ABI to include the allowance function
ERC20_ABI = [
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
]

# ABI cho router
ROUTER_ABI = [
    {"inputs": [{"internalType": "uint256", "name": "amountOutMin", "type": "uint256"}, {"internalType": "address[]", "name": "path", "type": "address[]"}, {"internalType": "address", "name": "to", "type": "address"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}], "name": "swapExactETHForTokens", "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "amountIn", "type": "uint256"}, {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"}, {"internalType": "address[]", "name": "path", "type": "address[]"}, {"internalType": "address", "name": "to", "type": "address"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}], "name": "swapExactTokensForETH", "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}], "stateMutability": "nonpayable", "type": "function"}
]

# Hàm kết nối RPC
def connect_to_rpc():
    for url in RPC_URLS:
        w3 = Web3(Web3.HTTPProvider(url))
        if w3.is_connected():
            print(f"{Fore.BLUE}🪫 Đã kết nối RPC: {url}{Style.RESET_ALL}")
            return w3
        print(f"{Fore.YELLOW}Không kết nối được với {url}, thử RPC khác...{Style.RESET_ALL}")
    raise Exception(f"{Fore.RED}❌ Không thể kết nối với bất kỳ RPC nào{Style.RESET_ALL}")

# Khởi tạo web3 provider
w3 = connect_to_rpc()
ROUTER_ADDRESS = w3.to_checksum_address(ROUTER_ADDRESS)
WMON_ADDRESS = w3.to_checksum_address(WMON_ADDRESS)
TOKENS = {key: {**value, "address": w3.to_checksum_address(value["address"])} for key, value in TOKENS.items()}

# Hàm đọc private key từ pvkey.txt
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

# Hàm hiển thị viền đẹp mắt
def print_border(text, color=Fore.MAGENTA, width=60):
    print(f"{color}╔{'═' * (width - 2)}╗{Style.RESET_ALL}")
    print(f"{color}║ {text:^56} ║{Style.RESET_ALL}")
    print(f"{color}╚{'═' * (width - 2)}╝{Style.RESET_ALL}")

# Hàm hiển thị bước
def print_step(step, message, lang):
    steps = {
        'vi': {'approve': 'Approve Token', 'swap': 'Swap'},
        'en': {'approve': 'Approve Token', 'swap': 'Swap'}
    }
    step_text = steps[lang][step]
    print(f"{Fore.YELLOW}🔸 {Fore.CYAN}{step_text:<15}{Style.RESET_ALL} | {message}")

# Tạo số lượng ngẫu nhiên (0.001 - 0.01 MON)
def get_random_amount():
    return round(random.uniform(0.001, 0.01), 6)

# Tạo delay ngẫu nhiên (1-3 phút)
def get_random_delay():
    return random.randint(10, 30)  # Trả về giây

# Add this constant for max approval
MAX_UINT256 = 2**256 - 1  # Maximum uint256 value for unlimited approval

# Add this function to check token allowance
async def check_token_allowance(token_address, owner_address, spender_address, decimals, language, max_retries=3):
    token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
    
    for attempt in range(max_retries):
        try:
            # Add this function to ERC20_ABI if not already there
            allowance = token_contract.functions.allowance(owner_address, spender_address).call()
            return allowance
        except Exception as e:
            if "429 Client Error" in str(e) and attempt < max_retries - 1:
                delay = 2 ** attempt
                print_step('approve', f"{Fore.YELLOW}Thông tin đang truy vấn, thử lại sau {delay} giây...{Style.RESET_ALL}", language)
                await asyncio.sleep(delay)
            else:
                print_step('approve', f"{Fore.RED}✘ Lỗi kiểm tra allowance: {str(e)}{Style.RESET_ALL}", language)
                return 0
    return 0

# Hàm approve token với retry
# Modify the approve_token function to check allowance first and use MAX_UINT256
async def approve_token(private_key, token_address, amount, decimals, language, max_retries=3):
    account = w3.eth.account.from_key(private_key)
    wallet = account.address[:8] + "..."
    token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
    symbol = token_contract.functions.symbol().call()

    lang = {
        'vi': {'check': f'Đang kiểm tra approval cho {symbol}', 'approving': f'Đang approve {symbol}', 'success': f'{symbol} đã được approve', 'already': f'{symbol} đã được approve trước đó'},
        'en': {'check': f'Checking approval for {symbol}', 'approving': f'Approving {symbol}', 'success': f'{symbol} approved', 'already': f'{symbol} already approved'}
    }[language]

    print_step('approve', lang['check'], language)
    
    # Check current allowance
    amount_in_decimals = w3.to_wei(amount, 'ether') if decimals == 18 else int(amount * 10**decimals)
    current_allowance = await check_token_allowance(token_address, account.address, ROUTER_ADDRESS, decimals, language)
    
    # If allowance is sufficient, skip approval
    if current_allowance >= amount_in_decimals:
        print_step('approve', f"{Fore.GREEN}✔ {lang['already']}{Style.RESET_ALL}", language)
        return amount_in_decimals
    
    # Otherwise approve with MAX_UINT256
    for attempt in range(max_retries):
        try:
            print_step('approve', lang['approving'], language)
            tx = token_contract.functions.approve(ROUTER_ADDRESS, MAX_UINT256).build_transaction({
                'from': account.address,
                'gas': 100000,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(account.address),
            })

            signed_tx = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            await asyncio.sleep(2)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
            if receipt.status == 1:
                print_step('approve', f"{Fore.GREEN}✔ {lang['success']} (Max Approval){Style.RESET_ALL}", language)
                return amount_in_decimals
            else:
                raise Exception(f"Approve thất bại: Status {receipt.status}")
        except Exception as e:
            if "429 Client Error" in str(e) and attempt < max_retries - 1:
                delay = 2 ** attempt
                print_step('approve', f"{Fore.YELLOW}Thông tin đang truy vấn, thử lại sau {delay} giây...{Style.RESET_ALL}", language)
                await asyncio.sleep(delay)
            else:
                print_step('approve', f"{Fore.RED}✘ Thất bại / Failed: {str(e)}{Style.RESET_ALL}", language)
                raise

# Hàm swap Token sang MON
# Modify swap_token_to_mon function to check token balance
async def swap_token_to_mon(private_key, token_symbol, amount, language):
    token = TOKENS[token_symbol]
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:8] + "..."
        lang = {
            'vi': {'start': f'Swap {amount} {token_symbol} sang MON', 'send': 'Đang gửi giao dịch swap...', 'success': 'Swap thành công!', 'insufficient': 'Số dư không đủ'},
            'en': {'start': f'Swapping {amount} {token_symbol} to MON', 'send': 'Sending swap transaction...', 'success': 'Swap successful!', 'insufficient': 'Insufficient balance'}
        }[language]

        print_border(f"{lang['start']} | {wallet}", Fore.MAGENTA)
        
        # Check token balance first
        token_contract = w3.eth.contract(address=token['address'], abi=ERC20_ABI)
        token_balance = token_contract.functions.balanceOf(account.address).call()
        amount_in_decimals = int(amount * 10**token['decimals'])
        
        if token_balance < amount_in_decimals:
            print_step('swap', f"{Fore.RED}✘ {lang['insufficient']} - {token_symbol}: {token_balance/(10**token['decimals'])} < {amount}{Style.RESET_ALL}", language)
            return False
        
        # Approve token
        await approve_token(private_key, token['address'], amount, token['decimals'], language)
        
        # Create path array
        path = [token['address'], WMON_ADDRESS]
        
        # Use a safety buffer for minimum output (0 means no minimum)
        amountOutMin = 0
        
        # Calculate deadline - 10 minutes from now
        deadline = int(time.time()) + 600
        
        # Build transaction with increased gas
        router = w3.eth.contract(address=ROUTER_ADDRESS, abi=ROUTER_ABI)
        tx = router.functions.swapExactTokensForETH(
            amount_in_decimals, 
            amountOutMin, 
            path, 
            account.address, 
            deadline
        ).build_transaction({
            'from': account.address,
            'gas': 190000,  # Increased gas limit
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
        })

        print_step('swap', lang['send'], language)
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print_step('swap', f"Tx Hash: {Fore.YELLOW}{EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}", language)
        await asyncio.sleep(2)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
        
        if receipt.status == 1:
            print_step('swap', f"{Fore.GREEN}✔ {lang['success']}{Style.RESET_ALL}", language)
            return True
        else:
            raise Exception(f"Giao dịch thất bại: Status {receipt.status}")
    except Exception as e:
        error_message = str(e)
        # Create a more user-friendly error message
        if "execution reverted: TransferHelper::transferFrom" in error_message:
            print_step('swap', f"{Fore.RED}✘ Thất bại / Failed: Token transfer failed - Check balance or approval{Style.RESET_ALL}", language)
        else:
            print_step('swap', f"{Fore.RED}✘ Thất bại / Failed: {error_message}{Style.RESET_ALL}", language)
        return False

# Hàm swap MON sang Token
async def swap_mon_to_token(private_key, token_symbol, amount, language):
    token = TOKENS[token_symbol]
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:8] + "..."
        lang = {
            'vi': {'start': f'Swap {amount} MON sang {token_symbol}', 'send': 'Đang gửi giao dịch swap...', 'success': 'Swap thành công!'},
            'en': {'start': f'Swapping {amount} MON to {token_symbol}', 'send': 'Sending swap transaction...', 'success': 'Swap successful!'}
        }[language]

        print_border(f"{lang['start']} | {wallet}", Fore.MAGENTA)
        
        tx = w3.eth.contract(address=ROUTER_ADDRESS, abi=ROUTER_ABI).functions.swapExactETHForTokens(
            0, [WMON_ADDRESS, token['address']], account.address, int(time.time()) + 600
        ).build_transaction({
            'from': account.address,
            'value': w3.to_wei(amount, 'ether'),
            'gas': 180000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
        })

        print_step('swap', lang['send'], language)
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print_step('swap', f"Tx Hash: {Fore.YELLOW}{EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}", language)
        await asyncio.sleep(2)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
        
        if receipt.status == 1:
            print_step('swap', f"{Fore.GREEN}✔ {lang['success']}{Style.RESET_ALL}", language)
            return True
        else:
            raise Exception(f"Giao dịch thất bại: Status {receipt.status}")
    except Exception as e:
        print_step('swap', f"{Fore.RED}✘ Thất bại / Failed: {str(e)}{Style.RESET_ALL}", language)
        return False

# Hàm kiểm tra số dư với retry
async def check_balance(private_key, language, max_retries=3):
    account = w3.eth.account.from_key(private_key)
    wallet = account.address[:8] + "..."
    lang = {'vi': 'Số dư', 'en': 'Balance'}[language]
    print_border(f"💰 {lang} | {wallet}", Fore.CYAN)
    
    try:
        mon_balance = w3.eth.get_balance(account.address)
        print_step('swap', f"MON: {Fore.CYAN}{w3.from_wei(mon_balance, 'ether')}{Style.RESET_ALL}", language)
    except Exception as e:
        print_step('swap', f"MON: {Fore.RED}Lỗi đọc số dư - {str(e)}{Style.RESET_ALL}", language)
    
    for symbol, token in TOKENS.items():
        for attempt in range(max_retries):
            try:
                token_contract = w3.eth.contract(address=token['address'], abi=ERC20_ABI)
                balance = token_contract.functions.balanceOf(account.address).call()
                print_step('swap', f"{symbol}: {Fore.CYAN}{balance / 10**token['decimals']}{Style.RESET_ALL}", language)
                break
            except Exception as e:
                if "429 Client Error" in str(e) and attempt < max_retries - 1:
                    delay = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    print_step('swap', f"{Fore.YELLOW}{symbol}: Quá nhiều yêu cầu, thử lại sau {delay} giây...{Style.RESET_ALL}", language)
                    await asyncio.sleep(delay)
                else:
                    print_step('swap', f"{symbol}: {Fore.RED}Lỗi đọc số dư - {str(e)}{Style.RESET_ALL}", language)
                    break
            await asyncio.sleep(1)  # Delay giữa các token

# Hàm thực hiện random swap
async def perform_random_swap(private_key, language):
    account = w3.eth.account.from_key(private_key)
    wallet = account.address[:8] + "..."
    is_mon_to_token = random.random() < 0.5
    token_symbols = list(TOKENS.keys())
    token_symbol = random.choice(token_symbols)
    token = TOKENS[token_symbol]

    if is_mon_to_token:
        amount = get_random_amount()
        amount_in_wei = w3.to_wei(amount, 'ether')
        print_border(f"🎲 Random Swap: {amount} MON → {token_symbol} | {wallet}", Fore.YELLOW)
        return await swap_mon_to_token(private_key, token_symbol, amount, language)
    else:
        amount = get_random_amount()
        print_border(f"🎲 Random Swap: {amount} {token_symbol} → MON | {wallet}", Fore.YELLOW)
        return await swap_token_to_mon(private_key, token_symbol, amount, language)

# Chạy vòng lặp swap
async def run_swap_cycle(cycles, private_keys, language):
    lang = {
        'vi': "VÒNG LẶP SWAP BEAN / BEAN SWAP CYCLE",
        'en': "BEAN SWAP CYCLE"
    }[language]

    for account_idx, private_key in enumerate(private_keys, 1):
        account = w3.eth.account.from_key(private_key)  # Khai báo account tại đây
        wallet = account.address[:8] + "..."
        print_border(f"🏦 TÀI KHOẢN / ACCOUNT {account_idx}/{len(private_keys)} | {wallet}", Fore.BLUE)
        await check_balance(private_key, language)

        for i in range(cycles):
            print_border(f"🔄 {lang} {i + 1}/{cycles} | {wallet}", Fore.CYAN)
            success = await perform_random_swap(private_key, language)
            if success:
                await check_balance(private_key, language)
            
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
    print(f"{Fore.GREEN}│ {'BEAN SWAP - MONAD TESTNET':^56} │{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")

    private_keys = load_private_keys('pvkey.txt')
    if not private_keys:
        return

    print(f"{Fore.CYAN}👥 {'Tài khoản' if language == 'vi' else 'Accounts'}: {len(private_keys)}{Style.RESET_ALL}")

    while True:
        try:
            print_border("🔢 SỐ VÒNG LẶP / NUMBER OF CYCLES", Fore.YELLOW)
            cycles_input = input(f"{Fore.GREEN}➤ {'Nhập số (mặc định 5): ' if language == 'vi' else 'Enter number (default 5): '}{Style.RESET_ALL}")
            cycles = int(cycles_input) if cycles_input.strip() else 5
            if cycles <= 0:
                raise ValueError
            break
        except ValueError:
            print(f"{Fore.RED}❌ {'Vui lòng nhập số hợp lệ!' if language == 'vi' else 'Please enter a valid number!'}{Style.RESET_ALL}")

    start_msg = f"Chạy {cycles} vòng swap Bean với giá trị ngẫu nhiên 1-3 phút cho {len(private_keys)} tài khoản..." if language == 'vi' else f"Running {cycles} Bean swaps with random 1-3 minute delay for {len(private_keys)} accounts..."
    print(f"{Fore.YELLOW}🚀 {start_msg}{Style.RESET_ALL}")
    await run_swap_cycle(cycles, private_keys, language)

if __name__ == "__main__":
    asyncio.run(run('en'))
