import os
import sys
import asyncio
from colorama import init, Fore, Style
import inquirer

# Khởi tạo colorama
init(autoreset=True)

# Độ rộng viền cố định
BORDER_WIDTH = 80

# Hàm hiển thị viền đẹp mắt
def print_border(text: str, color=Fore.CYAN, width=BORDER_WIDTH):
    text = text.strip()
    if len(text) > width - 4:
        text = text[:width - 7] + "..."  # Cắt dài và thêm "..."
    padded_text = f" {text} ".center(width - 2)
    print(f"{color}┌{'─' * (width - 2)}┐{Style.RESET_ALL}")
    print(f"{color}│{padded_text}│{Style.RESET_ALL}")
    print(f"{color}└{'─' * (width - 2)}┘{Style.RESET_ALL}")

# Hàm hiển thị banner
def _banner():
    banner = r"""


    ███╗░░░███╗░█████╗░███╗░░██╗░█████╗░██████╗░  ████████╗███████╗░██████╗████████╗███╗░░██╗███████╗████████╗
    ████╗░████║██╔══██╗████╗░██║██╔══██╗██╔══██╗  ╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝████╗░██║██╔════╝╚══██╔══╝
    ██╔████╔██║██║░░██║██╔██╗██║███████║██║░░██║  ░░░██║░░░█████╗░░╚█████╗░░░░██║░░░██╔██╗██║█████╗░░░░░██║░░░
    ██║╚██╔╝██║██║░░██║██║╚████║██╔══██║██║░░██║  ░░░██║░░░██╔══╝░░░╚═══██╗░░░██║░░░██║╚████║██╔══╝░░░░░██║░░░
    ██║░╚═╝░██║╚█████╔╝██║░╚███║██║░░██║██████╔╝  ░░░██║░░░███████╗██████╔╝░░░██║░░░██║░╚███║███████╗░░░██║░░░
    ╚═╝░░░░░╚═╝░╚════╝░╚═╝░░╚══╝╚═╝░░╚═╝╚═════╝░  ░░░╚═╝░░░╚══════╝╚═════╝░░░░╚═╝░░░╚═╝░░╚══╝╚══════╝░░░╚═╝░░░


    """
    print(f"{Fore.GREEN}{banner:^80}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")
    print_border("MONAD TESTNET", Fore.GREEN)
    print(f"{Fore.YELLOW}│ {'Liên hệ / Contact'}: {Fore.CYAN}https://t.me/thog099{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}│ {'Replit'}: {Fore.CYAN}Thog{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}│ {'Channel Telegram'}: {Fore.CYAN}https://t.me/thogairdrops{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")


# Hàm xóa màn hình
def _clear():
    os.system('cls' if os.name == 'nt' else 'clear')

# Lựa chọn ngôn ngữ
def select_language():
    while True:
        print(f"{Fore.GREEN}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")
        print_border("CHỌN NGÔN NGỮ / SELECT LANGUAGE", Fore.YELLOW)
        questions = [
            inquirer.List('language',
                          message=f"{Fore.CYAN}Vui lòng chọn / Please select:{Style.RESET_ALL}",
                          choices=[
                              ("1. Tiếng Việt", 'vi'),
                              ("2. English", 'en')
                          ],
                          carousel=True)
        ]
        answer = inquirer.prompt(questions)
        if answer and answer['language'] in ['vi', 'en']:
            return answer['language']
        print(f"{Fore.RED}❌ {'Lựa chọn không hợp lệ / Invalid choice':^76}{Style.RESET_ALL}")

# Định nghĩa hàm chạy cho từng script
async def run_rubic(language: str):
    from scripts.rubic import run as rubic_run
    rubic_run(language)

async def run_magma(language: str):
    from scripts.magma import run as magma_run
    await magma_run(language)

async def run_izumi(language: str):
    from scripts.izumi import run as izumi_run
    await izumi_run(language)

async def run_apriori(language: str):
    from scripts.apriori import run as apriori_run
    await apriori_run(language)

async def run_kintsu(language: str):
    from scripts.kintsu import run as kintsu_run
    await kintsu_run(language)

async def run_bean(language: str):
    from scripts.bean import run as bean_run
    await bean_run(language)

async def run_mono(language: str):
    from scripts.mono import run as mono_run
    await mono_run(language)

async def run_bebop(language: str):
    from scripts.bebop import run as bebop_run
    bebop_run(language)

async def run_ambient(language: str):
    from scripts.ambient import run as ambient_run
    await ambient_run(language)

async def run_uniswap(language: str):
    from scripts.uniswap import run as uniswap_run
    await uniswap_run(language)

async def run_deploy(language: str):
    from scripts.deploy import run as deploy_run
    await deploy_run(language)

async def run_sendtx(language: str):
    from scripts.sendtx import run as sendtx_run
    await sendtx_run(language)

async def run_bima(language: str):
    from scripts.bima import run as bima_run
    await bima_run(language)

async def run_lilchogstars(language: str):
    from scripts.lilchogstars import run as lilchogstars_run
    await lilchogstars_run(language)

async def run_naddomains(language: str):
    from scripts.naddomains import run as naddomains_run
    await naddomains_run(language)
    
async def run_shmonad(language: str):
    from scripts.shmonad import run as shmonad_run
    shmonad_run(language)
    
async def run_frontrunner(language: str):
    from scripts.frontrunner import run as run_frontrunner
    await run_frontrunner(language)

async def run_octoswap(language: str):
    from scripts.octoswap import run as octoswap_run
    await octoswap_run(language)

async def run_madness(language: str):
    from scripts.madness import run as madness_run
    await madness_run(language)

async def run_flapdotsh(language: str):
    from scripts.flapdotsh import run as flapdotsh_run
    await flapdotsh_run(language)

async def run_multiplifi(language: str):
    from scripts.multiplifi import run as multiplifi_run
    await multiplifi_run(language)

async def run_monsternad(language: str):
    from scripts.monsternad import run as monsternad_run
    await monsternad_run(language)

# Danh sách script với ánh xạ trực tiếp
SCRIPT_MAP = {
    "rubic": run_rubic,
    "magma": run_magma,
    "izumi": run_izumi,
    "apriori": run_apriori,
    "kintsu": run_kintsu,
    "bean": run_bean,
    "mono": run_mono,
    "bebop": run_bebop,
    "ambient": run_ambient,
    "uniswap": run_uniswap,
    "deploy": run_deploy,
    "sendtx": run_sendtx,
    "bima": run_bima,
    "lilchogstars": run_lilchogstars,
    "naddomains": run_naddomains,
    "shmonad": run_shmonad,
    "frontrunner": run_frontrunner,
    "octoswap": run_octoswap,
    "madness": run_madness,
    "flapdotsh": run_flapdotsh,
    "multiplifi": run_multiplifi,
    "monsternad": run_monsternad,
    "exit": lambda language: sys.exit(0)
}

def get_available_scripts(language):
    scripts = {
        'vi': [
            {"name": "1. Rubic Swap x Monad Testnet", "value": "rubic"},
            {"name": "2. Magma Staking x Monad Testnet", "value": "magma"},
            {"name": "3. Izumi Swap x Monad Testnet", "value": "izumi"},
            {"name": "4. aPriori Staking x Monad Testnet", "value": "apriori"},
            {"name": "5. Kintsu Staking x Monad Testnet", "value": "kintsu"},
            {"name": "6. Bean Swap x Monad Testnet", "value": "bean"},
            {"name": "7. Monorail Swap x Monad Testnet", "value": "mono"},
            {"name": "8. Bebop Swap x Monad Testnet", "value": "bebop"},
            {"name": "9. Ambient Finance Swap x Monad Testnet", "value": "ambient"},
            {"name": "10. Uniswap Swap x Monad Testnet", "value": "uniswap"},
            {"name": "11. Deploy Contract x Monad Testnet", "value": "deploy"},
            {"name": "12. Send TX ngẫu nhiên hoặc File (address.txt) x Monad Testnet", "value": "sendtx"},
            {"name": "13. Bima Deposit bmBTC x Monad Testnet", "value": "bima"},
            {"name": "14. Mint NFT Lil Chogstars x Monad Testnet", "value": "lilchogstars"},
            {"name": "15. Nad Domains x Monad Testnet", "value": "naddomains"},
            {"name": "16. Shmonad x Monad Testnet", "value": "shmonad"},
            {"name": "17. Chơi Frontrunner ( Shmonad ) x Monad Testnet", "value": "frontrunner"},

            {"name": "18. Octo Swap x Monad Testnet", "value": "octoswap"},
            {"name": "19. Madness Swap x Monad Testnet", "value": "madness"},
            {"name": "20. Flapdotsh Swap x Monad Testnet", "value": "flapdotsh"},
            {"name": "21. Multipli Stake x Monad Testnet", "value": "multiplifi"},
            {"name": "22. Monsternad Whitelist x Monad Testnet", "value": "monsternad"},

           
            {"name": "2x. Thoát", "value": "exit"},
        ],
        'en': [
            {"name": "1. Rubic Swap x Monad Testnet", "value": "rubic"},
            {"name": "2. Magma Staking x Monad Testnet", "value": "magma"},
            {"name": "3. Izumi Swap x Monad Testnet", "value": "izumi"},
            {"name": "4. aPriori Staking x Monad Testnet", "value": "apriori"},
            {"name": "5. Kintsu Staking x Monad Testnet", "value": "kintsu"},
            {"name": "6. Bean Swap x Monad Testnet", "value": "bean"},
            {"name": "7. Monorail Swap x Monad Testnet", "value": "mono"},
            {"name": "8. Bebop Swap x Monad Testnet", "value": "bebop"},
            {"name": "9. Ambient Finance Swap x Monad Testnet", "value": "ambient"},
            {"name": "10. Uniswap Swap x Monad Testnet", "value": "uniswap"},
            {"name": "11. Deploy Contract x Monad Testnet", "value": "deploy"},
            {"name": "12. Send Random TX or File (address.txt) x Monad Testnet", "value": "sendtx"},
            {"name": "13. Bima Deposit bmBTC x Monad Testnet", "value": "bima"},
            {"name": "14. Mint NFT Lil Chogstars x Monad Testnet", "value": "lilchogstars"},
            {"name": "15. Nad Domains x Monad Testnet", "value": "naddomains"},
            {"name": "16. Shmonad x Monad Testnet", "value": "shmonad"},
            {"name": "17. Play Frontrunner ( Shmonad ) x Monad Testnet", "value": "frontrunner"},

            {"name": "18. Octo Swap x Monad Testnet", "value": "octoswap"},
            {"name": "19. Madness Swap x Monad Testnet", "value": "madness"},
            {"name": "20. Flapdotsh Swap x Monad Testnet", "value": "flapdotsh"},
            {"name": "21. Multipli Stake x Monad Testnet", "value": "multiplifi"},
            {"name": "22. Monsternad Whitelist x Monad Testnet", "value": "monsternad"},


            {"name": "2x. Exit", "value": "exit"},
        ]
    }
    return scripts[language]

def run_script(script_func, language):
    """Chạy script bất kể nó là async hay không."""
    if asyncio.iscoroutinefunction(script_func):
        asyncio.run(script_func(language))
    else:
        script_func(language)

def main():
    _clear()
    _banner()
    language = select_language()

    while True:
        _clear()
        _banner()
        print_border("MENU CHÍNH / MAIN MENU", Fore.YELLOW)

        available_scripts = get_available_scripts(language)
        questions = [
            inquirer.List('script',
                          message=f"{Fore.CYAN}{'Chọn script để chạy / Select script to run'}{Style.RESET_ALL}",
                          choices=[script["name"] for script in available_scripts],
                          carousel=True)
        ]
        answers = inquirer.prompt(questions)
        if not answers:
            continue

        selected_script_name = answers['script']
        selected_script_value = next(script["value"] for script in available_scripts if script["name"] == selected_script_name)

        script_func = SCRIPT_MAP.get(selected_script_value)
        if script_func is None:
            print(f"{Fore.RED}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")
            print_border(f"{'Chưa triển khai / Not implemented'}: {selected_script_name}", Fore.RED)
            input(f"{Fore.YELLOW}⏎ {'Nhấn Enter để tiếp tục... / Press Enter to continue...'}{Style.RESET_ALL:^76}")
            continue

        try:
            print(f"{Fore.CYAN}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")
            print_border(f"ĐANG CHẠY / RUNNING: {selected_script_name}", Fore.CYAN)
            run_script(script_func, language)
            print(f"{Fore.GREEN}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")
            print_border(f"{'Hoàn thành / Completed'} {selected_script_name}", Fore.GREEN)
            input(f"{Fore.YELLOW}⏎ {'Nhấn Enter để tiếp tục... / Press Enter to continue...'}{Style.RESET_ALL:^76}")
        except Exception as e:
            print(f"{Fore.RED}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")
            print_border(f"{'Lỗi / Error'}: {str(e)}", Fore.RED)
            input(f"{Fore.YELLOW}⏎ {'Nhấn Enter để tiếp tục... / Press Enter to continue...'}{Style.RESET_ALL:^76}")

if __name__ == "__main__":
    main()
