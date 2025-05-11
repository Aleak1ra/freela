import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import time
import os

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

# Lê o primeiro CPF e e-mail do arquivo
with open("names_cpfs_emails.txt", "r", encoding="utf-8") as f:
    line = f.readline().strip()
    cpf, name, email = line.split(";")

# Randomizar user-agent
user_agent = random.choice(user_agents_list)

# Configurar Chrome invisível
options = uc.ChromeOptions()
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-extensions")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-infobars")
options.add_argument("--window-size=360,640")
# options.add_argument("--app=https://ssl-judge2.api.proxyscrape.com/")
options.add_argument("--incognito")
options.add_argument(f"user-agent={user_agent}")
options.add_experimental_option(
    "prefs", {"profile.default_content_setting_values.notifications": 2}
)
options.add_argument("--lang=pt-BR")

driver = uc.Chrome(options=options, headless=False, use_subprocess=True)
driver.set_window_size(360, 640)
driver.get(link)
wait = WebDriverWait(driver, 20)

try:
    print("✅ Página carregada")

    # Aceitar cookies
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

    # Confirmar maior de idade
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

    # Abrir cadastro
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

    # Preencher dados
    print("⌨️ Preenchendo e-mail, senha e CPF")
    wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(email)
    wait.until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(
        "SenhaSegura123"
    )
    wait.until(EC.presence_of_element_located((By.NAME, "cpf"))).send_keys(cpf)

    # Marcar termos
    checkbox = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="terms"]'))
    )
    driver.execute_script("arguments[0].click();", checkbox)

    # Esperar widget Turnstile aparecer
    print("🛡️ Aguarde o CAPTCHA ser resolvido manualmente...")
    WebDriverWait(driver, 180).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Comece já') and not(@disabled)]")
        )
    )
    print("✅ CAPTCHA resolvido! Enviando cadastro...")

    # Clicar no botão "Comece já"
    driver.find_element(By.XPATH, "//button[contains(text(), 'Comece já')]").click()
    print(f"🎉 Cadastro finalizado com sucesso para {email}!")

except Exception as e:
    print(f"❌ Erro durante o processo: {e}")

input("🔚 Pressione ENTER para sair...")
driver.quit()
