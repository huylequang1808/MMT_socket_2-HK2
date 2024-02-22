import socket
# Tạo một socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Lắng nghe trên cổng 12345
server_socket.bind(('localhost', 12345))
server_socket.listen(5)

print("Đang lắng nghe...")

while True:
    # Chấp nhận kết nối từ client
    client_socket, addr = server_socket.accept()
    print(f"Đã kết nối từ {addr}")

    # Gửi dữ liệu đến client
    message = "Xin chào từ máy chủ!"
    client_socket.send(message.encode('utf-8'))

    # Đóng kết nối với client
    client_socket.close()