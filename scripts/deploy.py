import os
import asyncio
import time
import json
import random  # Menambahkan import random yang hilang
from web3 import Web3
from solcx import compile_standard, install_solc
from colorama import init, Fore, Style
from faker import Faker  # Menambahkan import Faker

# Khởi tạo colorama
init(autoreset=True)

# Cài đặt phiên bản solc
install_solc('0.8.0')

# Constants
RPC_URL = "https://testnet-rpc.monad.xyz"
EXPLORER_URL = "https://testnet.monadexplorer.com/tx/0x"  # Thêm khai báo biến EXPLORER_URL

# Source code của contract
CONTRACT_SOURCE = """
pragma solidity ^0.8.0;

contract Counter {
    uint256 private count;
    
    event CountIncremented(uint256 newCount);
    
    function increment() public {
        count += 1;
        emit CountIncremented(count);
    }
    
    function getCount() public view returns (uint256) {
        return count;
    }
}
"""

# Hàm đọc nhiều private key từ pvkey.txt
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

# Khởi tạo web3 provider
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Kiểm tra kết nối
if not w3.is_connected():
    print(f"{Fore.RED}❌ Không kết nối được với RPC{Style.RESET_ALL}")
    exit(1)

# Hàm hiển thị viền đẹp mắt
def print_border(text, color=Fore.MAGENTA, width=60):
    print(f"{color}╔{'═' * (width - 2)}╗{Style.RESET_ALL}")
    print(f"{color}║ {text:^56} ║{Style.RESET_ALL}")
    print(f"{color}╚{'═' * (width - 2)}╝{Style.RESET_ALL}")

# Hàm hiển thị bước
def print_step(step, message, lang):
    steps = {
        'vi': {'compile': 'Biên dịch', 'deploy': 'Triển khai'},
        'en': {'compile': 'Compiling', 'deploy': 'Deploying'}
    }
    step_text = steps[lang][step]
    print(f"{Fore.YELLOW}🔸 {Fore.CYAN}{step_text:<15}{Style.RESET_ALL} | {message}")

# Hàm biên dịch contract
def compile_contract(language):
    lang = {
        'vi': {'start': 'Đang biên dịch contract...', 'success': 'Biên dịch contract thành công!'},
        'en': {'start': 'Compiling contract...', 'success': 'Contract compiled successfully!'}
    }[language]

    print_step('compile', lang['start'], language)
    try:
        input_data = {
            "language": "Solidity",
            "sources": {"Counter.sol": {"content": CONTRACT_SOURCE}},
            "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}}}
        }
        compiled_sol = compile_standard(input_data, solc_version="0.8.0")
        contract = compiled_sol['contracts']['Counter.sol']['Counter']
        print_step('compile', f"{Fore.GREEN}✔ {lang['success']}{Style.RESET_ALL}", language)
        return {'abi': contract['abi'], 'bytecode': contract['evm']['bytecode']['object']}
    except Exception as e:
        print_step('compile', f"{Fore.RED}✘ Thất bại / Failed: {str(e)}{Style.RESET_ALL}", language)
        raise

# Hàm deploy contract
async def deploy_contract(private_key, token_name, token_symbol, language):
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:8] + "..."
        lang = {
            'vi': {'start': f'Đang triển khai contract {token_name} ({token_symbol})', 'send': 'Đang gửi giao dịch...', 'success': f'Contract {token_name} triển khai thành công!'},
            'en': {'start': f'Deploying contract {token_name} ({token_symbol})', 'send': 'Sending transaction...', 'success': f'Contract {token_name} deployed successfully!'}
        }[language]

        print_border(f"{lang['start']} | {wallet}", Fore.MAGENTA)
        
        compiled = compile_contract(language)
        abi = compiled['abi']
        bytecode = compiled['bytecode']

        nonce = w3.eth.get_transaction_count(account.address)
        print_step('deploy', f"Nonce: {Fore.CYAN}{nonce}{Style.RESET_ALL}", language)

        contract = w3.eth.contract(abi=abi, bytecode=bytecode)
        tx = contract.constructor().build_transaction({
            'from': account.address,
            'gas': 850000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
        })

        print_step('deploy', lang['send'], language)
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print_step('deploy', f"Tx Hash: {Fore.YELLOW}{EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}", language)
        await asyncio.sleep(2)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
        
        if receipt.status == 1:
            print_step('deploy', f"{Fore.GREEN}✔ {lang['success']}{Style.RESET_ALL}", language)
            print(f"{Fore.CYAN}📌 Địa chỉ contract / Contract Address: {Fore.YELLOW}{receipt.contractAddress}{Style.RESET_ALL}")
            return receipt.contractAddress
        else:
            raise Exception(f"Giao dịch thất bại: Status {receipt.status}, Data: {w3.to_hex(receipt.get('data', b''))}")
    except Exception as e:
        print_step('deploy', f"{Fore.RED}✘ Thất bại / Failed: {str(e)}{Style.RESET_ALL}", language)
        return None

# Chạy vòng lặp deploy cho từng private key
async def run_deploy_cycle(cycles, private_keys, language):
    lang = {
        'vi': "VÒNG LẶP DEPLOY CONTRACT / CONTRACT DEPLOY CYCLE",
        'en': "CONTRACT DEPLOY CYCLE"
    }[language]
    
    # Inisialisasi Faker
    fake = Faker()

    for account_idx, private_key in enumerate(private_keys, 1):
        wallet = w3.eth.account.from_key(private_key).address[:8] + "..."
        print_border(f"🏦 TÀI KHOẢN / ACCOUNT {account_idx}/{len(private_keys)} | {wallet}", Fore.BLUE)

        for i in range(cycles):
            print_border(f"🔄 {lang} {i + 1}/{cycles} | {wallet}", Fore.CYAN)
            
            # Menggunakan Faker untuk nama orang
            person_name = fake.name()
            token_name = f"{person_name} Token"
            # Mengambil 3 huruf pertama dan ubah ke huruf besar
            token_symbol = person_name.replace(' ', '')[:3].upper()
            
            print(f"{Fore.GREEN}➤ {'Nama token' if language == 'vi' else 'Token name'}: {Fore.CYAN}{token_name}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}➤ {'Ký hiệu token' if language == 'vi' else 'Token symbol'}: {Fore.CYAN}{token_symbol}{Style.RESET_ALL}")
            
            # Tidak perlu validasi karena token_name dan token_symbol selalu ada

            await deploy_contract(private_key, token_name, token_symbol, language)
            
            if i < cycles - 1:
                delay = random.randint(4, 6)  # Delay 4-6 giây như trong JS
                print(f"\n{Fore.YELLOW}⏳ {'Đợi' if language == 'vi' else 'Waiting'} {delay} {'giây trước vòng tiếp theo...' if language == 'vi' else 'seconds before next cycle...'}{Style.RESET_ALL}")
                await asyncio.sleep(delay)

        if account_idx < len(private_keys):
            delay = random.randint(4, 6)
            print(f"\n{Fore.YELLOW}⏳ {'Đợi' if language == 'vi' else 'Waiting'} {delay} {'giây trước tài khoản tiếp theo...' if language == 'vi' else 'seconds before next account...'}{Style.RESET_ALL}")
            await asyncio.sleep(delay)

    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {'HOÀN TẤT' if language == 'vi' else 'ALL DONE'}: {cycles} {'VÒNG LẶP CHO' if language == 'vi' else 'CYCLES FOR'} {len(private_keys)} {'TÀI KHOẢN' if language == 'vi' else 'ACCOUNTS'}{' ' * (32 - len(str(cycles)) - len(str(len(private_keys))))}│{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")

# Hàm chính
async def run(language):
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {'DEPLOY CONTRACT - MONAD TESTNET':^56} │{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")

    # Periksa jika Faker terinstall
    try:
        from faker import Faker
        fake_test = Faker()
    except ImportError:
        print(f"{Fore.YELLOW}⚠️ Faker library tidak ditemukan. Menginstall...{Style.RESET_ALL}")
        try:
            import pip
            pip.main(['install', 'faker'])
            print(f"{Fore.GREEN}✔ Faker berhasil diinstall{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Gagal menginstall Faker: {str(e)}{Style.RESET_ALL}")
            print(f"{Fore.RED}❌ Silakan install manual dengan menjalankan 'pip install faker'{Style.RESET_ALL}")
            return

    private_keys = load_private_keys('pvkey.txt')
    if not private_keys:
        return

    print(f"{Fore.CYAN}👥 {'Tài khoản' if language == 'vi' else 'Accounts'}: {len(private_keys)}{Style.RESET_ALL}")

    while True:
        try:
            print_border("🔢 SỐ VÒNG LẶP / NUMBER OF CYCLES", Fore.YELLOW)
            cycles_input = input(f"{Fore.GREEN}➤ {'Nhập số (mặc định 1): ' if language == 'vi' else 'Enter number (default 1): '}{Style.RESET_ALL}")
            cycles = int(cycles_input) if cycles_input.strip() else 1
            if cycles <= 0:
                raise ValueError
            break
        except ValueError:
            print(f"{Fore.RED}❌ {'Vui lòng nhập số hợp lệ!' if language == 'vi' else 'Please enter a valid number!'}{Style.RESET_ALL}")

    start_msg = f"Chạy {cycles} vòng deploy contract cho {len(private_keys)} tài khoản..." if language == 'vi' else f"Running {cycles} contract deploy cycles for {len(private_keys)} accounts..."
    print(f"{Fore.YELLOW}🚀 {start_msg}{Style.RESET_ALL}")
    await run_deploy_cycle(cycles, private_keys, language)

if __name__ == "__main__":
    asyncio.run(run('en'))