import sys
from crypto_utils import encrypt_message, load_private_key, decrypt_message, load_public_key, pack_message, unpack_message
from network_utils import listen_on

def run_server():
    private_key = load_private_key("server_in")

    def handler(data):
        try:
            #1. Расшифровываем сообщение
            enc_key, enc_msg = unpack_message(data)
            decrypted_message = decrypt_message(private_key, enc_key, enc_msg)
            
            # Проверяем, что получили строку
            if isinstance(decrypted_message, bytes):
                decrypted_message = decrypted_message.decode('utf-8')
                
            print(f"[server] Расшифровано: {decrypted_message}")
            
            #2. Формируем ответ
            response = f"Ответ на: {decrypted_message}"

            #3. Шифруем ответ для обратного пути
            #Порядок: сначала для node1, потом для node2 (обратный порядок узлов!)
            encrypted_response = response.encode()
            for node_name in ["node2_out", "node1_out", "client_out"]:
                public_key = load_public_key(node_name)
                enc_key, enc_data = encrypt_message(public_key, encrypted_response)
                encrypted_response = pack_message(enc_key, enc_data)

            return encrypted_response
    
        except Exception as e:
            print(f"[server] Ошибка: {e}")

    listen_on(int(sys.argv[1]), handler)


if __name__ == "__main__":
    run_server()