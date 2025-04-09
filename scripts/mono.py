import os
import asyncio
import aiohttp
from web3 import Web3
from colorama import init, Fore, Style
import random
import time

# Khởi tạo colorama
init(autoreset=True)

# Constants
RPC_URL = "https://testnet-rpc.monad.xyz"
EXPLORER_URL = "https://testnet.monadexplorer.com/tx/0x"
CONTRACT_ADDRESS = "0xC995498c22a012353FAE7eCC701810D673E25794"
API_URL = "https://testnet-pathfinder-v2.monorail.xyz/v1/quote"

# Hàm đọc nhiều private key từ pvkey.txt
def load_private_keys(file_path='pvkey.txt'):
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

# Hàm hiển thị viền đẹp
def print_border(text, color=Fore.CYAN, width=60):
    print(f"{color}┌{'─' * (width - 2)}┐{Style.RESET_ALL}")
    print(f"{color}│ {text:^56} │{Style.RESET_ALL}")
    print(f"{color}└{'─' * (width - 2)}┘{Style.RESET_ALL}")

# Hàm kiểm tra số dư
async def check_balance(wallet_address, language):
    lang = {
        'vi': {
            'checking': "Đang kiểm tra số dư...",
            'balance': "Số dư",
            'insufficient': "Số dư không đủ để thực hiện giao dịch!"
        },
        'en': {
            'checking': "Checking balance...",
            'balance': "Balance",
            'insufficient': "Insufficient balance for transaction!"
        }
    }[language]

    print(f"{Fore.YELLOW}🔍 {lang['checking']}{Style.RESET_ALL}")
    balance = w3.eth.get_balance(wallet_address)
    balance_eth = w3.from_wei(balance, 'ether')
    print(f"{Fore.CYAN}💰 {lang['balance']}: {balance_eth} MONAD{Style.RESET_ALL}")

    if balance < w3.to_wei(0.1, 'ether') + w3.to_wei(0.01, 'ether'):  # 0.1 MON + phí gas dự phòng
        print(f"{Fore.RED}❌ {lang['insufficient']}{Style.RESET_ALL}")
        return False
    return True

# Hàm kiểm tra allowance (new)
async def get_allowance(token_address, owner_address, spender_address):
    # ABI cho phương thức allowance của ERC20
    allowance_abi = [
        {
            "constant": True, 
            "inputs": [
                {"name": "owner", "type": "address"}, 
                {"name": "spender", "type": "address"}
            ], 
            "name": "allowance", 
            "outputs": [{"name": "", "type": "uint256"}], 
            "type": "function"
        }
    ]
    
    token_contract = w3.eth.contract(address=token_address, abi=allowance_abi)
    allowance = token_contract.functions.allowance(owner_address, spender_address).call()
    return allowance

# Hàm approve token (new)
async def approve_token(private_key, token_address, spender_address, amount, language):
    account = w3.eth.account.from_key(private_key)
    wallet_address = account.address
    
    lang = {
        'vi': {
            'approving': "Đang approve token...",
            'success': "Approve thành công!",
            'fail': "Approve thất bại"
        },
        'en': {
            'approving': "Approving token...",
            'success': "Approval successful!",
            'fail': "Approval failed"
        }
    }[language]
    
    # ABI cho phương thức approve của ERC20
    approve_abi = [
        {
            "constant": False, 
            "inputs": [
                {"name": "spender", "type": "address"}, 
                {"name": "amount", "type": "uint256"}
            ], 
            "name": "approve", 
            "outputs": [{"name": "", "type": "bool"}], 
            "type": "function"
        }
    ]
    
    token_contract = w3.eth.contract(address=token_address, abi=approve_abi)
    
    try:
        print(f"{Fore.YELLOW}🔐 {lang['approving']}{Style.RESET_ALL}")
        
        tx = token_contract.functions.approve(
            spender_address,
            amount
        ).build_transaction({
            'from': wallet_address,
            'nonce': w3.eth.get_transaction_count(wallet_address),
            'gas': 100000,
            'gasPrice': w3.eth.gas_price
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            print(f"{Fore.GREEN}✅ {lang['success']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}🔗 Explorer: {EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}❌ {lang['fail']}{Style.RESET_ALL}")
            return False
    except Exception as e:
        print(f"{Fore.RED}❌ {lang['fail']}: {str(e)}{Style.RESET_ALL}")
        return False

# Hàm call API (updated with proper headers)
async def call_api(url, params, language, max_attempts=5):
    lang = {
        'vi': {
            'calling': "Đang gọi API Monorail...",
            'success': "Gọi API thành công!",
            'fail': "Gọi API thất bại"
        },
        'en': {
            'calling': "Calling Monorail API...",
            'success': "API call successful!",
            'fail': "API call failed"
        }
    }[language]
    
    print(f"{Fore.YELLOW}🌐 {lang['calling']}{Style.RESET_ALL}")
    
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'origin': 'https://testnet-preview.monorail.xyz',
        'referer': 'https://testnet-preview.monorail.xyz/',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
    }
    
    for attempt in range(max_attempts):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=10) as response:
                    if response.status != 200:
                        raise Exception(f"[{response.status}] {await response.text()} {url}")
                    
                    result = await response.json()
                    print(f"{Fore.GREEN}✅ {lang['success']}{Style.RESET_ALL}")
                    return result
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ API retry {attempt+1}/{max_attempts}: {str(e)}{Style.RESET_ALL}")
            if attempt < max_attempts - 1:
                await asyncio.sleep(3)  # Wait 3 seconds before retrying
            else:
                print(f"{Fore.RED}❌ {lang['fail']} after {max_attempts} attempts: {str(e)}{Style.RESET_ALL}")
                raise

# Hàm gửi giao dịch (updated with correct API parameters)
async def send_transaction(private_key, language):
    try:
        account = w3.eth.account.from_key(private_key)
        wallet_address = account.address
        wallet_short = wallet_address[:8] + "..."

        lang = {
            'vi': {
                'start': f"Khởi động Monorail cho {wallet_short}",
                'preparing': "Đang chuẩn bị swap MON → WMON...",
                'sending': "Đang gửi giao dịch...",
                'sent': "Giao dịch đã gửi! Đang chờ xác nhận...",
                'success': "Giao dịch thành công!",
                'fail': "Lỗi xảy ra"
            },
            'en': {
                'start': f"Starting Monorail for {wallet_short}",
                'preparing': "Preparing MON → WMON swap...",
                'sending': "Sending transaction...",
                'sent': "Transaction sent! Waiting for confirmation...",
                'success': "Transaction successful!",
                'fail': "Error occurred"
            }
        }[language]

        print_border(lang['start'])
        if not await check_balance(wallet_address, language):
            return

        # Setup tokens for swap - Native MON to WMON
        wmon_address = "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701"  # WMON token
        native_mon = "0x0000000000000000000000000000000000000000"  # Native MON address (zero address)
        mon_amount = 0.1  # Amount to swap: 0.1 MON

        print(f"{Fore.BLUE}🔄 {lang['preparing']}{Style.RESET_ALL}")
        
        # Call API to get transaction data with correct parameters
        try:
            api_params = {
                "amount": str(mon_amount),
                "from": native_mon,  # Native MON (this is the key change)
                "to": wmon_address,  # WMON address
                "slippage": "200",
                "deadline": "300",
                "source": "fe3",
                "sender": wallet_address
            }
            
            api_result = await call_api(API_URL, api_params, language)
            transaction = api_result.get("transaction")
            
            if not transaction:
                print(f"{Fore.RED}❌ No transaction data received from API{Style.RESET_ALL}")
                return
                
            # Build transaction with data from API
            tx = {
                'from': wallet_address,
                'to': w3.to_checksum_address(transaction.get("to")),
                'data': transaction.get("data"),
                'value': int(transaction.get("value"), 16) if isinstance(transaction.get("value"), str) else int(transaction.get("value", 0)),
                'gas': 300000,  # Use a higher gas limit to be safe
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(wallet_address),
            }
            
            print(f"{Fore.CYAN}Transaction details:{Style.RESET_ALL}")
            print(f"{Fore.CYAN}To: {tx['to']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Value: {w3.from_wei(tx['value'], 'ether')} MON{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Gas: {tx['gas']}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error preparing transaction: {str(e)}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Falling back to hardcoded transaction data...{Style.RESET_ALL}")
            # Hardcoded transaction data for MON to WMON swap
            data = "0x96f25cbe0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000760afe86e5de5fa0ee542fc7b7b713e1c5425701000000000000000000000000000000000000000000000000016345785d8a000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000140000000000000000000000000" + wallet_address.replace('0x', '').lower() + "000000000000000000000000000000000000000000000000016345785d8a00000000000000000000000000000000000000000000000000000000000067f648900000000000000000000000000000000000000000000000000000000000000001000000000000000000000000760afe86e5de5fa0ee542fc7b7b713e1c5425701000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000004d0e30db000000000000000000000000000000000000000000000000000000000"
            
            tx = {
                'from': wallet_address,
                'to': CONTRACT_ADDRESS,
                'data': data,
                'value': w3.to_wei(mon_amount, 'ether'),
                'gas': 300000,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(wallet_address),
            }

        # Send transaction
        print(f"{Fore.BLUE}🚀 {lang['sending']}{Style.RESET_ALL}")
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"{Fore.GREEN}✅ {lang['sent']}{Style.RESET_ALL}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            print(f"{Fore.GREEN}🎉 {lang['success']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}🔗 Explorer: {EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}❌ Transaction failed. Status: {receipt.status}{Style.RESET_ALL}")
            return False

    except Exception as e:
        print(f"{Fore.RED}❌ {lang['fail']}: {str(e)}{Style.RESET_ALL}")
        return False

# Hàm chính tương thích với main.py
async def run(language):
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {'MONORAIL - MONAD TESTNET':^56} │{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")

    private_keys = load_private_keys('pvkey.txt')
    if not private_keys:
        return

    print(f"{Fore.CYAN}👥 {'Tài khoản' if language == 'vi' else 'Accounts'}: {len(private_keys)}{Style.RESET_ALL}")

    success_count = 0
    for idx, private_key in enumerate(private_keys, 1):
        wallet_short = w3.eth.account.from_key(private_key).address[:8] + "..."
        print_border(f"TÀI KHOẢN / ACCOUNT {idx}/{len(private_keys)} | {wallet_short}", Fore.CYAN)
        
        if await send_transaction(private_key, language):
            success_count += 1
            
        if idx < len(private_keys):
            delay = random.randint(10, 30)
            print(f"\n{Fore.YELLOW}⏳ {'Đợi' if language == 'vi' else 'Waiting'} {delay} {'giây trước tài khoản tiếp theo...' if language == 'vi' else 'seconds before next account...'}{Style.RESET_ALL}")
            await asyncio.sleep(delay)

    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {'HOÀN TẤT' if language == 'vi' else 'ALL DONE'} - {len(private_keys)} {'TÀI KHOẢN' if language == 'vi' else 'ACCOUNTS'}{' ' * (40 - len(str(len(private_keys))))}│{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {'THÀNH CÔNG' if language == 'vi' else 'SUCCESSFUL'}: {success_count}/{len(private_keys)}{' ' * (40 - len(str(success_count)) - len(str(len(private_keys))))}│{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")

if __name__ == "__main__":
    asyncio.run(run('en'))  # Chạy độc lập với Tiếng Việt mặc định