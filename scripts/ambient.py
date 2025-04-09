import asyncio
import random
from typing import Dict, List, Optional, Tuple
from eth_account import Account
from eth_abi import abi
from decimal import Decimal
from loguru import logger
from web3 import AsyncWeb3, Web3
import aiohttp
from colorama import init, Fore, Style

# Khởi tạo colorama
init(autoreset=True)

# Định nghĩa các hằng số cố định
RPC_URL = "https://testnet-rpc.monad.xyz/"
EXPLORER_URL = "https://testnet.monadexplorer.com/tx/0x"
AMBIENT_CONTRACT = "0x88B96aF200c8a9c35442C8AC6cd3D22695AaE4F0"
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
POOL_IDX = 36000
RESERVE_FLAGS = 0
TIP = 0
MAX_SQRT_PRICE = 21267430153580247136652501917186561137
MIN_SQRT_PRICE = 65537
BORDER_WIDTH = 80  # Độ rộng viền cho giao diện
ATTEMPTS = 3
PAUSE_BETWEEN_SWAPS = [5, 10]
PAUSE_BETWEEN_ACTIONS = [5, 15]
MAX_UINT256 = 2**256 - 1  # Giá trị max uint256 cho approve

AMBIENT_TOKENS = {
    "usdt": {"address": "0x88b8E2161DEDC77EF4ab7585569D2415a1C1055D", "decimals": 6},
    "usdc": {"address": "0xf817257fed379853cDe0fa4F97AB987181B1E5Ea", "decimals": 6},
    "weth": {"address": "0xB5a30b0FDc5EA94A52fDc42e3E9760Cb8449Fb37", "decimals": 18},
    "wbtc": {"address": "0xcf5a6076cfa32686c0Df13aBaDa2b40dec133F1d", "decimals": 8},
    "seth": {"address": "0x836047a99e11F376522B447bffb6e3495Dd0637c", "decimals": 18},
}

ERC20_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "spender", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "address", "name": "spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

AMBIENT_ABI = [
    {
        "inputs": [
            {"internalType": "uint16", "name": "callpath", "type": "uint16"},
            {"internalType": "bytes", "name": "cmd", "type": "bytes"},
        ],
        "name": "userCmd",
        "outputs": [{"internalType": "bytes", "name": "", "type": "bytes"}],
        "stateMutability": "payable",
        "type": "function",
    }
]

# Hàm hiển thị viền đẹp mắt
def print_border(text: str, color=Fore.CYAN, width=BORDER_WIDTH):
    text = text.strip()
    if len(text) > width - 4:
        text = text[:width - 7] + "..."
    padded_text = f" {text} ".center(width - 2)
    print(f"{color}┌{'─' * (width - 2)}┐{Style.RESET_ALL}")
    print(f"{color}│{padded_text}│{Style.RESET_ALL}")
    print(f"{color}└{'─' * (width - 2)}┘{Style.RESET_ALL}")

# Hàm hiển thị bước với định dạng đẹp
def print_step(step: str, message: str, lang: str):
    steps = {
        'vi': {
            'balance': 'SỐ DƯ',
            'faucet': 'LẤY TOKEN',
            'approve': 'PHÊ DUYỆT',
            'swap': 'HOÁN ĐỔI'
        },
        'en': {
            'balance': 'BALANCE',
            'faucet': 'GET TOKENS',
            'approve': 'APPROVE',
            'swap': 'SWAP'
        }
    }
    step_text = steps[lang][step]
    formatted_step = f"{Fore.YELLOW}🔸 {Fore.CYAN}{step_text:<15}{Style.RESET_ALL}"
    print(f"{formatted_step} | {message}")

# Hàm hiển thị thông báo hoàn tất song ngữ
def print_completion_message(accounts: int, language: str, success_count: int):
    lang = {
        'vi': {
            'title': "AMBIENT SWAP - MONAD TESTNET",
            'done': "HOÀN TẤT",
            'accounts': "TÀI KHOẢN",
            'success': "GIAO DỊCH THÀNH CÔNG",
            'start_msg': f"Đã hoàn tất hoán đổi cho {accounts} tài khoản",
        },
        'en': {
            'title': "AMBIENT SWAP - MONAD TESTNET",
            'done': "ALL DONE",
            'accounts': "ACCOUNTS",
            'success': "SUCCESSFUL TRANSACTIONS",
            'start_msg': f"Completed swap for {accounts} accounts",
        }
    }[language]

    print(f"{Fore.GREEN}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")
    print_border(f" {lang['title']} ", Fore.GREEN)
    print(f"{Fore.GREEN}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}🎉 {lang['start_msg']:^76}{Style.RESET_ALL}")
    completion_msg = f"{lang['done']} - {accounts} {lang['accounts']}"
    print_border(completion_msg, Fore.GREEN)
    success_msg = f"{lang['success']}: {success_count}"
    print_border(success_msg, Fore.CYAN)
    print(f"{Fore.GREEN}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")

class AmbientDex:
    def __init__(self, account_index: int, private_key: str, session: aiohttp.ClientSession, language: str, swap_percentage: float):
        self.account_index = account_index
        self.web3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(RPC_URL))
        self.account = Account.from_key(private_key)
        self.session = session
        self.language = language
        self.swap_percentage = swap_percentage
        self.router_contract = self.web3.eth.contract(address=AMBIENT_CONTRACT, abi=AMBIENT_ABI)

    async def get_gas_params(self) -> Dict[str, int]:
        """Lấy thông số gas từ mạng."""
        try:
            latest_block = await self.web3.eth.get_block('latest')
            base_fee = latest_block['baseFeePerGas']
            max_priority_fee = await self.web3.eth.max_priority_fee
            return {
                "maxFeePerGas": base_fee + max_priority_fee,
                "maxPriorityFeePerGas": max_priority_fee,
            }
        except Exception as e:
            logger.warning(f"[{self.account_index}] Error getting gas params: {str(e)}. Using default values")
            # Provide default values if there's an error
            return {
                "maxFeePerGas": self.web3.to_wei(0.0000005, 'ether'),
                "maxPriorityFeePerGas": self.web3.to_wei(0.0000001, 'ether'),
            }

    def convert_to_wei(self, amount: float, token: str) -> int:
        """Chuyển đổi số lượng sang wei dựa trên số thập phân của token."""
        if token == "native":
            return self.web3.to_wei(amount, 'ether')
        decimals = AMBIENT_TOKENS[token.lower()]["decimals"]
        return int(Decimal(str(amount)) * Decimal(str(10 ** decimals)))

    def convert_from_wei(self, amount: int, token: str) -> float:
        """Chuyển đổi từ wei về đơn vị token."""
        if token == "native":
            return float(self.web3.from_wei(amount, 'ether'))
        decimals = AMBIENT_TOKENS[token.lower()]["decimals"]
        return float(Decimal(str(amount)) / Decimal(str(10 ** decimals)))

    async def get_tokens_with_balance(self) -> List[Tuple[str, float]]:
        """Lấy danh sách token có số dư lớn hơn 0."""
        tokens_with_balance = []
        
        # Kiểm tra số dư native token (MON)
        try:
            native_balance = await self.web3.eth.get_balance(self.account.address)
            if native_balance > 0:
                # Giữ lại một phần nhỏ để trả phí gas
                gas_reserve = self.web3.to_wei(0.01, 'ether')
                if native_balance > gas_reserve:
                    native_amount = self.convert_from_wei(native_balance - gas_reserve, "native")
                    tokens_with_balance.append(("native", native_amount))
        except Exception as e:
            logger.error(f"[{self.account_index}] Failed to get native balance: {str(e)}")
        
        # Kiểm tra số dư các token khác
        for token in AMBIENT_TOKENS:
            try:
                token_contract = self.web3.eth.contract(
                    address=self.web3.to_checksum_address(AMBIENT_TOKENS[token]["address"]),
                    abi=ERC20_ABI
                )
                balance = await token_contract.functions.balanceOf(self.account.address).call()
                if balance > 0:
                    amount = self.convert_from_wei(balance, token)
                    # Bỏ qua SETH và WETH nếu số dư quá thấp
                    if token.lower() in ["seth", "weth"] and amount < 0.001:
                        continue
                    tokens_with_balance.append((token, amount))
            except Exception as e:
                logger.error(f"[{self.account_index}] Failed to get balance for {token}: {str(e)}")
                continue
        
        return tokens_with_balance

    async def generate_swap_data(self, token_in: str, token_out: str, amount_in_wei: int) -> Dict:
        """Tạo dữ liệu giao dịch swap cho Ambient DEX."""
        for retry in range(ATTEMPTS):
            try:
                is_native = token_in == "native"
                token_address = (
                    AMBIENT_TOKENS[token_out.lower()]["address"] if is_native 
                    else AMBIENT_TOKENS[token_in.lower()]["address"]
                )
                
                # Áp dụng phần trăm swap nếu đó là native token
                if is_native:
                    percentage = Decimal(str(self.swap_percentage)) / Decimal('100')
                    amount_in_wei = int(Decimal(str(amount_in_wei)) * percentage)
                
                encode_data = abi.encode(
                    ['address', 'address', 'uint16', 'bool', 'bool', 'uint256', 'uint8', 'uint256', 'uint256', 'uint8'],
                    [
                        ZERO_ADDRESS,
                        self.web3.to_checksum_address(token_address),
                        POOL_IDX,
                        is_native,
                        is_native,
                        amount_in_wei,
                        TIP,
                        MAX_SQRT_PRICE if is_native else MIN_SQRT_PRICE,
                        0,
                        RESERVE_FLAGS
                    ]
                )
                function_selector = self.web3.keccak(text="userCmd(uint16,bytes)")[:4]
                cmd_params = abi.encode(['uint16', 'bytes'], [1, encode_data])
                tx_data = function_selector.hex() + cmd_params.hex()

                try:
                    gas_estimate = await self.web3.eth.estimate_gas({
                        'to': AMBIENT_CONTRACT,
                        'from': self.account.address,
                        'data': '0x' + tx_data,
                        'value': amount_in_wei if is_native else 0
                    })
                except Exception as gas_error:
                    logger.warning(f"[{self.account_index}] Gas estimation failed: {str(gas_error)}. Using default gas limit.")
                    gas_estimate = 210000  # Fallback gas limit

                return {
                    "to": AMBIENT_CONTRACT,
                    "data": '0x' + tx_data,
                    "value": amount_in_wei if is_native else 0,
                    "gas": int(gas_estimate * 1.2)  # Increased gas multiplier for better chances
                }
            except Exception as e:
                await self._handle_error("generate_swap_data", e)
        raise Exception("Failed to generate swap data after retries")

    async def execute_transaction(self, tx_data: Dict) -> str:
        """Thực hiện giao dịch và chờ xác nhận."""
        for retry in range(ATTEMPTS):
            try:
                nonce = await self.web3.eth.get_transaction_count(self.account.address)
                gas_params = await self.get_gas_params()
                transaction = {
                    "from": self.account.address,
                    "nonce": nonce,
                    "type": 2,
                    "chainId": 10143,
                    **tx_data,
                    **gas_params,
                }
                
                signed_txn = self.web3.eth.account.sign_transaction(transaction, self.account.key)
                tx_hash = await self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)
                print_step('swap', f"Waiting for transaction confirmation... TX: {EXPLORER_URL}{tx_hash.hex()}", self.language)
                receipt = await self.web3.eth.wait_for_transaction_receipt(tx_hash, poll_latency=2, timeout=120)
                if receipt['status'] == 1:
                    logger.success(f"[{self.account_index}] Transaction successful! TX: {EXPLORER_URL}{tx_hash.hex()}")
                    print_step('swap', f"{Fore.GREEN}✔ Transaction confirmed! TX: {EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}", self.language)
                    return tx_hash.hex()
                else:
                    raise Exception(f"Transaction failed: {EXPLORER_URL}{tx_hash.hex()}")
            except Exception as e:
                await self._handle_error("execute_transaction", e)
        raise Exception("Transaction execution failed after retries")

    async def approve_token(self, token: str, amount: int) -> Optional[str]:
        """Phê duyệt token cho Ambient DEX với MAX_UINT256."""
        for retry in range(ATTEMPTS):
            try:
                token_contract = self.web3.eth.contract(
                    address=self.web3.to_checksum_address(AMBIENT_TOKENS[token.lower()]["address"]),
                    abi=ERC20_ABI
                )
                
                # Kiểm tra allowance hiện tại
                current_allowance = await token_contract.functions.allowance(
                    self.account.address, AMBIENT_CONTRACT
                ).call()
                
                # Nếu allowance đã đủ, không cần phê duyệt lại
                if current_allowance >= amount:
                    logger.info(f"[{self.account_index}] Allowance sufficient for {token.upper()}: {current_allowance}")
                    print_step('approve', f"{Fore.GREEN}✔ Allowance already sufficient for {token.upper()}{Style.RESET_ALL}", self.language)
                    return None

                # Sử dụng MAX_UINT256 thay vì số lượng cụ thể
                nonce = await self.web3.eth.get_transaction_count(self.account.address)
                gas_params = await self.get_gas_params()
                
                approve_tx = await token_contract.functions.approve(
                    AMBIENT_CONTRACT, MAX_UINT256
                ).build_transaction({
                    'from': self.account.address,
                    'nonce': nonce,
                    'type': 2,
                    'chainId': 10143,
                    **gas_params,
                })
                
                signed_txn = self.web3.eth.account.sign_transaction(approve_tx, self.account.key)
                tx_hash = await self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)
                print_step('approve', f"Approving {token.upper()} with MAX value...", self.language)
                receipt = await self.web3.eth.wait_for_transaction_receipt(tx_hash, poll_latency=2, timeout=120)
                
                if receipt['status'] == 1:
                    logger.success(f"[{self.account_index}] Approval successful! TX: {EXPLORER_URL}{tx_hash.hex()}")
                    print_step('approve', f"{Fore.GREEN}✔ Approved with MAX value! TX: {EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}", self.language)
                    return tx_hash.hex()
                raise Exception("Approval failed")
            except Exception as e:
                await self._handle_error("approve_token", e)
        raise Exception(f"Failed to approve {token} after retries")

    async def swap(self, swap_type: str = "regular") -> Optional[str]:
        """Thực hiện swap trên Ambient DEX."""
        for retry in range(ATTEMPTS):
            try:
                tokens_with_balance = await self.get_tokens_with_balance()
                if not tokens_with_balance:
                    print_step('swap', f"{Fore.RED}✘ No tokens with balance found{Style.RESET_ALL}", self.language)
                    return None

                if swap_type == "collect":
                    tokens_to_swap = [(t, b) for t, b in tokens_with_balance if t != "native"]
                    if not tokens_to_swap:
                        print_step('swap', f"{Fore.YELLOW}⚠ No tokens to collect to native{Style.RESET_ALL}", self.language)
                        return None

                    for token_in, balance in tokens_to_swap:
                        try:
                            if token_in.lower() == "seth":
                                leave_amount = random.uniform(0.00001, 0.0001)
                                balance -= leave_amount
                            amount_wei = self.convert_to_wei(balance, token_in)
                            await self.approve_token(token_in, amount_wei)
                            await asyncio.sleep(random.uniform(*PAUSE_BETWEEN_SWAPS))
                            print_step('swap', f"Swapping {balance:.4f} {token_in.upper()} to MON...", self.language)
                            tx_data = await self.generate_swap_data(token_in, "native", amount_wei)
                            tx_hash = await self.execute_transaction(tx_data)
                            if token_in != tokens_to_swap[-1][0]:
                                await asyncio.sleep(random.uniform(5, 10))
                        except Exception as e:
                            logger.error(f"[{self.account_index}] Failed to collect {token_in} to native: {str(e)}")
                            continue
                    print_step('swap', f"{Fore.GREEN}✔ Collection to native completed{Style.RESET_ALL}", self.language)
                    return "Collection complete"

                else:  # Regular swap
                    # Memilih token secara acak dari saldo yang tersedia
                    token_in, balance = random.choice(tokens_with_balance)
                    available_out_tokens = list(AMBIENT_TOKENS.keys()) + ["native"]
                    if token_in in available_out_tokens:
                        available_out_tokens.remove(token_in)
                    token_out = random.choice(available_out_tokens)

                    if token_in == "native":
                        # Ambil saldo terbaru native token
                        native_balance = await self.web3.eth.get_balance(self.account.address)
                        # Simpan untuk gas
                        gas_reserve = self.web3.to_wei(0.01, 'ether')
                        available_balance = max(0, native_balance - gas_reserve)
                        
                        # Aplikasikan persentase swap
                        amount_wei = int(available_balance * self.swap_percentage / 100)
                        amount_token = self.convert_from_wei(amount_wei, "native")
                        
                        # Periksa jika jumlah terlalu kecil
                        if amount_wei <= 0:
                            print_step('swap', f"{Fore.RED}✘ Amount too small after applying {self.swap_percentage}% to native token{Style.RESET_ALL}", self.language)
                            return None
                    else:
                        # Untuk token non-native, gunakan seluruh saldo (atau sisakan sedikit untuk SETH)
                        if token_in.lower() == "seth":
                            leave_amount = random.uniform(0.00001, 0.0001)
                            balance -= leave_amount
                        
                        # Aplikasikan persentase swap untuk token non-native
                        balance = balance * self.swap_percentage / 100
                        amount_wei = self.convert_to_wei(balance, token_in)
                        amount_token = balance
                        
                        # Periksa jika jumlah terlalu kecil
                        if amount_wei <= 0:
                            print_step('swap', f"{Fore.RED}✘ Amount too small after applying {self.swap_percentage}% to {token_in}{Style.RESET_ALL}", self.language)
                            return None
                            
                        # Approve token
                        await self.approve_token(token_in, amount_wei)
                        await asyncio.sleep(random.uniform(*PAUSE_BETWEEN_SWAPS))

                    print_step('swap', f"Swapping {amount_token:.6f} {token_in.upper()} to {token_out.upper()}... ({self.swap_percentage}%)", self.language)
                    tx_data = await self.generate_swap_data(token_in, token_out, amount_wei)
                    return await self.execute_transaction(tx_data)

            except Exception as e:
                await self._handle_error("swap", e)
        print_step('swap', f"{Fore.RED}✘ Swap failed after {ATTEMPTS} attempts{Style.RESET_ALL}", self.language)
        return None

    async def _handle_error(self, action: str, error: Exception) -> None:
        """Xử lý lỗi với pause ngẫu nhiên."""
        pause = random.uniform(*PAUSE_BETWEEN_ACTIONS)
        logger.error(f"[{self.account_index}] Error in {action}: {error}. Sleeping for {pause:.2f}s")
        print_step(action, f"{Fore.RED}✘ Error: {str(error)}. Retrying in {pause:.2f}s{Style.RESET_ALL}", self.language)
        await asyncio.sleep(pause)

async def run(language: str, swap_percentage: float = 10) -> None:
    """Chạy script Ambient với nhiều private keys từ pvkey.txt."""
    try:
        with open("pvkey.txt", "r") as f:
            private_keys = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logger.error("File pvkey.txt not found!")
        print_border("ERROR: pvkey.txt not found!", Fore.RED)
        return

    if not private_keys:
        logger.error("No private keys found in pvkey.txt!")
        print_border("ERROR: No private keys found in pvkey.txt!", Fore.RED)
        return

    # Hiển thị tiêu đề mở đầu
    print(f"{Fore.GREEN}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")
    print_border("AMBIENT SWAP - MONAD TESTNET", Fore.GREEN)
    print(f"{Fore.GREEN}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}👥 {'Tài khoản / Accounts'}: {len(private_keys):^76}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💹 {'Phần trăm swap / Swap Percentage'}: {swap_percentage}%{Style.RESET_ALL}")

    success_count = 0
    async with aiohttp.ClientSession() as session:
        for idx, private_key in enumerate(private_keys, start=1):
            wallet_short = Account.from_key(private_key).address[:8] + "..."
            account_msg = f"ACCOUNT {idx}/{len(private_keys)} - {wallet_short}"
            print_border(account_msg, Fore.BLUE)
            ambient = AmbientDex(idx, private_key, session, language, swap_percentage)
            logger.info(f"Processing account {idx}/{len(private_keys)}: {ambient.account.address}")

            # Thực hiện swap
            try:
                tx_hash = await ambient.swap(swap_type="regular")
                if tx_hash:
                    success_count += 1
            except Exception as e:
                logger.error(f"[{idx}] Failed to execute swap: {str(e)}")
                print_step('swap', f"{Fore.RED}✘ Swap failed: {str(e)}{Style.RESET_ALL}", language)

            # Pause giữa các tài khoản
            if idx < len(private_keys):
                pause = random.uniform(10, 30)
                pause_msg = f"{'Đợi / Waiting'} {pause:.2f}s {'trước tài khoản tiếp theo... / before next account...'}"
                print(f"{Fore.YELLOW}⏳ {pause_msg:^76}{Style.RESET_ALL}")
                await asyncio.sleep(pause)

    # Hiển thị thông báo hoàn tất
    print_completion_message(accounts=len(private_keys), language=language, success_count=success_count)

if __name__ == "__main__":
    # Cho phép người dùng nhập phần trăm swap
    try:
        swap_percentage = float(input("Enter swap percentage (1-100, default 10): ") or 10)
        swap_percentage = max(1, min(100, swap_percentage))  # Giới hạn giá trị từ 1-100
    except ValueError:
        swap_percentage = 10.0
        print(f"{Fore.YELLOW}Invalid input, using default: 10%{Style.RESET_ALL}")
    
    # Chọn ngôn ngữ
    language = input("Choose language (vi/en, default vi): ").lower() or "vi"
    if language not in ["vi", "en"]:
        language = "vi"
    
    asyncio.run(run(language, swap_percentage))