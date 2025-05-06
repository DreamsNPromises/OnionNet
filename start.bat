@echo off

REM ===== Задаём порты =====
set NODE1_PORT=5003
set NODE2_PORT=5004
set CLIENT_PORT=5001
set SERVER_PORT=5005

REM Как строятся порты после запуска python node.py port1 port2 port3
REM port1 - порт для входящих запросов (на этом порту node будет принимать данные)
REM port2 - порт для пересылки запросов дальше (куда отправлять данные к серверу)
REM port3 - порт для возврата ответов (куда отправлять ответы назад к клиенту)

REM Или же коротко
REM python node.py <имя> <порт_приёма_запросов> <порт_пересылки_вперёд> <порт_возврата_ответов>

REM Думаю можно ещё круче сделать, но хз как (+ не супер важно)

REM ===== Запускаем узлы =====
start "server" cmd /k "title server && .\venv\Scripts\activate && python server.py %SERVER_PORT%"

start "node1" cmd /k "title node1 && .\venv\Scripts\activate && python node.py node1 %NODE1_PORT% %NODE2_PORT% %CLIENT_PORT%"

start "node2" cmd /k "title node2 && .\venv\Scripts\activate && python node.py node2 %NODE2_PORT% %SERVER_PORT% %NODE1_PORT%"

REM Для клиента порты выглядят вот так:
REM python client.py <порт_отправки_запроса> <порт_ожидания_ответа>

start "client" cmd /k "title client && .\venv\Scripts\activate && python client.py %NODE1_PORT% %CLIENT_PORT%"