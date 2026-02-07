import os
import sys
import time
import asyncio
import platform
import subprocess
import math
import ctypes

NAME = "Proxy Scraper"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(BASE_DIR, "proxies.txt")
IS_WINDOWS = platform.system().lower() == "windows"
SEM = asyncio.Semaphore(1000)
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

def clear():
    os.system("cls" if IS_WINDOWS else "clear")

def set_title(text):
    if IS_WINDOWS:
        ctypes.windll.kernel32.SetConsoleTitleW(text)

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

HTTP_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
]

HTTPS_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=https",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/https.txt",
]

SOCKS4_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
]

SOCKS5_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
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

async def scrape():
    proxies = []
    async with httpx.AsyncClient(timeout=15, verify=False) as client:
        for proto, sources in ALL_SOURCES:
            for url in sources:
                try:
                    r = await client.get(url)
                    for line in r.text.splitlines():
                        if ":" in line:
                            proxies.append((proto, line.strip()))
                except:
                    pass
    print(gradient(f"[+] Scraped: {len(proxies)}"))
    return proxies

async def check(proto, proxy, client, pbar):
    global checked, good, bad
    proxy_url = f"{proto}://{proxy}"
    try:
        async with SEM:
            r = await client.get(
                "http://httpbin.org/ip",
                proxies={"all://": proxy_url},
                timeout=8
            )
            async with lock:
                if r.status_code == 200:
                    good += 1
                    with open(OUTPUT, "a", encoding="utf-8") as f:
                        f.write(proxy + "\n")
                else:
                    bad += 1
                checked += 1
    except:
        async with lock:
            bad += 1
            checked += 1

    s = speed()
    set_title(f"{NAME} | GOOD {good} BAD {bad} | {s}/s")

    pbar.set_postfix(GOOD=good, BAD=bad, SPEED=f"{s}/s")
    pbar.update(1)

async def run(proxies):
    async with httpx.AsyncClient(verify=False) as client:
        pbar = tqdm(total=len(proxies), ncols=120)
        tasks = [check(proto, proxy, client, pbar) for proto, proxy in proxies]
        await asyncio.gather(*tasks)

async def main():
    clear()
    print(gradient(ASCII))
    print(gradient(NAME+"\n"))

    with open(OUTPUT, "w", encoding="utf-8"):
        pass

    proxies = await scrape()
    await run(proxies)

    print(gradient("\n[+] Done\n"))
    print(f"[+] Saved in {OUTPUT}")

if __name__ == "__main__":
    asyncio.run(main())
