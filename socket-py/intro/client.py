import socket

# Tạo một socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Kết nối đến server trên cổng 12345
client_socket.connect(('localhost', 12345))

# Nhận dữ liệu từ server
data = client_socket.recv(1024)
print(f"Đã nhận: {data.decode('utf-8')}")

# Đóng kết nối
client_socket.close()