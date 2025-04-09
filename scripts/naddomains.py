import asyncio
import random
import string
from typing import Dict, List, Optional
from eth_account import Account
from loguru import logger
from web3 import AsyncWeb3, Web3
import aiohttp
from colorama import init, Fore, Style

# Khởi tạo colorama
init(autoreset=True)

# Định nghĩa các hằng số cố định
RPC_URL = "https://testnet-rpc.monad.xyz/"
EXPLORER_URL = "https://testnet.monadexplorer.com/tx/0x"
NAD_CONTRACT_ADDRESS = "0x758D80767a751fc1634f579D76e1CcaAb3485c9c"
NAD_API_URL = "https://api.nad.domains/register/signature"
NAD_NFT_ADDRESS = "0x3019BF1dfB84E5b46Ca9D0eEC37dE08a59A41308"
BORDER_WIDTH = 80
ATTEMPTS = 3
PAUSE_BETWEEN_ACTIONS = [5, 15]
MIN_MON_BALANCE = 0.1  # Số dư tối thiểu cần để đăng ký

# ABI cho NAD NFT (ERC721)
NAD_NFT_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# ABI cho NAD Domains
NAD_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "string", "name": "name", "type": "string"},
                    {"internalType": "address", "name": "nameOwner", "type": "address"},
                    {"internalType": "bool", "name": "setAsPrimaryName", "type": "bool"},
                    {"internalType": "address", "name": "referrer", "type": "address"},
                    {"internalType": "bytes32", "name": "discountKey", "type": "bytes32"},
                    {"internalType": "bytes", "name": "discountClaimProof", "type": "bytes"},
                    {"internalType": "uint256", "name": "nonce", "type": "uint256"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                ],
                "internalType": "struct NadRegistrarController.RegisterParams",
                "name": "params",
                "type": "tuple"
            },
            {"internalType": "bytes", "name": "signature", "type": "bytes"}
        ],
        "name": "registerWithSignature",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "string", "name": "name", "type": "string"},
                    {"internalType": "address", "name": "nameOwner", "type": "address"},
                    {"internalType": "bool", "name": "setAsPrimaryName", "type": "bool"},
                    {"internalType": "address", "name": "referrer", "type": "address"},
                    {"internalType": "bytes32", "name": "discountKey", "type": "bytes32"},
                    {"internalType": "bytes", "name": "discountClaimProof", "type": "bytes"}
                ],
                "internalType": "struct NadRegistrarController.RegisterParamsBase",
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "calculateRegisterFee",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
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
            'check': 'KIỂM TRA',
            'register': 'ĐĂNG KÝ'
        },
        'en': {
            'balance': 'BALANCE',
            'check': 'CHECK',
            'register': 'REGISTER'
        }
    }
    step_text = steps[lang][step]
    formatted_step = f"{Fore.YELLOW}🔸 {Fore.CYAN}{step_text:<15}{Style.RESET_ALL}"
    print(f"{formatted_step} | {message}")

# Hàm hiển thị thông báo hoàn tất song ngữ
def print_completion_message(accounts: int, language: str, success_count: int):
    lang = {
        'vi': {
            'title': "NAD DOMAINS - MONAD TESTNET",
            'done': "HOÀN TẤT",
            'accounts': "TÀI KHOẢN",
            'success': "ĐĂNG KÝ THÀNH CÔNG",
            'start_msg': f"Đã hoàn tất đăng ký tên miền cho {accounts} tài khoản",
        },
        'en': {
            'title': "NAD DOMAINS - MONAD TESTNET",
            'done': "ALL DONE",
            'accounts': "ACCOUNTS",
            'success': "SUCCESSFUL REGISTRATIONS",
            'start_msg': f"Completed domain registration for {accounts} accounts",
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

class NadDomains:
    def __init__(self, account_index: int, private_key: str, session: aiohttp.ClientSession, language: str):
        self.account_index = account_index
        self.private_key = private_key
        self.session = session
        self.language = language
        self.account = Account.from_key(private_key=private_key)
        self.web3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(RPC_URL))
        self.contract = self.web3.eth.contract(address=NAD_CONTRACT_ADDRESS, abi=NAD_ABI)
        self.nft_contract = self.web3.eth.contract(address=NAD_NFT_ADDRESS, abi=NAD_NFT_ABI)

    async def get_gas_params(self) -> Dict[str, int]:
        """Lấy thông số gas từ mạng."""
        messages = {
            'vi': "Lấy thông số gas từ mạng...",
            'en': "Retrieving gas parameters from network..."
        }
        print_step('check', messages[self.language], self.language)
        latest_block = await self.web3.eth.get_block("latest")
        base_fee = latest_block["baseFeePerGas"]
        max_priority_fee = await self.web3.eth.max_priority_fee
        return {
            "maxFeePerGas": base_fee + max_priority_fee,
            "maxPriorityFeePerGas": max_priority_fee,
        }

    def generate_random_name(self, min_length=6, max_length=12) -> str:
        """Tạo tên miền ngẫu nhiên."""
        length = random.randint(min_length, max_length)
        characters = string.ascii_lowercase + string.digits
        name = ''.join(random.choice(characters) for _ in range(length))
        if name[0].isdigit():
            name = random.choice(string.ascii_lowercase) + name[1:]
        return name

    async def get_signature(self, name: str) -> Optional[Dict]:
        """Lấy chữ ký từ API cho việc đăng ký tên miền."""
        messages = {
            'vi': "Đang yêu cầu chữ ký từ API...",
            'en': "Requesting signature from API..."
        }
        print_step('check', messages[self.language], self.language)
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'origin': 'https://app.nad.domains',
            'referer': 'https://app.nad.domains/',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
        }
        params = {
            'name': name,
            'nameOwner': self.account.address,
            'setAsPrimaryName': 'true',
            'referrer': '0x0000000000000000000000000000000000000000',
            'discountKey': '0x0000000000000000000000000000000000000000000000000000000000000000',
            'discountClaimProof': '0x0000000000000000000000000000000000000000000000000000000000000000',
            'chainId': '10143',
        }
        for retry in range(ATTEMPTS):
            try:
                async with aiohttp.ClientSession(trust_env=True, connector=aiohttp.TCPConnector(ssl=False)) as temp_session:
                    response = await temp_session.get(NAD_API_URL, params=params, headers=headers)
                if response.status != 200:
                    logger.error(f"[{self.account_index}] API error: Status code {response.status}")
                    error_msg = {
                        'vi': f"Lỗi API: Mã trạng thái {response.status}",
                        'en': f"API error: Status code {response.status}"
                    }
                    print_step('check', f"{Fore.RED}✘ {error_msg[self.language]}{Style.RESET_ALL}", self.language)
                    return None
                data = await response.json()
                if data.get('success'):
                    logger.info(f"[{self.account_index}] Got signature for domain {name}")
                    success_msg = {
                        'vi': f"Đã nhận chữ ký cho tên miền {name}",
                        'en': f"Received signature for domain {name}"
                    }
                    print_step('check', f"{Fore.GREEN}✔ {success_msg[self.language]}{Style.RESET_ALL}", self.language)
                    return {
                        'signature': data['signature'],
                        'nonce': int(data['nonce']),
                        'deadline': int(data['deadline'])
                    }
                else:
                    logger.error(f"[{self.account_index}] API error: {data.get('message', 'Unknown error')}")
                    error_msg = {
                        'vi': f"Lỗi API: {data.get('message', 'Lỗi không xác định')}",
                        'en': f"API error: {data.get('message', 'Unknown error')}"
                    }
                    print_step('check', f"{Fore.RED}✘ {error_msg[self.language]}{Style.RESET_ALL}", self.language)
                    return None
            except Exception as e:
                await self._handle_error("get_signature", e)
        failure_msg = {
            'vi': f"Không thể lấy chữ ký cho {name} sau {ATTEMPTS} lần thử",
            'en': f"Failed to get signature for {name} after {ATTEMPTS} attempts"
        }
        print_step('check', f"{Fore.RED}✘ {failure_msg[self.language]}{Style.RESET_ALL}", self.language)
        return None

    async def calculate_fee(self, name: str) -> int:
        """Tính phí đăng ký tên miền dựa trên độ dài hoặc gọi hợp đồng."""
        messages = {
            'vi': f"Đang tính phí cho {name}...",
            'en': f"Calculating fee for {name}..."
        }
        print_step('register', messages[self.language], self.language)
        try:
            params = [
                name,
                self.account.address,
                True,
                "0x0000000000000000000000000000000000000000",
                "0x0000000000000000000000000000000000000000000000000000000000000000",
                "0x0000000000000000000000000000000000000000000000000000000000000000"
            ]
            fee = await self.contract.functions.calculateRegisterFee(params).call()
            logger.info(f"[{self.account_index}] Calculated fee for {name}: {self.web3.from_wei(fee, 'ether')} MON")
            fee_msg = {
                'vi': f"Phí: {self.web3.from_wei(fee, 'ether')} MON",
                'en': f"Fee: {self.web3.from_wei(fee, 'ether')} MON"
            }
            print_step('register', f"{Fore.CYAN}{fee_msg[self.language]}{Style.RESET_ALL}", self.language)
            return fee
        except Exception as e:
            # Nếu gọi hợp đồng thất bại, dùng phí mặc định dựa trên độ dài
            error_msg = {
                'vi': f"Lỗi tính phí on-chain: {str(e)}. Dùng phí mặc định dựa trên độ dài.",
                'en': f"On-chain fee calculation error: {str(e)}. Using default fee based on length."
            }
            logger.error(f"[{self.account_index}] {error_msg[self.language]}")
            print_step('register', f"{Fore.YELLOW}⚠ {error_msg[self.language]}{Style.RESET_ALL}", self.language)
            
            name_length = len(name)
            if name_length == 3:
                default_fee = self.web3.to_wei(1, 'ether')  # 1 MON cho 3 ký tự
            elif name_length == 4:
                default_fee = self.web3.to_wei(0.3, 'ether')  # 0.3 MON cho 4 ký tự
            else:  # 5 ký tự trở lên
                default_fee = self.web3.to_wei(0.1, 'ether')  # 0.1 MON cho 5+ ký tự
            
            fee_msg = {
                'vi': f"Phí mặc định ({name_length} ký tự): {self.web3.from_wei(default_fee, 'ether')} MON",
                'en': f"Default fee ({name_length} characters): {self.web3.from_wei(default_fee, 'ether')} MON"
            }
            print_step('register', f"{Fore.CYAN}{fee_msg[self.language]}{Style.RESET_ALL}", self.language)
            return default_fee

    async def check_mon_balance(self) -> bool:
        """Kiểm tra số dư MON của ví."""
        messages = {
            'vi': "Đang kiểm tra số dư MON...",
            'en': "Checking MON balance..."
        }
        print_step('check', messages[self.language], self.language)
        try:
            balance = await self.web3.eth.get_balance(self.account.address)
            balance_mon = self.web3.from_wei(balance, 'ether')
            if balance_mon < MIN_MON_BALANCE:
                insufficient_msg = {
                    'vi': f"Số dư MON không đủ: {balance_mon} MON (yêu cầu tối thiểu {MIN_MON_BALANCE} MON)",
                    'en': f"Insufficient MON balance: {balance_mon} MON (minimum required {MIN_MON_BALANCE} MON)"
                }
                print_step('check', f"{Fore.RED}✘ {insufficient_msg[self.language]}{Style.RESET_ALL}", self.language)
                return False
            balance_msg = {
                'vi': f"Số dư MON: {balance_mon} MON",
                'en': f"MON balance: {balance_mon} MON"
            }
            print_step('check', f"{Fore.GREEN}✔ {balance_msg[self.language]}{Style.RESET_ALL}", self.language)
            return True
        except Exception as e:
            error_msg = {
                'vi': f"Lỗi kiểm tra số dư MON: {str(e)}",
                'en': f"Error checking MON balance: {str(e)}"
            }
            print_step('check', f"{Fore.RED}✘ {error_msg[self.language]}{Style.RESET_ALL}", self.language)
            return False

    async def is_name_available(self, name: str) -> bool:
        """Kiểm tra xem tên miền có sẵn không qua API."""
        messages = {
            'vi': f"Đang kiểm tra tính khả dụng của {name}...",
            'en': f"Checking availability of {name}..."
        }
        print_step('check', messages[self.language], self.language)
        signature_data = await self.get_signature(name)
        if signature_data:
            available_msg = {
                'vi': f"Tên miền {name} có sẵn",
                'en': f"Domain {name} is available"
            }
            print_step('check', f"{Fore.GREEN}✔ {available_msg[self.language]}{Style.RESET_ALL}", self.language)
            return True
        else:
            unavailable_msg = {
                'vi': f"Tên miền {name} không có sẵn",
                'en': f"Domain {name} is not available"
            }
            print_step('check', f"{Fore.RED}✘ {unavailable_msg[self.language]}{Style.RESET_ALL}", self.language)
            return False

    async def register_domain(self, name: str) -> bool:
        """Đăng ký tên miền sử dụng hợp đồng thông minh NAD Domains."""
        for retry in range(ATTEMPTS):
            try:
                if not await self.check_mon_balance():
                    return False

                if not await self.is_name_available(name):
                    return False

                signature_data = await self.get_signature(name)
                if not signature_data:
                    return False

                fee = await self.calculate_fee(name)

                register_msg = {
                    'vi': f"Đang đăng ký tên miền {name}...",
                    'en': f"Registering domain {name}..."
                }
                print_step('register', register_msg[self.language], self.language)
                register_data = [
                    name,
                    self.account.address,
                    True,
                    "0x0000000000000000000000000000000000000000",
                    "0x0000000000000000000000000000000000000000000000000000000000000000",
                    "0x0000000000000000000000000000000000000000000000000000000000000000",
                    signature_data['nonce'],
                    signature_data['deadline']
                ]
                signature = signature_data['signature']
                gas_params = await self.get_gas_params()

                gas_estimate = await self.contract.functions.registerWithSignature(
                    register_data, signature
                ).estimate_gas({'from': self.account.address, 'value': fee})
                gas_with_buffer = int(gas_estimate * 1.2)

                transaction = await self.contract.functions.registerWithSignature(
                    register_data, signature
                ).build_transaction({
                    'from': self.account.address,
                    'value': fee,
                    'gas': gas_with_buffer,
                    'nonce': await self.web3.eth.get_transaction_count(self.account.address),
                    'chainId': 10143,
                    'type': 2,
                    **gas_params
                })
                signed_txn = self.web3.eth.account.sign_transaction(transaction, self.private_key)
                tx_hash = await self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)
                receipt = await self.web3.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt['status'] == 1:
                    success_msg = {
                        'vi': f"Đã đăng ký thành công {name}! TX: {EXPLORER_URL}{tx_hash.hex()}",
                        'en': f"Successfully registered {name}! TX: {EXPLORER_URL}{tx_hash.hex()}"
                    }
                    print_step('register', f"{Fore.GREEN}✔ {success_msg[self.language]}{Style.RESET_ALL}", self.language)
                    logger.success(f"[{self.account_index}] {success_msg[self.language]}")
                    return True
                else:
                    fail_msg = {
                        'vi': f"Không thể đăng ký {name}: {EXPLORER_URL}{tx_hash.hex()}",
                        'en': f"Failed to register {name}: {EXPLORER_URL}{tx_hash.hex()}"
                    }
                    print_step('register', f"{Fore.RED}✘ {fail_msg[self.language]}{Style.RESET_ALL}", self.language)
                    return False
            except Exception as e:
                await self._handle_error("register_domain", e)
        fail_msg = {
            'vi': f"Không thể đăng ký {name} sau {ATTEMPTS} lần thử",
            'en': f"Failed to register {name} after {ATTEMPTS} attempts"
        }
        print_step('register', f"{Fore.RED}✘ {fail_msg[self.language]}{Style.RESET_ALL}", self.language)
        return False

    async def has_domain(self) -> bool:
        """Kiểm tra xem ví đã sở hữu tên miền NAD chưa."""
        messages = {
            'vi': "Đang kiểm tra số dư tên miền NAD...",
            'en': "Checking NAD domain balance..."
        }
        print_step('balance', messages[self.language], self.language)
        for retry in range(ATTEMPTS):
            try:
                balance = await self.nft_contract.functions.balanceOf(self.account.address).call()
                if balance > 0:
                    logger.info(f"[{self.account_index}] Wallet owns {balance} NAD domain(s)")
                    has_domain_msg = {
                        'vi': f"Ví đã sở hữu {balance} tên miền NAD",
                        'en': f"Wallet already owns {balance} NAD domain(s)"
                    }
                    print_step('balance', f"{Fore.GREEN}✔ {has_domain_msg[self.language]}{Style.RESET_ALL}", self.language)
                    return True
                no_domain_msg = {
                    'vi': "Ví chưa sở hữu tên miền NAD nào",
                    'en': "Wallet has no NAD domains yet"
                }
                print_step('balance', f"{Fore.YELLOW}⚠ {no_domain_msg[self.language]}{Style.RESET_ALL}", self.language)
                return False
            except Exception as e:
                await self._handle_error("has_domain", e)
        fail_msg = {
            'vi': "Không thể kiểm tra số dư sau nhiều lần thử",
            'en': "Failed to check balance after multiple attempts"
        }
        print_step('balance', f"{Fore.RED}✘ {fail_msg[self.language]}{Style.RESET_ALL}", self.language)
        return False

    async def register_custom_domain(self, custom_name: str) -> bool:
        """Đăng ký tên miền do người dùng cung cấp, hỏi nếu đã có domain."""
        has_existing_domain = await self.has_domain()
        if has_existing_domain:
            question_msg = {
                'vi': "Bạn có muốn đăng ký thêm tên miền không? (y/n)",
                'en': "Do you want to register another domain? (y/n)"
            }
            choice = input(f"{Fore.CYAN}{question_msg[self.language]}: {Style.RESET_ALL}").strip().lower()
            if choice != 'y':
                skip_msg = {
                    'vi': "Bỏ qua đăng ký theo yêu cầu",
                    'en': "Skipping registration as requested"
                }
                print_step('register', f"{Fore.YELLOW}⚠ {skip_msg[self.language]}{Style.RESET_ALL}", self.language)
                return True
        return await self.register_domain(custom_name)

    # Remove the prompt for custom domain name and confirmation when wallet already has a domain
    # Modify the register_random_domain method to skip the confirmation prompt

    async def register_random_domain(self) -> bool:
        """Đăng ký tên miền ngẫu nhiên với logic retry."""
        has_existing_domain = await self.has_domain()
        if has_existing_domain:
            existing_msg = {
                'vi': "Ví đã có tên miền NAD. Tiếp tục đăng ký thêm tên miền ngẫu nhiên.",
                'en': "Wallet already has a NAD domain. Proceeding to register another random domain."
            }
            print_step('register', f"{Fore.YELLOW}⚠ {existing_msg[self.language]}{Style.RESET_ALL}", self.language)
            # No confirmation prompt, just continue with registration

        for retry in range(ATTEMPTS):
            try:
                name = self.generate_random_name()
                logger.info(f"[{self.account_index}] Generated random domain name: {name}")
                print_step('register', f"{Fore.CYAN}Tên miền ngẫu nhiên: {name}{Style.RESET_ALL}", self.language)

                if await self.is_name_available(name):
                    logger.info(f"[{self.account_index}] Domain {name} is available, registering...")
                    if await self.register_domain(name):
                        return True
                else:
                    logger.warning(f"[{self.account_index}] Domain {name} is not available, trying another...")
                    retry_msg = {
                        'vi': f"Tên miền {name} không có sẵn, thử lại...",
                        'en': f"Domain {name} is not available, trying again..."
                    }
                    print_step('register', f"{Fore.YELLOW}⚠ {retry_msg[self.language]}{Style.RESET_ALL}", self.language)

            except Exception as e:
                random_pause = random.uniform(PAUSE_BETWEEN_ACTIONS[0], PAUSE_BETWEEN_ACTIONS[1])
                logger.error(f"[{self.account_index}] Error registering domain (attempt {retry+1}/{ATTEMPTS}): {str(e)}. Sleeping for {random_pause} seconds")
                error_msg = {
                    'vi': f"Lỗi đăng ký (lần {retry+1}/{ATTEMPTS}): {str(e)}. Nghỉ {random_pause:.2f} giây",
                    'en': f"Error registering (attempt {retry+1}/{ATTEMPTS}): {str(e)}. Sleeping for {random_pause:.2f} seconds"
                }
                print_step('register', f"{Fore.RED}✘ {error_msg[self.language]}{Style.RESET_ALL}", self.language)
                await asyncio.sleep(random_pause)

        fail_msg = {
            'vi': "Không thể đăng ký tên miền ngẫu nhiên sau nhiều lần thử",
            'en': "Failed to register a random domain after multiple attempts"
        }
        print_step('register', f"{Fore.RED}✘ {fail_msg[self.language]}{Style.RESET_ALL}", self.language)
        return False

        async def _handle_error(self, action: str, error: Exception) -> None:
            """Xử lý lỗi với pause ngẫu nhiên."""
            pause = random.uniform(*PAUSE_BETWEEN_ACTIONS)
            logger.error(f"[{self.account_index}] Error in {action}: {error}. Sleeping for {pause:.2f}s")
            error_msg = {
                'vi': f"Lỗi: {str(error)}. Thử lại sau {pause:.2f} giây",
                'en': f"Error: {str(error)}. Retrying in {pause:.2f} seconds"
            }
            print_step(action, f"{Fore.RED}✘ {error_msg[self.language]}{Style.RESET_ALL}", self.language)
            await asyncio.sleep(pause)

async def run(language: str) -> None:
    """Chạy script NAD Domains với nhiều private keys từ pvkey.txt."""
    try:
        with open("pvkey.txt", "r") as f:
            private_keys = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logger.error("File pvkey.txt not found!")
        error_msg = {
            'vi': "LỖI: Không tìm thấy file pvkey.txt",
            'en': "ERROR: pvkey.txt not found"
        }
        print_border(error_msg[language], Fore.RED)
        return

    if not private_keys:
        logger.error("No private keys found in pvkey.txt!")
        error_msg = {
            'vi': "LỖI: Không tìm thấy private key trong pvkey.txt",
            'en': "ERROR: No private keys found in pvkey.txt"
        }
        print_border(error_msg[language], Fore.RED)
        return

    print(f"{Fore.GREEN}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")
    print_border("NAD DOMAINS - MONAD TESTNET", Fore.GREEN)
    print(f"{Fore.GREEN}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")
    accounts_msg = {
        'vi': f"Tài khoản / Accounts: {len(private_keys)}",
        'en': f"Accounts / Tài khoản: {len(private_keys)}"
    }
    print(f"{Fore.CYAN}👥 {accounts_msg[language]:^76}{Style.RESET_ALL}")

    auto_msg = {
        'vi': "Chế độ tự động: Đăng ký tên miền ngẫu nhiên cho tất cả tài khoản",
        'en': "Automatic mode: Registering random domains for all accounts"
    }
    print_border(auto_msg[language], Fore.CYAN)

    success_count = 0
    async with aiohttp.ClientSession() as session:
        for idx, private_key in enumerate(private_keys, start=1):
            wallet_short = Account.from_key(private_key).address[:8] + "..."
            account_msg = {
                'vi': f"TÀI KHOẢN {idx}/{len(private_keys)} - {wallet_short}",
                'en': f"ACCOUNT {idx}/{len(private_keys)} - {wallet_short}"
            }
            print_border(account_msg[language], Fore.BLUE)
            nad = NadDomains(idx, private_key, session, language)
            logger.info(f"Processing account {idx}/{len(private_keys)}: {nad.account.address}")

            # Always use random domain registration - no user input
            if await nad.register_random_domain():
                success_count += 1

            if idx < len(private_keys):
                pause = random.uniform(10, 30)
                pause_msg = {
                    'vi': f"Đợi {pause:.2f}s trước tài khoản tiếp theo...",
                    'en': f"Waiting {pause:.2f}s before next account..."
                }
                print(f"{Fore.YELLOW}⏳ {pause_msg[language]:^76}{Style.RESET_ALL}")
                await asyncio.sleep(pause)

    print_completion_message(accounts=len(private_keys), language=language, success_count=success_count)
    
if __name__ == "__main__":
    asyncio.run(run("vi"))  # Chạy mặc định với tiếng Việt
