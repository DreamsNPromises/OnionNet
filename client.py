import sys
from crypto_utils import decrypt_message, load_private_key, load_public_key, encrypt_message, pack_message, unpack_message
from network_utils import listen_on, send_to

NODE1_PORT = int(sys.argv[1])
CLIENT_PORT = int(sys.argv[2])

def run_client():
    message = "Пофиг, ставьте три"
    print(f"Сообщение: {message}" + "\n")
    #Загружаем все публичные ключи
    layers = [load_public_key(name + '_in') for name in ["node1", "node2", "server"]]
    
    #Загружаем ключи клиента
    client_private_key = load_private_key("client_in")  # Для расшифровки ответов
    #server_public_key = load_public_key("server_out")   # Публичный ключ сервера для ответов

    #Шифруем по очереди для каждого хоста:
    #Сначала для сервера, затем для node(N), затем для node(N-1) и т.д.
    encrypted_message = message
    for public_key in reversed(layers):
        encrypted_symmetric_key, encrypted_message = encrypt_message(public_key, encrypted_message)
        encrypted_message = pack_message(encrypted_symmetric_key, encrypted_message)
        print(f"Зашифрованное сообщение: {encrypted_message}" + "\n")

    #Отправляем на первый узел
    send_to("localhost", NODE1_PORT, encrypted_message)
    
    #Слушаем порт для ответа
    def response_handler(data):
        try:
            # Распаковываем ответ
            enc_key, enc_msg = unpack_message(data)
            
            # Расшифровываем (ключ для ответа - client_in)
            response = decrypt_message(client_private_key, enc_key, enc_msg)
            
            if isinstance(response, bytes):
                response = response.decode('utf-8')
            
            print(f"\n[client] Получен ответ от сервера: {response}")
            
        except Exception as e:
            print(f"[client] Ошибка при обработке ответа: {e}")
            
    # Слушаем ответ
    listen_on(CLIENT_PORT, response_handler)

if __name__ == "__main__":
    run_client()