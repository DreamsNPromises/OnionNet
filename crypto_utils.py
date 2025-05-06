import struct
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import os
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

KEYS_DIR = "keys"

def generate_rsa_keys(name, path = KEYS_DIR):
    os.makedirs(path, exist_ok=True)
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    public_key = private_key.public_key()

    priv_path = os.path.join(path, f"{name}_priv.pem")
    pub_path = os.path.join(path, f"{name}_pub.pem")

    #Приватный ключ
    with open(priv_path, "wb") as f:
        f.write(private_key.private_bytes(
            #PEM - формат для записи криптографических данных
            encoding=serialization.Encoding.PEM,
            #Формат для записи приватного ключа
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            #Ключ будет записан без шифрования (без шифрования самого ключа)
            encryption_algorithm=serialization.NoEncryption()
        ))

    #Публичный ключ
    with open(pub_path, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

#Загрузка приватного ключа по его имени
def load_private_key(name, path = KEYS_DIR):
    path = os.path.join(path, f"{name}_priv.pem")
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)

#Загрузка публичного ключа по его имени
def load_public_key(name, path=KEYS_DIR):
    path = os.path.join(path, f"{name}_pub.pem")
    with open(path, "rb") as f:
        return serialization.load_pem_public_key(f.read())
    
'''
В итоге это всё работает так:

1. Сообщения мы шифруем с помощью AES
2. Ключ для AES мы шифруем с помощью RSA, чтобы обеспечить его безопасность
3. Передаём сообщение, зашифрованное AES и его ключ, зашифрованный RSA
'''

#Генерация симметричного ключа AES
def generate_symmetric_key():
    #Генерируем случайные байты размером 32
    return os.urandom(32)

#Шифрование с помощью AES
def encrypt_with_aes(message, key):
    #Генерация случайного IV (инициализационный вектор для AES)
    '''
    IV - случайные данные, которые добавляются перед шифрованием, чтобы сделать итоговый шифротекст разным

    Без него мы будем одно и тоже сообщение шифровать одним и тем же ключом -> будем получать одно и тоже одинаковое зашифрованное сообщение
    '''
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()

    #Забиваем сообщение нулями до размера, кратного блоку (16 байт)
    #Чтобы сработало шифрование в режиме CBC
    padded_message = message + b"\0" * (16 - len(message) % 16)
    
    #Шифруем сообщение
    ciphertext = encryptor.update(padded_message) + encryptor.finalize()

    #Вернем IV и зашифрованное сообщение вместе
    return iv + ciphertext

#Шифрование сообщения с использованием RSA для шифрования симметричного ключа
def encrypt_message(public_key, message):
    #Генерация симметричного ключа AES
    symmetric_key = generate_symmetric_key()
    
    # Если сообщение - строка, кодируем его в байты, если оно уже байты - не делаем ничего
    if isinstance(message, str):
        message = message.encode('utf-8')

    #Шифруем сообщение с использованием AES
    encrypted_message = encrypt_with_aes(message, symmetric_key)

    #Шифруем симметричный ключ с использованием RSA
    encrypted_symmetric_key = public_key.encrypt(
        symmetric_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),  # МГФ1 с SHA256
            algorithm=hashes.SHA256(),  # Алгоритм для хеширования
            label=None  # Необязательный параметр
        )
    )

    return encrypted_symmetric_key, encrypted_message

#Дешифровка с помощью AES
def decrypt_with_aes(encrypted_message, key):
    iv = encrypted_message[:16]  #Первые 16 байт - это IV
    ciphertext = encrypted_message[16:]  #Остальное - это зашифрованное сообщение

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()

    #Дешифруем сообщение
    decrypted_message = decryptor.update(ciphertext) + decryptor.finalize()

    #Убираем добавленные нули
    return decrypted_message.rstrip(b"\0").decode('utf-8')

def decrypt_message(private_key, encrypted_symmetric_key, encrypted_message):
    # Дешифруем AES-ключ
    symmetric_key = private_key.decrypt(
        encrypted_symmetric_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Дешифруем сообщение (возвращаем байты, а не строку!)
    iv = encrypted_message[:16]
    ciphertext = encrypted_message[16:]
    
    cipher = Cipher(algorithms.AES(symmetric_key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    
    decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
    return decrypted_data.rstrip(b"\0")  # Убираем паддинг, но оставляем байты!



#Упаковываем сообщение: длина ключа (4 байта) + сам ключ + сообщение
def pack_message(encrypted_key: bytes, encrypted_message: bytes) -> bytes:
    key_len = struct.pack("!I", len(encrypted_key))  # 4 байта беззнаковое целое (big-endian)
    return key_len + encrypted_key + encrypted_message


#Распаковываем сообщение: сначала читаем 4 байта длины ключа, затем сам ключ, потом сообщение
def unpack_message(data: bytes) -> (bytes, bytes): # type: ignore
    key_len = struct.unpack("!I", data[:4])[0]
    encrypted_key = data[4:4 + key_len]
    encrypted_message = data[4 + key_len:]
    return encrypted_key, encrypted_message



'''
#Шифрование с помощью публичного ключа
def encrypt_message(public_key, message):
    #Если сообщение - строка, то мы его кодируем в байты
    #Иначе оно уже представляется байтами, и нам ничего делать не надо
    if isinstance(message, str):
        message = message.encode('utf-8')

    #Шифруем сообщение с использованием публичного ключа
    #PKCS1v15 - паддинг, то есть добавляет дополнительные данные, чтобы не было уязвимостей (хз чё там под капотом)
    ciphertext = public_key.encrypt(
        message,
        padding.PKCS1v15()
    )

    return ciphertext

#Расшифровка с помощью приватного ключа
def decrypt_message(private_key, ciphertext):
    #Дешифруем сообщение с использованием приватного ключа
    plaintext = private_key.decrypt(
        ciphertext,
        padding.PKCS1v15()
    )

    #Преобразуем обратно в строку
    return plaintext.decode('utf-8')
'''