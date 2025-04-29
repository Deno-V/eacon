import socket
import time

class API:
    def __init__(self,host='127.0.0.1',port=33331,debug=False):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))
        self.debug = debug
        if debug:
            print(f"Connected to {self.host}:{self.port}")

    def disconnect(self):
        self.client_socket.close()

    def set_arg_t(self,x,verbose=True):
        y = self.send_message('[command]arg_t={}'.format(x))
        if verbose:
            print(y)

    def set_arg_max_new_tokens(self,x,verbose=True):
        y = self.send_message('[command]arg_max_new_tokens={}'.format(x))
        if verbose:
            print(y)

    def set_server_debug_true(self,verbose=True):
        y = self.send_message('[command]debug=true')
        if verbose:
            print(y)

    def set_server_debug_false(self,verbose=True):
        y = self.send_message('[command]debug=false')
        if verbose:
            print(y)

    def show_server_status(self,verbose=True):
        y = self.send_message('[command]info')
        if verbose:
            print(y)

    def send_message(self,message):
        # Send the message to the server
        self.client_socket.send(message.encode('utf-8'))
        if self.debug:
            print(f"Sent message: {message}")
        # Receive the response from the server
        try:
            response = self.client_socket.recv(30000).decode('utf-8')
            if response[-1]=='\n':
                response = response[:-1]
            if self.debug:
                print(f"Received response: {response}")
            return response
        except socket.error as e:
            # Handle the case where no data is available yet
            if e.errno == 11 or e.errno == 35:  # errno 11 on Unix, 35 on Windows
                print("No data available yet.")
            else:
                print(f"Error: {e}")
            return None


# 食用方法，用API例如main中的方式
# 或者 「telnet 服务器IP 33331」 直接进入对话模式 ^]后输入q回车退出
def get_api(arg_t=0.03,arg_max_new_tokens=800,host='127.0.0.1',port=33331,debug=False,server_debug=False):
    api = API(host=host,port=port,debug=debug)
    api.set_arg_max_new_tokens(arg_max_new_tokens,verbose=debug)
    api.set_arg_t(arg_t,verbose=debug)
    if server_debug:
        api.set_server_debug_true(verbose=debug)
    else:
        api.set_server_debug_false(verbose=debug)
    if debug:
        api.show_server_status()
    return api



if __name__ == "__main__":
    # Send messages sequentially
    api = get_api(arg_t=2)
    api.set_arg_max_new_tokens(10)
    print(api.send_message('USER: What is the color of clouds? Answer me directly with one color. ASSISTANT:'))
    api.disconnect()