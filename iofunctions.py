import configparser, socket, pickle
from os import path
from classes import socketClient

def current_path(file=None):
    try:
        dir_path = path.dirname(path.realpath(__file__), )
        if file != None:
            config_path = path.join(dir_path, file)
            return config_path
        else:
            return dir_path
    except Exception as e:
        return e

def fromcfg(section,key):
    try:
        fullpath = current_path('config.cfg')
        config = configparser.RawConfigParser()
        config.read_file(open(fullpath))
        r = config.get(section,key)
    except:
        print("Error on reading 'config.cfg' file")
        return None
    return r

def write(filepath, msg):
    try:
        f = open(filepath, 'a')
        f.write(msg)
        f.close
        return 1
    except Exception as e:
        print("Error on writing: ", filepath, "\n\rmessage:", msg, "\n\rwith error: ", e)
        return 0

def tcpsock_client(msg, ip='locahost', port=5007):
    address = (ip, port)
    client = socketClient(address)
    sock = client.create_socket()
    ans = client.connect(sock)
    if ans == 'ok':
        ans = client.send_data(sock, msg)
    else:
        return 'error on connecting to server', ans
    if ans == 'ok':
        ans = client.receive_data(sock, 1024)
        if ans == msg:
            ans = 'ok'
        else:
            client.close(sock)
            return 'error on receiving data', ans
    client.close(sock)
    return ans
