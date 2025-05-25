from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
import random
import time
import os
import threading
from screeninfo import get_monitors
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager
import re

INSTANCIAS_POR_CICLO = 4
SENHA_PADRAO = "SenhaSegura123"
WINDOW_WIDTH = 360
WINDOW_HEIGHT = 640
DADOS_FILE = "names_cpfs_emails.txt"
DADOS_USADOS_FILE = "dados_usados.txt"
PROXIES_FILE = "proxies.txt"
PROXIES_USADAS_FILE = "proxies_usadas.txt"
LINK_FILE = "link.txt"
driver_path = ChromeDriverManager().install()

monitor = get_monitors()[0]
screen_width = monitor.width

indice_lock = threading.Lock()


def agora():
    return datetime.now().strftime("%H:%M:%S")


def agora_full():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def gerar_user_agents(qtd=30):
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.199 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.70 Mobile Safari/537.36",
        # ... outros user agents ...
    ]
    extra = []
    for i in range(qtd - len(user_agents)):
        base = random.choice(user_agents)
        ua = re.sub(
            r"Chrome/\d+\.\d+\.\d+\.\d+",
            f"Chrome/{random.randint(100,136)}.0.{random.randint(1000,9999)}.{random.randint(10,999)}",
            base,
        )
        ua = re.sub(r"Firefox/\d+\.\d+", f"Firefox/{random.randint(100,135)}.0", ua)
        extra.append(ua)
    user_agents.extend(extra)
    random.shuffle(user_agents)
    return user_agents


user_agents_list = gerar_user_agents(30)


def gerar_accept_header():
    options = [
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "text/html,application/xml;q=0.9,*/*;q=0.8",
        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    ]
    return random.choice(options)


def gerar_accept_language():
    options = [
        "pt-BR,pt;q=0.9",
        "pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3",
        "pt-BR,pt;q=0.7,en-US;q=0.5",
    ]
    return random.choice(options)


def gerar_sec_ch_ua(user_agent):
    if "Chrome" in user_agent or "Chromium" in user_agent:
        match = re.search(r"Chrome/([\d\.]+)", user_agent)
        chrome_ver = match.group(1).split(".")[0] if match else "120"
        sec_ch_ua = f'"Chromium";v="{chrome_ver}", "Google Chrome";v="{chrome_ver}", "Not.A/Brand";v="99"'
        if "Android" in user_agent or "Mobile" in user_agent or "iPhone" in user_agent:
            sec_ch_ua_mobile = "?1"
            if "Android" in user_agent:
                sec_ch_ua_platform = '"Android"'
            elif "iPhone" in user_agent:
                sec_ch_ua_platform = '"iOS"'
            else:
                sec_ch_ua_platform = '"Android"'
        else:
            sec_ch_ua_mobile = "?0"
            if "Windows" in user_agent:
                sec_ch_ua_platform = '"Windows"'
            elif "Mac OS X" in user_agent or "Macintosh" in user_agent:
                sec_ch_ua_platform = '"macOS"'
            else:
                sec_ch_ua_platform = '"Linux"'
    elif "Firefox" in user_agent:
        sec_ch_ua = '"Not.A/Brand";v="99"'
        sec_ch_ua_mobile = "?0"
        sec_ch_ua_platform = '"Windows"' if "Windows" in user_agent else '"Linux"'
    else:
        sec_ch_ua = '"Not.A/Brand";v="99"'
        sec_ch_ua_mobile = "?0"
        sec_ch_ua_platform = '"Windows"'
    return sec_ch_ua, sec_ch_ua_platform, sec_ch_ua_mobile


def random_timezone():
    timezones = [
        "America/Araguaina",
        "America/Bahia",
        "America/Belem",
        "America/Boa_Vista",
        "America/Campo_Grande",
        "America/Cuiaba",
        "America/Eirunepe",
        "America/Fortaleza",
        "America/Maceio",
        "America/Manaus",
        "America/Porto_Velho",
        "America/Recife",
        "America/Rio_Branco",
        "America/Santarem",
        "America/Sao_Paulo",
        "America/Noronha",
    ]
    return random.choice(timezones)


def ler_arquivo(arquivo):
    if not os.path.exists(arquivo):
        with open(arquivo, "w", encoding="utf-8") as f:
            pass
        return []
    with open(arquivo, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    return lines


def remover_linha_arquivo(arquivo, linha_remover):
    with open(arquivo, "r", encoding="utf-8") as f:
        linhas = f.readlines()
    with open(arquivo, "w", encoding="utf-8") as f:
        for l in linhas:
            if l.strip() != linha_remover.strip():
                f.write(l)


def adicionar_bloco_usados(arquivo, usadas):
    if not usadas:
        return
    with open(arquivo, "a", encoding="utf-8") as f:
        f.write(f"\n[{agora_full()}] Usada nesta execução\n")
        for item in usadas:
            f.write(item.strip() + "\n")
        f.write("\n")


def parse_proxy(proxy_str):
    if "@" in proxy_str:
        return proxy_str
    partes = proxy_str.split(":")
    if len(partes) == 4:
        ip, porta, user, senha = partes
        return f"{user}:{senha}@{ip}:{porta}"
    elif len(partes) == 2:
        return proxy_str
    else:
        raise ValueError("Formato de proxy inválido")


def executar(cpf, name, email, pos_x, proxy_usada):
    if user_agents_list:
        user_agent = user_agents_list.pop(random.randrange(len(user_agents_list)))
    else:
        user_agent = gerar_user_agents(1)[0]
    tz = random_timezone()
    accept = gerar_accept_header()
    accept_lang = gerar_accept_language()

    seleniumwire_options = {}
    if proxy_usada:
        proxy_url = parse_proxy(proxy_usada)
        seleniumwire_options["proxy"] = {
            "http": f"http://{proxy_url}",
            "https": f"http://{proxy_url}",
        }

    options = webdriver.ChromeOptions()
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=360,640")
    options.add_argument("--disable-webrtc")
    options.add_argument("--incognito")
    options.add_argument("--app=https://ssl-judge2.api.proxyscrape.com/")
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument(f"--lang={accept_lang}")
    options.add_experimental_option(
        "prefs", {"profile.default_content_setting_values.notifications": 2}
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(driver_path)
    driver = webdriver.Chrome(
        service=service,
        options=options,
        seleniumwire_options=seleniumwire_options,
    )

    sec_ch_ua, sec_ch_ua_platform, sec_ch_ua_mobile = gerar_sec_ch_ua(user_agent)
    driver.header_overrides = {
        "User-Agent": user_agent,
        "Accept": accept,
        "Accept-Language": accept_lang,
        "Sec-CH-UA": sec_ch_ua,
        "Sec-CH-UA-Platform": sec_ch_ua_platform,
        "Sec-CH-UA-Mobile": sec_ch_ua_mobile,
    }

    js_fingerprint = f"""
        Object.defineProperty(navigator, 'userAgent', {{ get: () => '{user_agent}' }});
        Object.defineProperty(navigator, 'plugins', {{get: () => [1, 2, 3, 4, 5]}});
        Object.defineProperty(navigator, 'languages', {{get: () => ['pt-BR', 'pt']}});
        Object.defineProperty(window, 'chrome', {{get: () => true}});
        try {{
          Intl.DateTimeFormat.prototype.resolvedOptions = function() {{ return {{ timeZone: '{tz}' }} }}
        }} catch(e) {{}}
    """
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument", {"source": js_fingerprint}
    )

    driver.set_window_size(WINDOW_WIDTH, WINDOW_HEIGHT)
    driver.set_window_position(pos_x, 0)
    input(f"[{agora()}] 📝 Analise o navegador. Pressione Enter para fechar...")
    driver.quit()


def iniciar_ciclo():
    # Coleta as linhas e proxies do ciclo antes de rodar as threads!
    linhas_ciclo = []
    proxies_ciclo = []
    with indice_lock:
        linhas_todas = ler_arquivo(DADOS_FILE)
        proxies_todas = ler_arquivo(PROXIES_FILE)
        qtd = min(INSTANCIAS_POR_CICLO, len(linhas_todas), len(proxies_todas))
        for i in range(qtd):
            linhas_ciclo.append(linhas_todas[i])
            proxies_ciclo.append(proxies_todas[i])

    threads = []
    for i, (linha_dados, proxy_str) in enumerate(zip(linhas_ciclo, proxies_ciclo)):
        try:
            cpf, name, email = linha_dados.split(";")
        except Exception:
            continue
        pos_x = (i * WINDOW_WIDTH) % screen_width
        # Remove dos arquivos antes de rodar o navegador
        remover_linha_arquivo(DADOS_FILE, linha_dados)
        remover_linha_arquivo(PROXIES_FILE, proxy_str)
        t = threading.Thread(target=executar, args=(cpf, name, email, pos_x, proxy_str))
        t.start()
        threads.append(t)
        time.sleep(1)
    for t in threads:
        t.join()

    # Salva bloco de usados ao final do ciclo
    adicionar_bloco_usados(PROXIES_USADAS_FILE, proxies_ciclo)
    adicionar_bloco_usados(DADOS_USADOS_FILE, linhas_ciclo)


def main():
    with open(LINK_FILE, "r", encoding="utf-8") as f:
        link = f.read().strip()
    try:
        while True:
            linhas = ler_arquivo(DADOS_FILE)
            proxies = ler_arquivo(PROXIES_FILE)
            if not linhas or not proxies:
                break
            iniciar_ciclo()
        print("✅ Todos os cadastros foram processados.")
    except KeyboardInterrupt:
        print(f"\n[{agora()}] 🛑 Execução interrompida com Ctrl+C.")


if __name__ == "__main__":
    main()
