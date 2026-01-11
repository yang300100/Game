import socket
import threading

SERVER_HOST_MAIN = "192.168.16.112"
SERVER_PORT_MAIN = 9999
BUFFER_SIZE = 1024
ENCODING = "utf-8"

def recv_message(client_socket):
    while True:
        try:
            msg = client_socket.recv(BUFFER_SIZE).decode(ENCODING)
            if not msg:
                print("\n与游戏服务器断开连接！")
                break
            print(f"{msg}",end="")
        except Exception as e:
            print(f"\n网络异常，连接断开：{e}")
            break
    client_socket.close()
    exit()

def main():
    SERVER_HOST = input("请输入游戏服务器IP: ")
    if not SERVER_HOST:
        SERVER_HOST = SERVER_HOST_MAIN
    SERVER_PORT = input("请输入游戏服务器端口(可不填): ")
    if not SERVER_PORT:
        SERVER_PORT = SERVER_PORT_MAIN
    SERVER_PORT = int(SERVER_PORT)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # 连接服务端
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        print("=====================================")
        print(f"成功连接游戏服务器")
        print(f"服务器地址：{SERVER_HOST}:{SERVER_PORT}")
        print(f"提示：输入内容按【回车】发送，断开连接直接关闭窗口")
        print("=====================================")

        recv_thread = threading.Thread(target=recv_message, args=(client_socket,), daemon=True)
        recv_thread.start()

        print("选项前有数字时填写选项前的数字，选项前无数字时直接填写选项")

        while True:
            user_input = input()
            if user_input.strip():  # 过滤空输入，避免发送空消息
                client_socket.send(user_input.encode(ENCODING))

    except ConnectionRefusedError:
        # 连接失败的常见原因，一站式排查
        print("连接游戏服务器失败！请检查：")
        print("1. 服务端是否已经启动")
        print("2. SERVER_HOST 是否是服务端的真实局域网IP")
        print("3. 服务端电脑是否关闭了防火墙，是否同局域网")
    except Exception as e:
        print(f"客户端异常：{e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()