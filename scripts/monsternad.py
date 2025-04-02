import os
import sys
import asyncio
import random
from web3 import Web3
from eth_account import Account
from colorama import init, Fore, Style
import primp

# Khởi tạo colorama
init(autoreset=True)

# Độ rộng viền
BORDER_WIDTH = 80

# Constants
RPC_URL = "https://testnet-rpc.monad.xyz/"
EXPLORER_URL = "https://testnet.monadexplorer.com/tx/0x"
CHAIN_ID = 10143  # Monad testnet chain ID

# Từ vựng song ngữ
LANG = {
    'vi': {
        'title': 'MONSTERNAD WHITELIST - MONAD TESTNET',
        'info': 'Thông tin',
        'found': 'Tìm thấy',
        'wallets': 'ví',
        'processing_wallet': 'XỬ LÝ VÍ',
        'starting_whitelist': 'Bắt đầu thêm vào whitelist...',
        'success': 'Thêm vào whitelist thành công!',
        'already_added': 'Địa chỉ ví đã tồn tại trong whitelist',
        'too_many_requests': 'Quá nhiều yêu cầu. Có thể đã được thêm vào whitelist',
        'failure': 'Thêm vào whitelist thất bại',
        'address': 'Địa chỉ',
        'pausing': 'Tạm nghỉ',
        'completed': 'HOÀN THÀNH: {successful}/{total} VÍ ĐƯỢC THÊM VÀO WHITELIST',
        'error': 'Lỗi',
        'connect_success': 'Thành công: Đã kết nối mạng Monad Testnet',
        'connect_error': 'Không thể kết nối RPC',
        'web3_error': 'Kết nối Web3 thất bại',
        'pvkey_not_found': 'File pvkey.txt không tồn tại',
        'pvkey_empty': 'Không tìm thấy private key hợp lệ',
        'pvkey_error': 'Đọc pvkey.txt thất bại',
        'invalid_key': 'không hợp lệ, bỏ qua',
        'warning_line': 'Cảnh báo: Dòng',
    },
    'en': {
        'title': 'MONSTERNAD WHITELIST - MONAD TESTNET',
        'info': 'Info',
        'found': 'Found',
        'wallets': 'wallets',
        'processing_wallet': 'PROCESSING WALLET',
        'starting_whitelist': 'Starting whitelist process...',
        'success': 'Successfully added to whitelist!',
        'already_added': 'Wallet address already exists in whitelist',
        'too_many_requests': 'Too many requests. Likely already added to whitelist',
        'failure': 'Failed to add to whitelist',
        'address': 'Address',
        'pausing': 'Pausing',
        'completed': 'COMPLETED: {successful}/{total} WALLETS ADDED TO WHITELIST',
        'error': 'Error',
        'connect_success': 'Success: Connected to Monad Testnet',
        'connect_error': 'Failed to connect to RPC',
        'web3_error': 'Web3 connection failed',
        'pvkey_not_found': 'pvkey.txt file not found',
        'pvkey_empty': 'No valid private keys found',
        'pvkey_error': 'Failed to read pvkey.txt',
        'invalid_key': 'is invalid, skipped',
        'warning_line': 'Warning: Line',
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

# Hàm kết nối Web3 (dù không cần thiết cho whitelist, giữ để tương thích)
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

# Hàm thêm ví vào whitelist
async def monsternad_whitelist(private_key: str, wallet_index: int, language: str = 'en') -> bool:
    async with primp.AsyncClient() as session:
        for retry in range(3):  # Giới hạn 3 lần thử
            try:
                wallet = Account.from_key(private_key)
                print(f"{Fore.CYAN}  > {LANG[language]['starting_whitelist']}{Style.RESET_ALL}")

                headers = {
                    "accept": "application/json, text/plain, */*",
                    "content-type": "application/json",
                    "origin": "https://airdrop.monsternad.xyz",
                    "referer": "https://airdrop.monsternad.xyz/",
                }

                json_data = {
                    "address": wallet.address,
                    "chainId": CHAIN_ID,
                }

                response = await session.post(
                    "https://api.monsternad.xyz/wallets",
                    headers=headers,
                    json=json_data,
                )

                if response.status_code >= 200 and response.status_code < 300:
                    if response.json()["address"].lower() == wallet.address.lower():
                        print(f"{Fore.GREEN}  ✔ {LANG[language]['success']}{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}    {LANG[language]['address']:<12}: {wallet.address}{Style.RESET_ALL}")
                        return True

                if "Wallet address already exists" in response.text:
                    print(f"{Fore.GREEN}  ✔ {LANG[language]['already_added']}{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}    {LANG[language]['address']:<12}: {wallet.address}{Style.RESET_ALL}")
                    return True

                if "Too Many Requests" in response.text:
                    print(f"{Fore.YELLOW}  ⚠ {LANG[language]['too_many_requests']}{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}    {LANG[language]['address']:<12}: {wallet.address}{Style.RESET_ALL}")
                    return True

                raise Exception(response.text)

            except Exception as e:
                random_pause = random.uniform(5, 15)
                print(f"{Fore.RED}  ✖ {LANG[language]['failure']} ({retry + 1}/3): {str(e)}. {LANG[language]['pausing']} {random_pause:.2f} {'giây' if language == 'vi' else 'seconds'}{Style.RESET_ALL}")
                await asyncio.sleep(random_pause)
                continue
        print(f"{Fore.RED}  ✖ {LANG[language]['failure']} sau 3 lần thử{Style.RESET_ALL}")
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

    # Kết nối Web3 (tùy chọn, để kiểm tra mạng)
    connect_web3(language)
    print()

    successful_whitelists = 0
    total_wallets = len(private_keys)

    random.shuffle(private_keys)
    for i, (profile_num, private_key) in enumerate(private_keys, 1):
        print_border(f"{LANG[language]['processing_wallet']} {profile_num} ({i}/{len(private_keys)})", Fore.MAGENTA)
        print()
        
        if await monsternad_whitelist(private_key, profile_num, language):
            successful_whitelists += 1
        
        if i < len(private_keys):
            delay = random.uniform(10, 30)
            print(f"{Fore.YELLOW}  ℹ {LANG[language]['pausing']} {delay:.2f} {'giây' if language == 'vi' else 'seconds'}{Style.RESET_ALL}")
            await asyncio.sleep(delay)
        print_separator()
    
    print()
    print_border(f"{LANG[language]['completed'].format(successful=successful_whitelists, total=total_wallets)}", Fore.GREEN)
    print()

if __name__ == "__main__":
    asyncio.run(run('en'))
