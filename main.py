import os, sys, time, asyncio, platform, subprocess, math, ctypes

NAME = "Proxy Scraper"
OUTPUT = "proxies.txt"
IS_WINDOWS = platform.system().lower() == "windows"

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

if IS_WINDOWS:
    for pkg in ["httpx", "tqdm", "colorama"]:
        ensure(pkg)

import httpx
from tqdm import tqdm
from colorama import init
init()

RESET = "\033[0m"

def gradient(text, t=None):
    if t is None:
        t = time.time()*5
    result = ""
    for i, c in enumerate(text):
        wave = math.sin(t + i*0.2)
        r = int(120 + wave*100)
        g = int(180 + wave*60)
        b = int(255 - wave*140)
        result += f"\033[38;2;{r};{g};{b}m{c}"
    return result + RESET

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

checked = 0
good = 0
bad = 0
start = time.time()
lock = asyncio.Lock()
SEM = asyncio.Semaphore(1000)

def speed():
    t = time.time() - start
    return int(checked / t) if t > 0 else 0

def success():
    return (good / checked * 100) if checked else 0

SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTP_RAW.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt",
]


async def scrape():
    proxies = set()
    spinner = ["|", "/", "-", "\\"]
    print()
    print(gradient("[+] Scraping proxies "), end="", flush=True)

    async with httpx.AsyncClient(timeout=15, verify=False) as client:
        tasks = [client.get(url) for url in SOURCES]
        for i, coro in enumerate(asyncio.as_completed(tasks)):
            try:
                r = await coro
                for p in r.text.splitlines():
                    if ":" in p:
                        proxies.add(p.strip())
            except:
                pass
            sys.stdout.write(f"\r{gradient('[+] Scraping proxies ')}{spinner[i % len(spinner)]}")
            sys.stdout.flush()

    sys.stdout.write("\r" + " " * 50 + "\r") 
    print(gradient(f"[+] Total proxies: {len(proxies)}"))
    return list(proxies)


async def check(proxy, client, pbar):
    global checked, good, bad
    try:
        async with SEM:
            r = await client.get("http://httpbin.org/ip", proxies=f"http://{proxy}", timeout=6)
            async with lock:
                if r.status_code == 200:
                    good += 1
                    with open(OUTPUT, "a") as f:
                        f.write(proxy + "\n")
                else:
                    bad += 1
                checked += 1
    except:
        async with lock:
            bad += 1
            checked += 1

    s = speed()
    set_title(f"{NAME} | GOOD {good} BAD {bad} | {s}/s | {success():.1f}%")

    pbar.set_description(gradient(f"[ {checked}/{pbar.total} ]"))
    pbar.set_postfix({
        "GOOD": good,
        "BAD": bad,
        "SPEED": f"{s}/s",
        "SUCCESS": f"{success():.1f}%"
    })
    pbar.update(1)

async def run(proxies):
    async with httpx.AsyncClient(verify=False) as client:
        pbar = tqdm(
            total=len(proxies),
            ascii="░█",
            ncols=120,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"
        )
        tasks = [check(p, client, pbar) for p in proxies]
        await asyncio.gather(*tasks)

async def main():
    clear()
    print(gradient(ASCII))
    print(gradient(NAME + "\n"))

    if os.path.exists(OUTPUT):
        os.remove(OUTPUT)

    proxies = await scrape()
    print(gradient("\n[+] Checking proxies...\n"))
    await run(proxies)
    print(gradient("\n[+] DONE\n"))

asyncio.run(main())
