"""
Скрипт для получения SSL-сертификата Let's Encrypt через ACME HTTP-01 challenge.
Генерирует файл для проверки, который нужно загрузить на хостинг.
"""
import json, hashlib, base64, time, os, sys
from urllib.request import urlopen, Request
from urllib.error import URLError

# ACME директория Let's Encrypt
DIRECTORY_URL = "https://acme-v02.api.letsencrypt.org/directory"
DOMAIN = "zevs.ltd"
EMAIL = "frolova.bz@gmail.com"

try:
    from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding, utils
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.backends import default_backend
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    import josepy as jose
    from acme import client as acme_client
    from acme import messages, challenges
except ImportError as e:
    print(f"Не хватает модуля: {e}")
    print("Установи: pip install cryptography acme josepy")
    sys.exit(1)

def main():
    print(f"=== Получение SSL для {DOMAIN} ===\n")

    # 1. Генерируем ключ аккаунта
    print("[1/5] Генерирую ключ аккаунта...")
    account_key = jose.JWKRSA(key=rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    ))

    # 2. Подключаемся к Let's Encrypt
    print("[2/5] Подключаюсь к Let's Encrypt...")
    net = acme_client.ClientNetwork(account_key)
    directory = messages.Directory.from_json(
        net.get(DIRECTORY_URL).json()
    )
    acme = acme_client.ClientV2(directory, net)

    # 3. Регистрируем аккаунт
    print("[3/5] Регистрирую аккаунт...")
    reg = messages.NewRegistration.from_data(
        email=EMAIL, terms_of_service_agreed=True
    )
    acme.new_account(reg)

    # 4. Запрашиваем сертификат
    print(f"[4/5] Запрашиваю challenge для {DOMAIN}...")

    # Генерируем CSR
    domain_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    # Сохраняем приватный ключ домена
    key_pem = domain_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open("zevs-ssl-key.pem", "wb") as f:
        f.write(key_pem)
    print("   Приватный ключ сохранён: zevs-ssl-key.pem")

    csr = x509.CertificateSigningRequestBuilder().subject_name(
        x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, DOMAIN)])
    ).sign(domain_key, hashes.SHA256(), default_backend())

    csr_pem = csr.public_bytes(serialization.Encoding.DER)

    # Заказываем сертификат
    order = acme.new_order(csr_pem)

    # Ищем HTTP-01 challenge
    for auth in order.authorizations:
        for challenge in auth.body.challenges:
            if isinstance(challenge.chall, challenges.HTTP01):
                http_challenge = challenge
                break

    # Получаем данные для проверки
    token = http_challenge.chall.token
    key_auth = http_challenge.validation(account_key)
    challenge_path = http_challenge.chall.path  # /.well-known/acme-challenge/TOKEN

    print(f"\n{'='*60}")
    print(f"ВНИМАНИЕ! Нужно загрузить файл на хостинг:")
    print(f"{'='*60}")
    print(f"\n1. В файловом менеджере Beget создай папки:")
    print(f"   .well-known/acme-challenge/")
    print(f"   (внутри public_html)")
    print(f"\n2. Создай файл с именем:")
    print(f"   {token}")
    print(f"\n3. Содержимое файла (скопируй ТОЧНО):")
    print(f"   {key_auth}")
    print(f"\n4. Проверочный URL:")
    print(f"   http://{DOMAIN}{challenge_path}")
    print(f"\n{'='*60}")

    # Сохраняем challenge-файл локально
    os.makedirs(".well-known/acme-challenge", exist_ok=True)
    challenge_file = f".well-known/acme-challenge/{token}"
    with open(challenge_file, "w") as f:
        f.write(key_auth)
    print(f"\nФайл также сохранён локально: {challenge_file}")
    print(f"Загрузи папку .well-known на Beget в public_html")

    input("\nНажми Enter когда загрузишь файл на Beget...")

    # 5. Подтверждаем challenge
    print("\n[5/5] Подтверждаю владение доменом...")
    acme.answer_challenge(http_challenge, http_challenge.response(account_key))

    # Ждём финализации
    print("Жду выпуска сертификата...")
    deadline = time.time() + 120
    order = acme.poll_and_finalize(order, deadline=deadline)

    # Сохраняем сертификат
    cert_pem = order.fullchain_pem
    with open("zevs-ssl-cert.pem", "w") as f:
        f.write(cert_pem)

    print(f"\n{'='*60}")
    print(f"ГОТОВО!")
    print(f"{'='*60}")
    print(f"Сертификат: zevs-ssl-cert.pem")
    print(f"Ключ:       zevs-ssl-key.pem")
    print(f"\nТеперь иди в Beget → Домены → zevs.ltd → Установка сертификата")
    print(f"Вставь содержимое этих файлов в соответствующие поля.")

if __name__ == "__main__":
    main()
