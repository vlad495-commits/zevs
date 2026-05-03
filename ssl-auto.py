import josepy as jose, time, os, datetime, sys
from urllib.request import urlopen
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID
from acme import client as acme_client, messages, challenges

DOMAIN = 'zevs.ltd'
EMAIL = 'frolova.bz@gmail.com'
DIRECTORY_URL = 'https://acme-v02.api.letsencrypt.org/directory'

print(f"=== SSL для {DOMAIN} ===\n")

print("[1] Генерирую ключи...")
account_key = jose.JWKRSA(key=rsa.generate_private_key(65537, 2048, default_backend()))
domain_key = rsa.generate_private_key(65537, 2048, default_backend())

key_pem = domain_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption())
with open('zevs-ssl-key.pem', 'wb') as f:
    f.write(key_pem)

print("[2] Подключаюсь к Let's Encrypt...")
net = acme_client.ClientNetwork(account_key)
directory = messages.Directory.from_json(net.get(DIRECTORY_URL).json())
acme = acme_client.ClientV2(directory, net)
acme.new_account(messages.NewRegistration.from_data(email=EMAIL, terms_of_service_agreed=True))

print("[3] Запрашиваю сертификат...")
csr = x509.CertificateSigningRequestBuilder().subject_name(
    x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, DOMAIN)])
).sign(domain_key, hashes.SHA256(), default_backend())

order = acme.new_order(csr.public_bytes(serialization.Encoding.PEM))

http_challenge = None
for auth in order.authorizations:
    for ch in auth.body.challenges:
        if isinstance(ch.chall, challenges.HTTP01):
            http_challenge = ch
            break

token = http_challenge.chall.encode('token')
key_auth = http_challenge.validation(account_key)
token_str = token.decode() if isinstance(token, bytes) else token
key_auth_str = key_auth.decode() if isinstance(key_auth, bytes) else key_auth

# Проверяем — может файл уже на сервере (от прошлого запуска тот же аккаунт не будет, но попробуем)
check_url = f"http://{DOMAIN}/.well-known/acme-challenge/{token_str}"
print(f"\nПроверяю {check_url}...")

# Ждём пока файл появится на сервере (пользователь загружает)
print(f"\nНовый токен: {token_str}")
print(f"Содержимое: {key_auth_str}")
print(f"\nСохраняю файл локально...")

os.makedirs('.well-known/acme-challenge', exist_ok=True)
# Очищаем старые файлы
for f in os.listdir('.well-known/acme-challenge'):
    os.remove(f'.well-known/acme-challenge/{f}')
with open(f'.well-known/acme-challenge/{token_str}', 'w') as f:
    f.write(key_auth_str)

# Также сохраняем отдельно для удобной загрузки
with open(f'{token_str}', 'w') as f:
    f.write(key_auth_str)

print(f"Файл для загрузки: {token_str}")
print(f"\nЖду появления файла на сервере (проверяю каждые 5 сек)...")

for i in range(60):  # 5 мин макс
    try:
        resp = urlopen(check_url, timeout=10)
        content = resp.read().decode().strip()
        if content == key_auth_str:
            print(f"Файл найден на сервере!")
            break
        else:
            print(f"  Файл найден, но содержимое неверное")
    except:
        pass
    print(f"  Попытка {i+1}/60... жду 5 сек")
    time.sleep(5)
else:
    print("ОШИБКА: файл не появился за 5 минут")
    sys.exit(1)

print("\n[4] Подтверждаю владение доменом...")
acme.answer_challenge(http_challenge, http_challenge.response(account_key))

print("[5] Жду выпуска сертификата...")
deadline = datetime.datetime.now() + datetime.timedelta(seconds=120)
order = acme.poll_and_finalize(order, deadline=deadline)

with open('zevs-ssl-cert.pem', 'w') as f:
    f.write(order.fullchain_pem)

print(f"\n{'='*60}")
print(f"СЕРТИФИКАТ ПОЛУЧЕН!")
print(f"{'='*60}")
print(f"Сертификат: zevs-ssl-cert.pem")
print(f"Ключ: zevs-ssl-key.pem")
print(f"\nТеперь в Beget -> Домены -> zevs.ltd -> Установка сертификата")
print(f"Вставь содержимое этих файлов.")
