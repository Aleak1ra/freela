from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
import random
import time
import os
import sys
import threading
from screeninfo import get_monitors
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager
import re

INSTANCIAS_POR_CICLO = 2
SENHA_PADRAO = "SenhaSegura123"
WINDOW_WIDTH = 360
WINDOW_HEIGHT = 640
BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))

DADOS_FILE = os.path.join(BASE_DIR, "names_cpfs_emails.txt")
DADOS_USADOS_FILE = os.path.join(BASE_DIR, "dados_usados.txt")
PROXIES_FILE = os.path.join(BASE_DIR, "proxies.txt")
PROXIES_USADAS_FILE = os.path.join(BASE_DIR, "proxies_usadas.txt")
LINK_FILE = os.path.join(BASE_DIR, "link.txt")
driver_path = ChromeDriverManager().install()

monitor = get_monitors()[0]
screen_width = monitor.width

emails_sucesso = []
emails_falha = []
indice_lock = threading.Lock()
indice_atual = 0

usar_proxy = None  # Controla se vai usar proxy


def agora():
    return datetime.now().strftime("%H:%M:%S")


def gerar_user_agents(qtd=30):
    user_agents = [
        # ... (sua lista, mantida)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.199 Safari/537.36",
        "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6110.102 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.129 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.199 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.70 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 12; Pixel 6 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.89 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 16_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 14_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13.3; rv:114.0) Gecko/20100101 Firefox/114.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:110.0) Gecko/20100101 Firefox/110.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.199 Safari/537.36 Edg/120.0.2210.61",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15",
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


def adicionar_linha_arquivo(arquivo, linha):
    with open(arquivo, "a", encoding="utf-8") as f:
        f.write(linha.strip() + "\n")


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


def perguntar_uso_proxy():
    global usar_proxy
    while True:
        resposta = input("Deseja usar proxy? (S/N): ").strip().lower()
        if resposta in ["s", "n"]:
            usar_proxy = resposta == "s"
            break
        print("Digite S para sim ou N para não.")


def executar_proximo(pos_x):
    global indice_atual
    with indice_lock:
        linhas = ler_arquivo(DADOS_FILE)
        proxies = ler_arquivo(PROXIES_FILE)
        if indice_atual >= len(linhas):
            print(f"[{agora()}] 🛘 Nenhum dado restante para nova tentativa.")
            return
        linha_dados = linhas[indice_atual]
        indice_atual += 1
    try:
        cpf, name, email = linha_dados.split(";")
    except Exception as e:
        print(f"[{agora()}] ⚠️ Erro ao processar dados: {linha_dados} ({e})")
        return

    remover_linha_arquivo(DADOS_FILE, linha_dados)
    adicionar_linha_arquivo(DADOS_USADOS_FILE, linha_dados)

    proxy_usada = None
    if usar_proxy:
        proxies = ler_arquivo(PROXIES_FILE)
        proxy_str = random.choice(proxies) if proxies else None
        if proxy_str:
            proxy_usada = proxy_str
            remover_linha_arquivo(PROXIES_FILE, proxy_usada)
            adicionar_linha_arquivo(PROXIES_USADAS_FILE, proxy_usada)

    executar(cpf, name, email, pos_x, proxy_usada)


def executar(cpf, name, email, pos_x, proxy_usada):
    print(f"\n[{agora()}] 🖥️ Iniciando navegador na posição X={pos_x} com:")
    print(f"   👤 Nome: {name}")
    print(f"   📧 Email: {email}")
    print(f"   🆔 CPF: {cpf}\n")

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

    print(f"   🆔 USER-AGENT: {user_agent}\n")

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

    # >>>>>> ABRA O LINK AQUI <<<<<<
    with open(LINK_FILE, "r", encoding="utf-8") as f:
        link = f.read().strip()
    if not link.startswith("http"):
        link = "https://" + link
    driver.get(link)

    input(f"[{agora()}] 📝 Analise o navegador. Pressione Enter para fechar...")
    driver.quit()


def iniciar_ciclo():
    global indice_atual
    emails_sucesso.clear()
    emails_falha.clear()
    linhas = ler_arquivo(DADOS_FILE)
    proxies = ler_arquivo(PROXIES_FILE)
    indice_atual = 0

    if not linhas:
        print("⚠️ Todos os dados já foram utilizados.")
        return

    if usar_proxy and not proxies:
        print("⚠️ Todas as proxies já foram utilizadas.")
        return

    qtd = INSTANCIAS_POR_CICLO
    threads = []
    for i in range(qtd):
        linhas = ler_arquivo(DADOS_FILE)
        proxies = ler_arquivo(PROXIES_FILE)
        if indice_atual >= len(linhas) or (usar_proxy and not proxies):
            print("🚫 Não há mais dados ou proxies disponíveis.")
            break
        pos_x = (i * WINDOW_WIDTH) % screen_width
        t = threading.Thread(target=executar_proximo, args=(pos_x,))
        t.start()
        threads.append(t)
        time.sleep(1)

    for t in threads:
        t.join()

    print("\n📊 RESUMO DO CICLO:")
    print(f"✅ Sucesso: {len(emails_sucesso)}")
    for email in emails_sucesso:
        print(f"   - {email}")
    print(f"\n❌ Falha: {len(emails_falha)}")
    for email in emails_falha:
        print(f"   - {email}")


def main():
    perguntar_uso_proxy()
    try:
        while True:
            linhas = ler_arquivo(DADOS_FILE)
            proxies = ler_arquivo(PROXIES_FILE)
            if not linhas or (usar_proxy and not proxies):
                break
            iniciar_ciclo()
        print("✅ Todos os cadastros foram processados.")
    except KeyboardInterrupt:
        print(f"\n[{agora()}] 🛑 Execução interrompida com Ctrl+C.")


if __name__ == "__main__":
    main()
