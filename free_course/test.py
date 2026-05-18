# server = ['Ru', 'EY', 'USA', 'ASIA'] ; server.append('Gemeni top')
# server.pop(0)
# print(len(server[0]))

# server = ['Ru', 'EY', 'USA']

# for s in server:
#     print

servers = ["web-server-01", "db-server-01", "backup-node"]

for server in servers:
    print(f"Подключаюсь к {server}...")
    print(f"Обновление пакетов на {server} завершено.")
    print("---")