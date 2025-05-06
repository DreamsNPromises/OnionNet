from crypto_utils import generate_rsa_keys

#Разово генерим RSA ключи для входящих сообщений
for name in ["client", "node1", "node2", "server"]:
    generate_rsa_keys(name + '_in')
    
#Разово генерим RSA ключи для исходящих сообщений
for name in ["client", "node1", "node2", "server"]:
    generate_rsa_keys(name + '_out')