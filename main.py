import os
import sys
import time
import asyncio
import platform
import subprocess
import math
import ctypes
import shutil

NAME = "Proxy Scraper"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_CHECKED = os.path.join(BASE_DIR, "proxies.txt")
OUTPUT_UNCHECKED = os.path.join(BASE_DIR, "nocheckproxy.txt")
IS_WINDOWS = platform.system().lower() == "windows"
SEM = asyncio.Semaphore(500)
lock = asyncio.Lock()
checked = 0
good = 0
bad = 0
start = time.time()

ASCII = """
⠀⠀⠀⠀⠀⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢿⣧⠀⠀⠀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢸⣿⣇⠀⢸⣿⣿⣦⣤⣄⣀⣴⣿⣷⠀⠀⠀
⠀⠀⠀⠀⠀⢸⣿⣿⡆⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀
⠀⠀⠀⠀⢀⣼⣿⣿⣧⣿⣿⣿⣿⡟⣿⣿⣿⠻⣿⠂⡀⠀
⠀⠀⠀⣠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣧⣿⣿⣿⣦⣿⣏⠁⠀
⠀⠀⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠏⠀⠀
⠀⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠋⠀⠀⠀
⠀⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡀⠀⠀
⢠⣾⣿⡿⠋⠀⠈⠙⣿⣿⣿⡿⣿⡿⠿⠟⢿⣿⣿⣷⣄⠀
⠈⠿⡿⠃⠀⠀⠀⠀⣿⣿⣿⣧⠀⠀⠀⠀⠀⠉⠻⣿⡿⠂
⠀⠀⠀⠀⠀⠀⠀⠈⢿⡿⠟⠃⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀
"""

MENU = """
╔════════════════════════════════════════╗
║         PROXY SCRAPER MENU             ║
╠════════════════════════════════════════╣
║  [1] Check Proxy                       ║
║  [2] No Check Proxy                    ║
╚════════════════════════════════════════╝
"""

def clear():
    os.system("cls" if IS_WINDOWS else "clear")

def set_title(text):
    if IS_WINDOWS:
        ctypes.windll.kernel32.SetConsoleTitleW(text)

def center_text(text):
    terminal_width = shutil.get_terminal_size().columns
    lines = text.split('\n')
    centered = []
    for line in lines:
        import re
        clean_line = re.sub(r'\033\[[0-9;]+m', '', line)
        padding = (terminal_width - len(clean_line)) // 2
        centered.append(' ' * padding + line)
    return '\n'.join(centered)

def center_vertically():
    terminal_height = shutil.get_terminal_size().lines
    content_lines = len(ASCII.split('\n')) + 8
    padding_lines = (terminal_height - content_lines) // 2
    print('\n' * max(0, padding_lines))

def pip_install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

def ensure(pkg):
    try:
        __import__(pkg)
    except:
        pip_install(pkg)

for pkg in ["httpx", "tqdm", "colorama", "httpx[socks]"]:
    ensure(pkg)

import httpx
from tqdm import tqdm
from colorama import init
init()

RESET = "\033[0m"

def gradient(text, t=None):
    if t is None:
        t = time.time() * 5
    result = ""
    for i, c in enumerate(text):
        wave = math.sin(t + i * 0.2)
        r = int(120 + wave*100)
        g = int(180 + wave*60)
        b = int(255 - wave*140)
        result += f"\033[38;2;{r};{g};{b}m{c}"
    return result + RESET

def log(msg, level="INFO"):
    timestamp = time.strftime("%H:%M:%S")
    colors = {
        "INFO": "\033[36m",
        "SUCCESS": "\033[32m", 
        "WARNING": "\033[33m",
        "ERROR": "\033[31m"
    }
    color = colors.get(level, "\033[37m")
    print(f"{color}[{timestamp}] [{level}]{RESET} {msg}")

HTTP_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http",
    "https://api.openproxylist.xyz/http.txt",
    "https://alexa.lr2b.com/proxylist.txt",
    "https://multiproxy.org/txt_all/proxy.txt",
    "https://proxyspace.pro/http.txt",
    "https://proxyspace.pro/https.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/https.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
    "https://raw.githubusercontent.com/UserR3X/proxy-list/main/online/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/hendrikbgr/Free-Proxy-Repo/master/proxy_list.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-https.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/https.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTP_RAW.txt",
    "https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies_anonymous/http.txt",
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/http.txt",
    "https://raw.githubusercontent.com/almroot/proxylist/master/list.txt",
    "https://raw.githubusercontent.com/aslisk/proxyhttps/main/https.txt",
    "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/HTTP.txt",
    "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/http.txt",
    "https://raw.githubusercontent.com/scidam/proxy-list/master/proxy.list",
    "https://raw.githubusercontent.com/ObcbO/getproxy/master/file/http.txt",
    "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/http/http.txt",
    "https://raw.githubusercontent.com/yuceltoluyag/GoodProxy/main/raw.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/https.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/http_proxies.txt",
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/https_proxies.txt",
    "https://raw.githubusercontent.com/caliphdev/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/https.txt",
    "https://raw.githubusercontent.com/im-razvan/proxy_list/main/http.txt",
    "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/http.txt",
    "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/https.txt",
    "https://raw.githubusercontent.com/Vann-Dev/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/Vann-Dev/proxy-list/main/proxies/https.txt",
    "https://raw.githubusercontent.com/zloi-user/hideip.me/main/http.txt",
    "https://raw.githubusercontent.com/Bardiafa/Proxy-Leecher/main/proxies.txt",
    "https://raw.githubusercontent.com/themiralay/Proxy-List-World/master/data.txt",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://www.proxy-list.download/api/v1/get?type=https",
    "https://www.proxyscan.io/download?type=http",
    "https://www.proxyscan.io/download?type=https",
    "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/https.txt",
    "https://raw.githubusercontent.com/zloi-user/hideip.me/main/https.txt",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "https://raw.githubusercontent.com/rx443/proxy-list/main/online/http.txt",
    "https://raw.githubusercontent.com/rx443/proxy-list/main/online/https.txt",
    "https://raw.githubusercontent.com/casals-ar/proxy-list/main/http",
    "https://raw.githubusercontent.com/casals-ar/proxy-list/main/https",
    "https://raw.githubusercontent.com/Volodichev/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/Volodichev/proxy-list/main/https.txt",
]

HTTPS_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=https&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=https",
    "https://api.openproxylist.xyz/https.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/https.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/https.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/https.txt",
    "https://raw.githubusercontent.com/UserR3X/proxy-list/main/online/https.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/https.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-https.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/https.txt",
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/https.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/https.txt",
    "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/https.txt",
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/https_proxies.txt",
    "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/https.txt",
    "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/https.txt",
    "https://raw.githubusercontent.com/Vann-Dev/proxy-list/main/proxies/https.txt",
    "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/https.txt",
    "https://raw.githubusercontent.com/zloi-user/hideip.me/main/https.txt",
    "https://raw.githubusercontent.com/rx443/proxy-list/main/online/https.txt",
    "https://raw.githubusercontent.com/casals-ar/proxy-list/main/https",
    "https://raw.githubusercontent.com/Volodichev/proxy-list/main/https.txt",
    "https://www.proxy-list.download/api/v1/get?type=https",
    "https://www.proxyscan.io/download?type=https",
    "https://proxyspace.pro/https.txt",
]

SOCKS4_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=10000&country=all",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4",
    "https://api.openproxylist.xyz/socks4.txt",
    "https://proxyspace.pro/socks4.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/socks4.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt",
    "https://raw.githubusercontent.com/UserR3X/proxy-list/main/online/socks4.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks4.txt",
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks4.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks4.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/socks4.txt",
    "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/SOCKS4.txt",
    "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks4.txt",
    "https://raw.githubusercontent.com/ObcbO/getproxy/master/file/socks4.txt",
    "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/socks4/socks4.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks4.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks4/data.txt",
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/socks4_proxies.txt",
    "https://raw.githubusercontent.com/caliphdev/Proxy-List/master/socks4.txt",
    "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/socks4.txt",
    "https://raw.githubusercontent.com/im-razvan/proxy_list/main/socks4.txt",
    "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/Vann-Dev/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks4.txt",
    "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt",
    "https://raw.githubusercontent.com/rx443/proxy-list/main/online/socks4.txt",
    "https://raw.githubusercontent.com/casals-ar/proxy-list/main/socks4",
    "https://raw.githubusercontent.com/Volodichev/proxy-list/main/socks4.txt",
    "https://www.proxy-list.download/api/v1/get?type=socks4",
    "https://www.proxyscan.io/download?type=socks4",
]

SOCKS5_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000&country=all",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5",
    "https://api.openproxylist.xyz/socks5.txt",
    "https://proxyspace.pro/socks5.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/socks5.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
    "https://raw.githubusercontent.com/UserR3X/proxy-list/main/online/socks5.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks5.txt",
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks5.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks5.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/socks5.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/SOCKS5.txt",
    "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks5.txt",
    "https://raw.githubusercontent.com/ObcbO/getproxy/master/file/socks5.txt",
    "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/socks5/socks5.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks5.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks5/data.txt",
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/socks5_proxies.txt",
    "https://raw.githubusercontent.com/caliphdev/Proxy-List/master/socks5.txt",
    "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/socks5.txt",
    "https://raw.githubusercontent.com/im-razvan/proxy_list/main/socks5.txt",
    "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/Vann-Dev/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks5.txt",
    "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
    "https://raw.githubusercontent.com/rx443/proxy-list/main/online/socks5.txt",
    "https://raw.githubusercontent.com/casals-ar/proxy-list/main/socks5",
    "https://raw.githubusercontent.com/Volodichev/proxy-list/main/socks5.txt",
    "https://www.proxy-list.download/api/v1/get?type=socks5",
    "https://www.proxyscan.io/download?type=socks5",
]

ALL_SOURCES = [
    ("http", HTTP_SOURCES),
    ("https", HTTPS_SOURCES),
    ("socks4", SOCKS4_SOURCES),
    ("socks5", SOCKS5_SOURCES),
]

def speed():
    t = time.time() - start
    return int(checked / t) if t > 0 else 0

def loading_animation(duration=1.5):
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        frame = frames[i % len(frames)]
        msg = f"{gradient(frame)} Loading..."
        print(f"\r{center_text(msg)}", end="", flush=True)
        time.sleep(0.08)
        i += 1
    print("\r" + " " * 80 + "\r", end="")

async def fetch_source(client, proto, url, seen, proxies):
    try:
        r = await client.get(url)
        count = 0
        for line in r.text.splitlines():
            line = line.strip()
            if ":" in line and line not in seen:
                seen.add(line)
                proxies.append((proto, line))
                count += 1
        if count > 0:
            log(f"Found {count} proxies from {url.split('/')[2]}", "SUCCESS")
    except:
        pass

async def scrape():
    log("Starting proxy scraping...", "INFO")
    proxies = []
    seen = set()
    
    async with httpx.AsyncClient(timeout=10, verify=False, limits=httpx.Limits(max_connections=150)) as client:
        tasks = []
        for proto, sources in ALL_SOURCES:
            log(f"Scraping {proto.upper()} proxies from {len(sources)} sources...", "INFO")
            for url in sources:
                tasks.append(fetch_source(client, proto, url, seen, proxies))
        
        await asyncio.gather(*tasks)
    
    log(f"Scraped {len(proxies)} unique proxies in total", "SUCCESS")
    return proxies

async def check(proto, proxy, client, pbar):
    global checked, good, bad
    
    try:
        ip, port = proxy.split(":")
        port = int(port)
    except:
        async with lock:
            bad += 1
            checked += 1
        pbar.update(1)
        return
    
    if proto in ["http", "https"]:
        proxy_url = f"http://{proxy}"
        test_url = "http://www.google.com"
    else:
        proxy_url = f"{proto}://{proxy}"
        test_url = "http://www.google.com"
    
    try:
        async with SEM:
            if proto in ["socks4", "socks5"]:
                r = await client.get(
                    test_url,
                    proxy=proxy_url,
                    timeout=15
                )
            else:
                r = await client.get(
                    test_url,
                    proxies={"http://": proxy_url, "https://": proxy_url},
                    timeout=15
                )
            
            if r.status_code in [200, 301, 302]:
                async with lock:
                    good += 1
                    with open(OUTPUT_CHECKED, "a", encoding="utf-8") as f:
                        f.write(f"{proto}://{proxy}\n")
                    checked += 1
                
                s = speed()
                set_title(f"{NAME} | GOOD {good} BAD {bad} | {s}/s")
                pbar.set_postfix(GOOD=good, BAD=bad, SPEED=f"{s}/s")
                pbar.update(1)
                return
    except:
        pass
    
    async with lock:
        bad += 1
        checked += 1
    
    s = speed()
    set_title(f"{NAME} | GOOD {good} BAD {bad} | {s}/s")
    pbar.set_postfix(GOOD=good, BAD=bad, SPEED=f"{s}/s")
    pbar.update(1)

async def run_checked(proxies):
    log("Starting proxy validation...", "INFO")
    async with httpx.AsyncClient(verify=False, limits=httpx.Limits(max_connections=300), follow_redirects=True) as client:
        pbar = tqdm(total=len(proxies), ncols=100, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}')
        tasks = [check(proto, proxy, client, pbar) for proto, proxy in proxies]
        await asyncio.gather(*tasks)
        pbar.close()

async def run_unchecked(proxies):
    log("Saving proxies without checking...", "INFO")
    with open(OUTPUT_UNCHECKED, "w", encoding="utf-8") as f:
        for proto, proxy in proxies:
            f.write(f"{proto}://{proxy}\n")
    log(f"Saved {len(proxies)} unchecked proxies", "SUCCESS")

def show_menu():
    clear()
    center_vertically()
    print(center_text(gradient(ASCII)))
    print(center_text(gradient(NAME)))
    print(center_text(gradient(MENU)))
    print()
    
    while True:
        choice = input(center_text("Choose option [1/2]: ").split('\n')[0]).strip()
        if choice in ["1", "2"]:
            return choice
        print(center_text("Invalid choice! Please enter 1 or 2"))

async def main():
    choice = show_menu()
    
    clear()
    center_vertically()
    print(center_text(gradient(ASCII)))
    print(center_text(gradient(NAME)))
    print(center_text(gradient("=" * 50)))
    print()
    
    loading_animation(1.5)

    if choice == "1":
        with open(OUTPUT_CHECKED, "w", encoding="utf-8"):
            pass
        
        proxies = await scrape()
        print()
        await run_checked(proxies)
        
        print()
        log("Scraping completed!", "SUCCESS")
        log(f"Working proxies: {good}/{checked}", "SUCCESS")
        log(f"Success rate: {(good/checked*100):.2f}%" if checked > 0 else "0%", "INFO")
        log(f"Saved in {OUTPUT_CHECKED}", "INFO")
        print()
    else:
        proxies = await scrape()
        print()
        await run_unchecked(proxies)
        
        print()
        log("Scraping completed!", "SUCCESS")
        log(f"Total proxies saved: {len(proxies)}", "SUCCESS")
        log(f"Saved in {OUTPUT_UNCHECKED}", "INFO")
        print()

if __name__ == "__main__":
    asyncio.run(main())
