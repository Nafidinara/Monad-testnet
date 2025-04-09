import os
import random
import asyncio
from web3 import AsyncWeb3
from eth_account import Account
from colorama import init, Fore, Style
import argparse
import inquirer

# Khởi tạo colorama
init(autoreset=True)

# Hằng số
RPC_URL = "https://testnet-rpc.monad.xyz/"
EXPLORER_URL = "https://testnet.monadexplorer.com/tx/0x"
FRONTRUNNER_CONTRACT = "0x9EaBA701a49adE7525dFfE338f0C7E06Eca7Cf07"
CHAIN_ID = 10143  # Monad testnet chain ID
BALANCE_THRESHOLD = 0.001  # Ngưỡng số dư tối thiểu
DEFAULT_ATTEMPTS = 20  # Giảm mặc định để người dùng dễ nhập
GAS_LIMIT = 180000
BORDER_WIDTH = 80

# ABI cho contract Frontrunner
FRONTRUNNER_ABI = [
    {"type": "function", "name": "frontrun", "inputs": [], "outputs": [], "stateMutability": "nonpayable"},
    {"type": "function", "name": "getScore", "inputs": [{"name": "_address", "type": "address"}], 
     "outputs": [{"name": "", "type": "tuple", "components": [
         {"name": "Address", "type": "address"}, 
         {"name": "Wins", "type": "uint256"}, 
         {"name": "Losses", "type": "uint256"}
     ]}], "stateMutability": "view"}
]

# Khởi tạo Web3
w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(RPC_URL))
contract = w3.eth.contract(address=FRONTRUNNER_CONTRACT, abi=FRONTRUNNER_ABI)

# Hàm hiển thị viền đẹp hơn
def print_border(text: str, color=Fore.CYAN, width=BORDER_WIDTH, icon="★"):
    text = text.strip()
    content_length = len(text) + len(icon) * 2 + 4  # Độ dài text + icon + khoảng cách
    width = max(content_length, BORDER_WIDTH)
    if len(text) > width - 4 - len(icon) * 2:
        text = text[:width - 7 - len(icon) * 2] + "..."
    padding = (width - len(text) - 4 - len(icon) * 2) // 2
    padded_text = " " * padding + f"{icon} {text} {icon}" + " " * padding
    print(f"{color}╔{'═' * (width - 2)}╗{Style.RESET_ALL}")
    print(f"{color}║{padded_text}║{Style.RESET_ALL}")
    print(f"{color}╚{'═' * (width - 2)}╝{Style.RESET_ALL}")

# Hàm hiển thị bước thực hiện với biểu tượng
def print_step(step: str, message: str, lang: str):
    steps = {
        'vi': {
            'check': '🔍 KIỂM TRA',
            'play': '🎲 CHƠI',
            'balance': '💰 SỐ DƯ',
            'input': '📝 NHẬP'
        },
        'en': {
            'check': '🔍 CHECKING',
            'play': '🎲 PLAYING',
            'balance': '💰 BALANCE',
            'input': '📝 INPUT'
        }
    }
    step_text = steps[lang].get(step, step.upper())
    print(f"{Fore.YELLOW}║ {Fore.MAGENTA}{step_text:<15} {Fore.YELLOW}│ {Fore.CYAN}{message}{Style.RESET_ALL}")

# Tải private keys
def load_private_keys(file_path='pvkey.txt'):
    try:
        with open(file_path, 'r') as file:
            keys = [line.strip() for line in file if line.strip()]
        if not keys:
            print(f"{Fore.RED}❌ Không tìm thấy khóa nào trong pvkey.txt{Style.RESET_ALL}")
        return keys
    except FileNotFoundError:
        print(f"{Fore.RED}❌ Không tìm thấy file pvkey.txt{Style.RESET_ALL}")
        return []
    except Exception as e:
        print(f"{Fore.RED}❌ Lỗi khi đọc pvkey.txt: {str(e)}{Style.RESET_ALL}")
        return []

# Hỏi số lần chơi
def ask_attempts(language: str):
    lang_dict = {
        'vi': "Nhập số lần bạn muốn chơi Frontrunner (mặc định 99): ",
        'en': "Enter how many times you want to play Frontrunner (default 99): "
    }
    questions = [
        inquirer.Text('attempts',
                     message=f"{Fore.CYAN}{lang_dict[language]}{Style.RESET_ALL}",
                     default=str(DEFAULT_ATTEMPTS),
                     validate=lambda _, x: x.isdigit() and int(x) > 0)
    ]
    answers = inquirer.prompt(questions)
    return int(answers['attempts']) if answers else DEFAULT_ATTEMPTS

# Phân tích tham số dòng lệnh
def parse_args():
    parser = argparse.ArgumentParser(description="Frontrunner Bot for Monad Testnet")
    parser.add_argument('--gas_price', type=int, default=0, help="Gas price in GWEI")
    parser.add_argument('--interval', type=float, default=1.0, help="Khoảng cách giữa các lần thử (giây)")
    return parser.parse_args()

# Chơi Frontrunner cho một tài khoản
async def play_frontrunner(private_key: str, attempts: int, interval: float, gas_price_gwei: int, language: str):
    lang_dict = {
        'vi': {
            'title': "🎮 CHƠI FRONTRUNNER - MONAD TESTNET",
            'start': "Ví: {}",
            'connect': "✅  Kết nối thành công tới Monad Testnet",
            'connect_fail': "❌  Không thể kết nối tới Monad Testnet",
            'gas': "⛽  Gas price: {} GWEI",
            'balance': "💸 Số dư: {} MON",
            'low_balance': "⚠️ Số dư quá thấp (< {} MON)",
            'score': "🏆 Điểm: Thắng {} - Thua {}",
            'first_time': "🌟 Lần đầu chơi - Chúc may mắn!",
            'nonce': "🔢 Nonce hiện tại: {}",
            'tx_sent': "🚀 Đã gửi TX {} - Hash: {}",
            'success': "✅  Giao dịch thành công!",
            'fail': "❌  Giao dịch thất bại",
            'error': "⚠️ Lỗi: {}",
            'limit': "🏁 Đã hoàn thành {} lượt"
        },
        'en': {
            'title': "🎮 PLAY FRONTRUNNER - MONAD TESTNET",
            'start': "Wallet: {}",
            'connect': "✅  Successfully connected to Monad Testnet",
            'connect_fail': "❌  Failed to connect to Monad Testnet",
            'gas': "⛽  Gas price: {} GWEI",
            'balance': "💸 Balance: {} MON",
            'low_balance': "⚠️ Balance too low (< {} MON)",
            'score': "🏆 Score: Wins {} - Losses {}",
            'first_time': "🌟 First time playing - Good luck!",
            'nonce': "🔢 Current nonce: {}",
            'tx_sent': "🚀 Sent TX {} - Hash: {}",
            'success': "✅  Transaction successful!",
            'fail': "❌  Transaction failed",
            'error': "⚠️ Error: {}",
            'limit': "🏁 Completed {} attempts"
        }
    }
    lang = lang_dict[language]

    account = Account.from_key(private_key)
    wallet = f"{account.address[:6]}...{account.address[-4:]}"
    print_border(lang['start'].format(wallet), Fore.GREEN, icon="🎲")

    # Kiểm tra kết nối
    if not await w3.is_connected():
        print_step('check', f"{Fore.RED}{lang['connect_fail']}{Style.RESET_ALL}", language)
        return
    print_step('check', lang['connect'], language)

    # Thiết lập gas price
    gas_price = gas_price_gwei if gas_price_gwei > 0 else int(await w3.eth.gas_price * 10**-9)
    print_step('check', lang['gas'].format(gas_price), language)

    # Kiểm tra số dư
    balance = w3.from_wei(await w3.eth.get_balance(account.address), 'ether')
    print_step('balance', lang['balance'].format(balance), language)
    if balance < BALANCE_THRESHOLD:
        print_step('balance', f"{Fore.RED}{lang['low_balance'].format(BALANCE_THRESHOLD)}{Style.RESET_ALL}", language)
        return

    # Kiểm tra điểm số
    try:
        _, wins, losses = await contract.functions.getScore(account.address).call()
        if wins > 0 or losses > 0:
            print_step('check', lang['score'].format(wins, losses), language)
        else:
            print_step('check', f"{Fore.YELLOW}{lang['first_time']}{Style.RESET_ALL}", language)
    except Exception as e:
        print_step('check', f"{Fore.RED}{lang['error'].format(str(e))}{Style.RESET_ALL}", language)

    # Vòng lặp chơi
    nonce = await w3.eth.get_transaction_count(account.address)
    print_step('check', lang['nonce'].format(nonce), language)

    for attempt in range(attempts):
        try:
            tx = await contract.functions.frontrun().build_transaction({
                'chainId': CHAIN_ID,
                'gas': GAS_LIMIT,
                'maxPriorityFeePerGas': w3.to_wei('2.5', 'gwei'),
                'maxFeePerGas': w3.to_wei(gas_price, 'gwei'),
                'nonce': nonce
            })

            signed_tx = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = await w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_url = f"{Fore.YELLOW}{EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}"
            print_step('play', lang['tx_sent'].format(nonce, tx_url), language)

            receipt = await w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            status = 'success' if receipt['status'] == 1 else 'fail'
            color = Fore.GREEN if receipt['status'] == 1 else Fore.RED
            print_step('play', f"{color}{lang[status]}{Style.RESET_ALL}", language)

            nonce += 1
            await asyncio.sleep(interval)

        except Exception as e:
            print_step('play', f"{Fore.RED}{lang['error'].format(str(e))}{Style.RESET_ALL}", language)
            nonce += 1
            await asyncio.sleep(interval)

    print_step('play', f"{Fore.GREEN}{lang['limit'].format(attempts)}{Style.RESET_ALL}", language)

# Hàm chính
async def run(language: str = 'vi'):
    args = parse_args()
    private_keys = load_private_keys()
    
    if not private_keys:
        print_border("❌ KHÔNG CÓ TÀI KHOẢN ĐỂ CHƠI" if language == 'vi' else "❌ NO ACCOUNTS TO PLAY", Fore.RED, icon="⚠️")
        return

    # Hỏi số lần chơi
    print_border("🎮 FRONTRUNNER - MONAD TESTNET", Fore.GREEN, icon="⭐")
    print(f"{Fore.GREEN}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")
    attempts = ask_attempts(language)
    print('')
    print_step('input', f"{'Số lần chơi' if language == 'vi' else 'Number of attempts'}: {attempts}", language)
    print(f"\n{Fore.GREEN}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")

    print(f"{Fore.CYAN}👥 {'Số tài khoản' if language == 'vi' else 'Number of accounts'}: {len(private_keys)}{Style.RESET_ALL}")

    for i, pk in enumerate(private_keys, 1):
        print(f"\n{Fore.GREEN}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")
        print_border(f"🎯 TÀI KHOẢN {i}/{len(private_keys)}" if language == 'vi' else f"🎯 ACCOUNT {i}/{len(private_keys)}", Fore.YELLOW, icon="👤")
        await play_frontrunner(pk, attempts, args.interval, args.gas_price, language)
        
        if i < len(private_keys):
            delay = random.randint(10, 30)
            msg = f"⏳ Đợi {delay} giây..." if language == 'vi' else f"⏳ Waiting {delay} seconds..."
            print(f"\n{Fore.YELLOW}{msg}{Style.RESET_ALL}")
            await asyncio.sleep(delay)

    print(f"\n{Fore.GREEN}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")
    print_border("🏆 HOÀN TẤT" if language == 'vi' else "🏆 ALL DONE", Fore.GREEN, icon="🎉")

if __name__ == "__main__":
    asyncio.run(run('en'))
