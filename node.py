import sys
from crypto_utils import encrypt_message, load_private_key, decrypt_message, load_public_key, pack_message, unpack_message
from network_utils import send_to, listen_on

def run_node(name, listen_port, next_port, prev_port):
    #Загружаем приватный ключ узла по его имени
    private_key_in = load_private_key(f"{name}_in")
    public_key_out = load_public_key(f"{name}_out")

    def handler(data):
        print(f"[{name}] Получил данные ({len(data)} байт)")

        #Расшифровываем один слой
        try:
            #1. Распаковываем ключ и сообщение
            enc_key, enc_msg = unpack_message(data)
            print(f"[{name}] Длина ключа: {len(enc_key)}, длина сообщения: {len(enc_msg)}")

            #И расшифровываем
            decrypted_message = decrypt_message(private_key_in, enc_key, enc_msg)
            print(f"[{name}] Расшифровано: {decrypted_message}...")  # Логируем первые 50 символов
            
            #2. Если это запрос (от клиента) -> пересылаем к серверу
            if isinstance(decrypted_message, bytes):
                print(f"[{name}] Пересылаю на порт {next_port}")
                send_to("localhost", next_port, decrypted_message)

            #3. Если это ответ (от сервера) -> пересылаем назад
            else:
                # Шифруем для предыдущего узла
                print(f"[{name}] Возвращаю ответ на порт {prev_port}")
                encrypted_response = encrypt_message(public_key_out, decrypted_message.decode('utf-8'))
                send_to("localhost", prev_port, pack_message(*encrypted_response))
            
            '''
            # Проверяем, что это байты (а не строка)
            if isinstance(decrypted_message, str):
                print(f"[{name}] Ошибка: получена строка, ожидались байты")
                return

            print(f"[{name}] Пересылаем {len(decrypted_message)} байт на порт {next_port}...")
            send_to("localhost", next_port, decrypted_message)
            '''
        except Exception as e:
            print(f"[{name}] Ошибка при расшифровке: {e}")
            return

    #Слушаем порт
    print(f"[{name}] Слушаю порт {listen_port}, пересылаю на {next_port}, возвращаю на {prev_port}")
    listen_on(listen_port, handler)

if __name__ == "__main__":
    _, name, listen_port, next_port, prev_port = sys.argv
    run_node(name, int(listen_port), int(next_port), int(prev_port))