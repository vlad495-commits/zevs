import josepy as jose, time, os, datetime, sys, pickle
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID
from acme import client as acme_client, messages, challenges

DOMAIN = 'zevs.ltd'
EMAIL = 'frolova.bz@gmail.com'
DIRECTORY_URL = 'https://acme-v02.api.letsencrypt.org/directory'

print(f"=== SSL DNS-01 для {DOMAIN} ===\n", flush=True)

print("[1] Генерирую ключи...", flush=True)
account_key = jose.JWKRSA(key=rsa.generate_private_key(65537, 2048, default_backend()))
domain_key = rsa.generate_private_key(65537, 2048, default_backend())

key_pem = domain_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption())
with open('zevs-ssl-key.pem', 'wb') as f:
    f.write(key_pem)

print("[2] Подключаюсь к Let's Encrypt...", flush=True)
net = acme_client.ClientNetwork(account_key)
directory = messages.Directory.from_json(net.get(DIRECTORY_URL).json())
acme = acme_client.ClientV2(directory, net)
acme.new_account(messages.NewRegistration.from_data(email=EMAIL, terms_of_service_agreed=True))

print("[3] Запрашиваю сертификат...", flush=True)
csr = x509.CertificateSigningRequestBuilder().subject_name(
    x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, DOMAIN)])
).sign(domain_key, hashes.SHA256(), default_backend())

order = acme.new_order(csr.public_bytes(serialization.Encoding.PEM))

dns_challenge = None
for auth in order.authorizations:
    for ch in auth.body.challenges:
        if isinstance(ch.chall, challenges.DNS01):
            dns_challenge = ch
            break

if not dns_challenge:
    print("DNS-01 challenge не найден!", flush=True)
    sys.exit(1)

# Получаем TXT запись
validation = dns_challenge.validation(account_key)
dns_name = f"_acme-challenge.{DOMAIN}"

print(f"\n{'='*60}", flush=True)
print(f"НУЖНО ДОБАВИТЬ TXT-ЗАПИСЬ В DNS:", flush=True)
print(f"{'='*60}", flush=True)
print(f"Имя:      {dns_name}", flush=True)
print(f"Тип:      TXT", flush=True)
print(f"Значение: {validation}", flush=True)
print(f"{'='*60}", flush=True)

# Сохраняем состояние для второго этапа
with open('acme-state.pkl', 'wb') as f:
    pickle.dump({
        'account_key_pem': account_key.key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption()
        ),
        'domain_key_pem': key_pem,
        'order_url': order.uri,
        'challenge_url': dns_challenge.uri,
        'validation': validation,
        'dns_name': dns_name,
    }, f)

print(f"\nСостояние сохранено в acme-state.pkl", flush=True)
print(f"После добавления TXT-записи запусти: python ssl-dns-finalize.py", flush=True)
