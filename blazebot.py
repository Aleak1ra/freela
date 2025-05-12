import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import random
import time
import os
import threading
from screeninfo import get_monitors
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager

# Instala automaticamente o driver compatível com o Chrome instalado
driver_path = ChromeDriverManager().install()


# Timestamp formatado
def agora():
    return datetime.now().strftime("%H:%M:%S")


# Lista de user agents
user_agents_list = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Mobile Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 14_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
]

# Lê o link do arquivo
with open("link.txt", "r", encoding="utf-8") as f:
    link = f.read().strip()

if not link.startswith("http"):
    raise ValueError("Link inválido no link.txt")

# Lê os CPFs e e-mails do arquivo
with open("names_cpfs_emails.txt", "r", encoding="utf-8") as f:
    linhas = [linha.strip() for linha in f if linha.strip()]

WINDOW_WIDTH = 360
WINDOW_HEIGHT = 640

# Obter largura da tela
monitor = get_monitors()[0]
screen_width = monitor.width

emails_sucesso = []
emails_falha = []


def executar(cpf, name, email, pos_x):
    print(f"\n[{agora()}] 🖥️ Iniciando navegador na posição X={pos_x} com:")
    print(f"   👤 Nome: {name}")
    print(f"   📧 Email: {email}")
    print(f"   🆔 CPF: {cpf}\n")

    user_agent = random.choice(user_agents_list)

    options = uc.ChromeOptions()
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=360,640")
    options.add_argument("--disable-webrtc")  # 🛡️ Evita vazamento via WebRTC
    options.add_argument("--incognito")
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--lang=pt-BR")
    options.add_experimental_option(
        "prefs", {"profile.default_content_setting_values.notifications": 2}
    )

    driver = uc.Chrome(
        driver_executable_path=driver_path,
        options=options,
        headless=False,
        use_subprocess=True,
    )

    # 🛡️ Anti-fingerprint: remover sinal de automação
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
            // Remove navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Fake plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Fake languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['pt-BR', 'pt']
            });

            // Fake screen properties
            Object.defineProperty(window, 'chrome', {
                get: () => true
            });
            """
        },
    )

    driver.set_window_size(WINDOW_WIDTH, WINDOW_HEIGHT)
    driver.set_window_position(pos_x, 0)
    driver.get(link)
    wait = WebDriverWait(driver, 20)

    try:
        print(f"[{agora()}] ✅ Página carregada")

        btn_cookie = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[contains(@class, 'policy-regulation-button-container')]//button[contains(text(), 'ACEITAR TODOS OS COOKIES')]",
                )
            )
        )
        print(f"[{agora()}] 🍪 Aceitando cookies")
        btn_cookie.click()
        time.sleep(1)

        btn_idade = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[contains(@class, 'buttons')]//button[contains(text(), 'Eu tenho mais de 18 anos')]",
                )
            )
        )
        print(f"[{agora()}] 🔞 Confirmando idade")
        btn_idade.click()
        time.sleep(1)

        btn_cadastro = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(@class, 'sign-up') and contains(text(), 'Cadastre-se')]",
                )
            )
        )
        print(f"[{agora()}] 📝 Abrindo modal de cadastro")
        btn_cadastro.click()
        time.sleep(2)

        print(f"[{agora()}] ⌨️ Preenchendo e-mail, senha e CPF")
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(
            email
        )
        wait.until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(
            "SenhaSegura123"
        )

        print(f"[{agora()}] ⌨️ Digitando CPF com ActionChains...")
        cpf_input = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'input[data-testid="national-id"]')
            )
        )
        cpf_input.click()
        time.sleep(0.5)
        actions = ActionChains(driver)
        for char in cpf:
            actions.send_keys(char)
            actions.pause(0.1)
        actions.perform()

        checkbox = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="terms"]'))
        )
        driver.execute_script("arguments[0].click();", checkbox)

        print(f"[{agora()}] 🛡️ Aguardando o CAPTCHA ser resolvido manualmente...")
        WebDriverWait(driver, 180).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Comece já') and not(@disabled)]")
            )
        )
        print(f"[{agora()}] ✅ CAPTCHA resolvido! Enviando cadastro...")

        driver.find_element(By.XPATH, "//button[contains(text(), 'Comece já')]").click()
        print(f"[{agora()}] 🎉 Cadastro finalizado com sucesso para {email}!")
        emails_sucesso.append(email)

    except Exception as e:
        print(f"[{agora()}] ❌ Erro durante o processo com {email}: {e}")
        emails_falha.append(email)

    print(f"[{agora()}] ✅ Navegador finalizado para {email}. Ele permanecerá aberto.")
    input("🔚 Pressione ENTER para encerrar esta aba manualmente...")
    driver.quit()


# Quantas instâncias abrir
indice_atual = 0
total_linhas = len(linhas)


def iniciar_ciclo():
    global indice_atual
    threads = []
    emails_sucesso.clear()
    emails_falha.clear()

    try:
        qtd = int(input("Quantas instâncias deseja abrir neste ciclo? "))
    except ValueError:
        print("❌ Entrada inválida.")
        return True

    if indice_atual >= total_linhas:
        print(
            "⚠️ Todos os dados já foram utilizados. Nenhum ciclo adicional será executado."
        )
        return False

    for i in range(qtd):
        if indice_atual >= total_linhas:
            print("🚫 Não há mais CPFs/emails disponíveis para novo ciclo.")
            break
        cpf, name, email = linhas[indice_atual].split(";")
        pos_x = (i * WINDOW_WIDTH) % screen_width
        t = threading.Thread(target=executar, args=(cpf, name, email, pos_x))
        t.start()
        threads.append(t)
        indice_atual += 1
        time.sleep(1)

    for t in threads:
        t.join()

    print("\n📊 RESUMO DO CICLO:")
    print(f"✅ Cadastros bem-sucedidos: {len(emails_sucesso)}")
    for email in emails_sucesso:
        print(f"   - {email}")

    print(f"\n❌ Cadastros com erro: {len(emails_falha)}")
    for email in emails_falha:
        print(f"   - {email}")

    return True


try:
    while True:
        executado = iniciar_ciclo()
        if not executado:
            break

        resposta = input("\n🔄 Deseja rodar mais um ciclo? (s/n): ").strip().lower()
        if resposta != "s":
            print("✅ Execução finalizada.")
            break

except KeyboardInterrupt:
    print(
        f"\n[{agora()}] 🛑 Execução interrompida com Ctrl+C. Os navegadores continuarão abertos."
    )
    exit(0)
