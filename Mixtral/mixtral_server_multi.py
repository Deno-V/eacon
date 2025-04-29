import signal
import sys
import socket
import time
from transformers import LlamaTokenizer, LlamaForCausalLM, AutoModelForCausalLM, AutoTokenizer
import torch
import os
import threading 
import pickle
import copy
server_socket = None
threads = []

model_lock = threading.Lock()
thread_pool_lock = threading.Lock()

def signal_handler(sig, frame):
    # Handle Ctrl+C outside the main loop
    print("\nServer interrupted in main thread. Closing connections...")
    global server_socket,threads
    for thread in threads:
        thread.terminate()
        print(f'Set close for {thread.client_address}')
    for thread in threads:
        thread.join()
        print(f'Joined {thread.client_address}')
    if server_socket:
        server_socket.close()
        time.sleep(2)
        print("Server socket closed.")
    sys.exit(0)

def dealwithsystem(x):
    # assert len(x)>=2
    if x[0]['role'] != 'system':
        return x
    else:
        nx = copy.deepcopy(x)
        systemprompt = nx.pop(0)['content'] + '\n'
        nx[0]['content'] =  systemprompt + nx[0]['content']
        return nx

class MyWrapLlamaTokenizer:
    def __init__(self,path,max_length=999):
        print('load tokenizer from:',path)
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        self.max_length = max_length
        # debug
        print("tokenizer_max_length: {}".format(max_length))
        self.tokenizer.padding_side = 'left'
        self.tokenizer.pad_token = '<pad>'
    def decode(self,*args,**kwds):
        return self.tokenizer.decode(*args,**kwds)
    def apply_chat_template(self,*args,**kwds):
        return self.tokenizer.apply_chat_template(*args,**kwds)
    def __call__(self, *args, **kwds):
        # print(args,kwds)
        l = [1.34*len(args[0][i].split(' ')) for i in range(len(args[0]))]
        for dl in l:
            if dl>self.max_length:
                print('ALLERT: Too short max_length {} of {}'.format(dl,self.max_length))
        return self.tokenizer(
            *args,
            padding="longest",
            max_length=self.max_length,
            truncation = True,
            return_tensors = "pt",
            **kwds 
        )


def get_llama_tokenizer(path,max_length):
    return MyWrapLlamaTokenizer(path,max_length=max_length)


class ClientHandler(threading.Thread):
    def __init__(self, client_socket, client_address):
        super(ClientHandler, self).__init__()
        self.client_socket = client_socket
        self.client_address = client_address
        self.arg_t = 0.05  # Default values for arg_t and arg_max_new_tokens
        self.arg_max_new_tokens = 500
        self.debug = False
        self.terminate_flag = threading.Event()
    
    def terminate(self):
        self.terminate_flag.set()

    def run(self):
        global threads
        with thread_pool_lock:
            threads.append(self)
        
        while not self.terminate_flag.is_set():
            try:
                data = self.client_socket.recv(130000)
                data = pickle.loads(data)
                if self.debug:
                    print(f'Data recv: {data}')
                if not data:
                    print(f"Connection closed by {self.client_address}.")
                    self.client_socket.close()
                    self.terminate()
                    break

                r_data = self.process(data)
                if self.debug:
                    print(f'Data sent: {r_data}')
                self.client_socket.send(r_data.encode('utf-8'))

            except KeyboardInterrupt:
                print("Server interrupted in client thread. Closing connection with", self.client_address)
                self.client_socket.close()
                self.terminate()
                break
            except Exception as e:
                print("Shutting down client socket...", self.client_address)
                print("Crush due to:",e)
                self.client_socket.close()
                self.terminate()
            
        with thread_pool_lock:
            threads.pop(threads.index(self))

    def process(self, llama_input):
        if type(llama_input) is str:
            if llama_input.startswith('[command]'):
                llama_input = llama_input[9:]
                if llama_input.startswith('arg_t'):
                    llama_input = llama_input.split('=')[1].strip()
                    self.arg_t = float(llama_input)
                    if self.arg_t<=0:
                        self.arg_t = 0.001
                    print('arg_t is set to {}'.format(self.arg_t))
                    return 'arg_t is set to {}'.format(self.arg_t)
                elif llama_input.startswith('debug'):
                    llama_input = llama_input.split('=')[1].strip().lower()
                    if llama_input=='true':
                        self.debug = True
                        print('debug is set to {}'.format(self.debug))
                        return 'debug is set to {}'.format(self.debug)
                    elif llama_input=='false':
                        self.debug = False
                        print('debug is set to {}'.format(self.debug))
                        return 'debug is set to {}'.format(self.debug)
                    else:
                        print('Recieve invalid command')
                        return 'INVALID COMMAND'
                elif llama_input.startswith('info'):
                    print('debug is {};arg_t is {};arg_max_new_tokens is {};{} active connections'.format(self.debug,self.arg_t,self.arg_max_new_tokens,len(threads)))
                    return 'debug is {};arg_t is {};arg_max_new_tokens is {};{} active connections'.format(self.debug,self.arg_t,self.arg_max_new_tokens,len(threads))
                elif llama_input.startswith('arg_max_new_tokens'):
                    llama_input = llama_input.split('=')[1].strip()
                    self.arg_max_new_tokens = int(llama_input)
                    if self.arg_max_new_tokens<=0:
                        self.arg_max_new_tokens = 500
                    print('arg_max_new_tokens is set to {}'.format(self.arg_max_new_tokens))
                    return 'arg_max_new_tokens is set to {}'.format(self.arg_max_new_tokens)
                else:
                    print('Recieve invalid command')
                    return 'INVALID COMMAND'
        
        else:
            with model_lock:
                # print(llama_input)
                llama_input = dealwithsystem(llama_input)
                inputs = tokenizer.apply_chat_template(llama_input, tokenize=False)
                # print(inputs)
                if inputs.startswith('<s>'):
                    inputs = inputs[3:]
                inputs = tokenizer(inputs)
                inputids = inputs['input_ids'].cuda()
                attention_mask=inputs['attention_mask'].cuda()
                # print(inputs,attention_mask)
                with torch.no_grad():
                    ot = model.generate(
                            inputs=inputids,
                            attention_mask = attention_mask ,
                            max_new_tokens= self.arg_max_new_tokens,
                            temperature = self.arg_t,
                            repetition_penalty=1.0,
                            pad_token_id=tokenizer.tokenizer.pad_token_id,
                            do_sample=True if self.arg_t>1e-5 else False
                        )
                    ot = ot[0][len(inputs[0]):]
                    # print(ot)
                out = tokenizer.decode(ot,skip_special_tokens=True) + '\n'
            return out
    
def start_server(port=33331):
    # host = '127.0.0.1'  # Use your computer's IP address or 'localhost'
    host = '0.0.0.0'
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Bind the socket to a specific address and port
        server_socket.bind((host, port))

        # Listen for incoming connections
        server_socket.listen(5)  # Allow up to 5 queued connections
        print(f"Listening on {host}:{port}...")

        while True:
            # Wait for a connection
            client_socket, client_address = server_socket.accept()
            print(f"Accepted connection from {client_address}")
            client_handler = ClientHandler(client_socket, client_address)
            client_handler.start()

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Close the server socket to release the port
        server_socket.close()
        print("Server socket closed. Exiting.")
####################################################3

llama_path ='MixtralModel'
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    print('start loading')
    model = AutoModelForCausalLM.from_pretrained(llama_path,torch_dtype=torch.bfloat16,device_map = "balanced")
    tokenizer = get_llama_tokenizer(llama_path,max_length=1024*8)
    print('loading done')
    start_server(port=33331)