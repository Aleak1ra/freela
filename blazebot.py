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
indice_lock = threading.Lock()
indice_atual = 0
cadastros_ativos = 0
cadastros_sucesso_necessarios = 0
sucessos_no_ciclo = 0


def executar_proximo(pos_x):
    global indice_atual
    with indice_lock:
        if indice_atual >= len(linhas):
            print(f"[{agora()}] 🛘 Nenhum dado restante para nova tentativa.")
            return
        cpf, name, email = linhas[indice_atual].split(";")
        indice_atual += 1
    executar(cpf, name, email, pos_x, tentativa=1)


def executar(cpf, name, email, pos_x, tentativa=1):
    global sucessos_no_ciclo
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
    options.add_argument("--disable-webrtc")
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

    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt']});
        Object.defineProperty(window, 'chrome', {get: () => true});
        """
        },
    )

    driver.set_window_size(WINDOW_WIDTH, WINDOW_HEIGHT)
    driver.set_window_position(pos_x, 0)
    driver.get(link)
    wait = WebDriverWait(driver, 20)

    try:
        print(f"[{agora()}] ✅ Página carregada")

        wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[contains(@class, 'policy-regulation-button-container')]//button[contains(text(), 'ACEITAR TODOS OS COOKIES')]",
                )
            )
        ).click()
        print(f"[{agora()}] 🍪 Aceitando cookies")
        time.sleep(1)

        wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[contains(@class, 'buttons')]//button[contains(text(), 'Eu tenho mais de 18 anos')]",
                )
            )
        ).click()
        print(f"[{agora()}] 🔞 Confirmando idade")
        time.sleep(1)

        wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(@class, 'sign-up') and contains(text(), 'Cadastre-se')]",
                )
            )
        ).click()
        print(f"[{agora()}] 📝 Abrindo modal de cadastro")
        time.sleep(2)

        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(
            email
        )
        wait.until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(
            "SenhaSegura123"
        )
        print(f"[{agora()}] ⌨️ Preenchendo e-mail e senha")

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
        print(f"[{agora()}] ✉️ Digitando CPF")

        checkbox = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="terms"]'))
        )
        driver.execute_script("arguments[0].click();", checkbox)

        cpf_ja_cadastrado = driver.find_elements(
            By.XPATH,
            "//span[contains(text(), 'O CPF já está cadastrado')] | //div[contains(text(), 'CPF tem problemas judiciais ou está na lista negra.')]",
        )
        if cpf_ja_cadastrado:
            print(
                f"[{agora()}] ⚠️ CPF inválido (já cadastrado ou com problemas judiciais) para {email}. Pulando para o próximo dado..."
            )
            emails_falha.append(email)
            with open("cadastros_falha.txt", "a", encoding="utf-8") as f:
                f.write(f"{cpf};{name};{email}\n")
            driver.quit()
            executar_proximo(pos_x)
            return

        print(f"[{agora()}] 🛡️ Aguardando o CAPTCHA ser resolvido...")
        try:
            WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[contains(text(), 'Comece já') and not(@disabled)]",
                    )
                )
            )
            print(f"[{agora()}] ✅ CAPTCHA resolvido! Enviando cadastro...")
        except Exception:
            print(
                f"[{agora()}] ❌ CAPTCHA não resolvido em 8 segundos para {email}. Reiniciando com os mesmos dados..."
            )
            driver.quit()
            executar(cpf, name, email, pos_x, tentativa)
            return

        botao_comecar = driver.find_element(
            By.XPATH, "//button[contains(text(), 'Comece já')]"
        )
        url_antes = driver.current_url
        botao_comecar.click()
        time.sleep(3)
        url_depois = driver.current_url

        if url_depois != url_antes:
            print(f"[{agora()}] 🎉 Cadastro finalizado com sucesso para {email}!")
            emails_sucesso.append(email)
            with open("cadastros_sucesso.txt", "a", encoding="utf-8") as f:
                f.write(f"{cpf};{name};{email}\n")
            global cadastros_ativos
            cadastros_ativos -= 1
        else:
            if tentativa >= 1:
                print(
                    f"[{agora()}] ❌ Falha persistente no cadastro para {email}. Máximo de tentativas atingido."
                )
                emails_falha.append(email)
                with open("cadastros_falha.txt", "a", encoding="utf-8") as f:
                    f.write(f"{cpf};{name};{email}\n")
                driver.quit()
                executar_proximo(pos_x)
                return
            print(
                f"[{agora()}] ❌ Cadastro pode ter falhado (sem redirecionamento) para {email}. Tentando novamente... (tentativa {tentativa + 1})"
            )
            driver.quit()
            executar(cpf, name, email, pos_x, tentativa + 1)
            return

    except Exception as e:
        print(f"[{agora()}] ❌ Erro durante o processo com {email}: {e}")
        emails_falha.append(email)
        with open("cadastros_falha.txt", "a", encoding="utf-8") as f:
            f.write(f"{cpf};{name};{email}\n")

    print(f"[{agora()}] ✅ Navegador finalizado para {email}. Ele permanecerá aberto.")
    input("🔚 Pressione ENTER para encerrar esta aba manualmente...")
    driver.quit()


def iniciar_ciclo():
    global indice_atual, cadastros_ativos, cadastros_sucesso_necessarios, sucessos_no_ciclo
    emails_sucesso.clear()
    emails_falha.clear()

    try:
        qtd = int(input("Quantas instâncias deseja abrir neste ciclo? "))
    except ValueError:
        print("❌ Entrada inválida.")
        return True

    if indice_atual >= len(linhas):
        print(
            "⚠️ Todos os dados já foram utilizados. Nenhum ciclo adicional será executado."
        )
        return False

    cadastros_ativos = qtd
    cadastros_sucesso_necessarios = qtd
    sucessos_no_ciclo = 0

    for i in range(qtd):
        if indice_atual >= len(linhas):
            print("🚫 Não há mais CPFs/emails disponíveis para novo ciclo.")
            break
        with indice_lock:
            cpf, name, email = linhas[indice_atual].split(";")
            indice_atual += 1
        pos_x = (i * WINDOW_WIDTH) % screen_width
        threading.Thread(target=executar, args=(cpf, name, email, pos_x)).start()
        time.sleep(1)

    while len(emails_sucesso) < cadastros_sucesso_necessarios:
        time.sleep(2)

    print("\n📊 RESUMO DO CICLO:")
    print(f"✅ Cadastros bem-sucedidos: {len(emails_sucesso)}")
    for email in emails_sucesso:
        print(f"   - {email}")

    print(f"\n❌ Cadastros com erro: {len(emails_falha)}")
    for email in emails_falha:
        print(f"   - {email}")

    resposta = input("\n🔄 Deseja rodar mais um ciclo? (s/n): ").strip().lower()
    return resposta == "s"


try:
    while True:
        executado = iniciar_ciclo()
        if not executado:
            resposta = (
                input("\n⚠️ Dados esgotados. Deseja reiniciar do início? (s/n): ")
                .strip()
                .lower()
            )
            if resposta == "s":
                indice_atual = 0
                continue
            else:
                print("✅ Execução finalizada.")
                break
except KeyboardInterrupt:
    print(
        f"\n[{agora()}] 🛑 Execução interrompida com Ctrl+C. Os navegadores continuarão abertos."
    )
    exit(0)
