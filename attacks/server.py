import socket
import time
import os

class Server():
    def __init__(self, ip, port):
        self.ip = "localhost"
        self.port = 9999
        self.server_sock = None
    
    def sendto_server(self, data):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        time.sleep(1)
        sock.sendto(data, (self.ip, self.port))

    def start_record_server(self, result_filename):
        self.result_filename = result_filename
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_sock.bind((self.ip, self.port))
        print(f'*********starting server at {self.ip}:{self.port}*********')
        injection_test = False
        success_count = 0
        runtime_error = 0
        inject_success_count = 0
        exec_flag = True
        total_test_count = 0
        while True:
            data, addr = self.server_sock.recvfrom(1024)
            if data == b"RESET":
                exec_flag = false
                total_test_count = 0
                success_count = 0

            if data == b"STARTAPP":
                print('STARTAPP')

            if data == b'START_EXEC':
                exec_flag = True
                total_test_count += 1
                # print('-- START EXECUTION --')

            if exec_flag and data == b'FIRST_FUNC_EXECUTION':
                print('FIRST_FUNC_EXECUTION')
                success_count += 1

            if data == b"ENDAPP":
                print('ENDAPP')

            if data == b"END_EXEC":
                # print('-- END EXECUTION --')
                exec_flag = False

            if data == b"END_EXEC_WITH_ERROR":
                print('-- END EXECUTION WITH ERROR--')
                exec_flag = False
                runtime_error += 1

            if data == b'END':
                self.server_sock.close()
                break
            
            if b'INJECT INSTRUCTION:' in data:
                injection_test = True
                print(data)


    def end_server(self):
        if self.start_server:
            self.server_sock.close()