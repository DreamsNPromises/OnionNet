import socket
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def send_to(host, port, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        
        if isinstance(message, str):
            message = message.encode('utf-8')
        
        print(f"[client] Отправка {len(message)} байт...")
        s.sendall(message)  # Отправляем данные
        
        # Закрываем запись (но оставляем чтение для ответа)
        s.shutdown(socket.SHUT_WR)  # Важно! Говорим серверу, что данных больше не будет
        
        # Ждём подтверждения
        response = s.recv(1024)
        print(f"[client] Ответ сервера: {response.decode('utf-8')}")
        
        # Полное закрытие соединения
        s.close()
        
def listen_on(port, handler):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', port))
        s.listen(1)
        print(f"Ожидаем подключения на порту {port}...")

        while True:
            conn, addr = s.accept()
            with conn:
                print(f"[listen_on] Подключение от {addr}")
                data = b''
                
                try:
                    conn.settimeout(3.0)  # Таймаут на чтение
                    
                    while True:
                        chunk = conn.recv(4096)
                        if not chunk:  # Клиент закрыл соединение
                            break
                        data += chunk
                        print(f"[listen_on] Получено {len(chunk)} байт")
                    
                    if not data:
                        print("[listen_on] Пустое сообщение")
                        continue
                    
                    print(f"[listen_on] Всего данных: {len(data)} байт")
                    
                    # Получаем ответ от handler
                    response = handler(data)
                    
                    # Отправляем ответ или "OK", если ответа нет
                    if response:
                        conn.sendall(response)
                        print(f"[listen_on] Отправлен ответ {len(response)} байт")
                
                except socket.timeout:
                    print(f"[listen_on] Таймаут при чтении от {addr}")
                except ConnectionResetError:
                    print(f"[listen_on] Клиент {addr} разорвал соединение")
                except Exception as e:
                    print(f"[listen_on] Ошибка: {e}")