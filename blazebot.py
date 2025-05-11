import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import time
import os
import threading
from screeninfo import get_monitors

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


def executar(cpf, name, email, pos_x):
    user_agent = random.choice(user_agents_list)

    options = uc.ChromeOptions()
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=360,640")
    options.add_argument("--incognito")
    options.add_argument(f"user-agent={user_agent}")
    options.add_experimental_option(
        "prefs", {"profile.default_content_setting_values.notifications": 2}
    )
    options.add_argument("--lang=pt-BR")

    driver = uc.Chrome(options=options, headless=False, use_subprocess=True)
    driver.set_window_size(WINDOW_WIDTH, WINDOW_HEIGHT)
    driver.set_window_position(pos_x, 0)
    driver.get(link)
    wait = WebDriverWait(driver, 20)

    try:
        print("✅ Página carregada")

        btn_cookie = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[contains(@class, 'policy-regulation-button-container')]//button[contains(text(), 'ACEITAR TODOS OS COOKIES')]",
                )
            )
        )
        print("🍪 Aceitando cookies")
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
        print("🔞 Confirmando idade")
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
        print("📝 Abrindo modal de cadastro")
        btn_cadastro.click()
        time.sleep(2)

        print("⌨️ Preenchendo e-mail, senha e CPF")
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(
            email
        )
        wait.until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(
            "SenhaSegura123"
        )
        wait.until(EC.presence_of_element_located((By.NAME, "cpf"))).send_keys(cpf)

        checkbox = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="terms"]'))
        )
        driver.execute_script("arguments[0].click();", checkbox)

        print("🛡️ Aguarde o CAPTCHA ser resolvido manualmente...")
        WebDriverWait(driver, 180).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Comece já') and not(@disabled)]")
            )
        )
        print("✅ CAPTCHA resolvido! Enviando cadastro...")

        driver.find_element(By.XPATH, "//button[contains(text(), 'Comece já')]").click()
        print(f"🎉 Cadastro finalizado com sucesso para {email}!")

    except Exception as e:
        print(f"❌ Erro durante o processo: {e}")

    input("🔚 Pressione ENTER para sair...")
    driver.quit()


qtd = int(input("Quantas instâncias deseja abrir? "))
threads = []

for i in range(min(qtd, len(linhas))):
    cpf, name, email = linhas[i].split(";")
    pos_x = (i * WINDOW_WIDTH) % screen_width
    t = threading.Thread(target=executar, args=(cpf, name, email, pos_x))
    t.start()
    threads.append(t)
    time.sleep(1)

for t in threads:
    t.join()
