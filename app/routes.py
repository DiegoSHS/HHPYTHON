from flask import request, Blueprint
from flask_cors import cross_origin
import json
from brutesleuth import BruteChain
import string
import threading
import zipfile
import re
import time
from queue import Queue
from random import shuffle

main = Blueprint('main', __name__)
passwords = Queue()
finalpass = None
threads = []
tests = 0
filename = ''
zf = None


def generate(len=3, dig=True, lw=False, up=False,  sp=False, ct=''):
    if ct != '':
        return BruteChain(len, list(bytes.fromhex(ct).decode('utf-8')))
    if up and lw and dig and sp:
        return BruteChain(len, list(string.printable))
    if up and lw and dig:
        return BruteChain(len, list(string.ascii_letters+string.digits))
    if up and lw:
        return BruteChain(len, list(string.ascii_letters))
    if up and dig:
        return BruteChain(len, list(string.ascii_uppercase+string.digits))
    if lw and dig:
        return BruteChain(len, list(string.ascii_lowercase+string.digits))
    if up:
        return BruteChain(len, list(string.ascii_uppercase))
    if lw:
        return BruteChain(len, list(string.ascii_lowercase))
    if dig:
        return BruteChain(len, list(range(0, 10)))
    else:
        return BruteChain(len, list(string.printable))


def timeit(f):
    """A decorator to print the time a function took to run"""
    def wrapper(*args, **kwargs):
        """The wrapper that is run instead of the function"""
        t0 = time.time()
        ret = f(*args, **kwargs)
        t1 = time.time()
        print('Time spent: {} seconds'.format(t1 - t0))
        return ret
    return wrapper


def calculate(pswdict, filename):
    zf = zipfile.ZipFile(filename)
    global finalpass, tests
    for psw in pswdict:
        if finalpass != None:
            break
        try:
            zf.setpassword(psw.encode())
            if zf.testzip() is None:
                finalpass = psw
                break
        except:
            pass


def createThreads(limit):
    global threads
    for _ in range(1, limit):
        thread = threading.Thread(target=worker, args=(_,), daemon=True)
        thread.start()
        threads.append(thread)


def joinThreads():
    global threads
    for thread in threads:
        thread.join()


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))


@timeit
def reorder(iterable):
    passws = [p for p in list(iterable) if not re.findall(
        pattern=r'(.)\1{2}|(.)\1{3}|(.)\1{4}|(.)\1{5}|(.)\1{6}|(.)\1{7}|(.)\1{8}', string=p
    )]
    shuffle(passws)
    passwords.queue.extend(passws)
    print('Filtered')


def worker(w):
    global finalpass, zf, filename
    while not passwords.empty():
        password = passwords.get()
        try:
            zf.extractall(
                path='/tmp/',
                pwd=password.encode())
            finalpass = password
            with passwords.mutex:
                passwords.all_tasks_done()
                passwords.queue.clear()
            return
        except:
            pass
        pass


def startThreads():
    length = passwords.qsize()
    print(f'Dict size {length}')
    createThreads(4)


def iftr(string):
    if string == 'true':
        return True
    else:
        return False


@main.route('/bruteforce/', methods=['POST'])
@cross_origin()
def bruteforce():
    global threads, filename, zf, finalpass
    finalpass = None
    threads = []
    print('starts')
    file = request.files['file']
    typee = request.form['type']
    argum = json.loads(typee)
    reorder(iterable=generate(
        len=int(argum['len']),
        dig=iftr(argum['dig']),
        lw=iftr(argum['lw']),
        up=iftr(argum['up']),
        sp=iftr(argum['sp']),
        ct=argum['ct']
    ))
    filename = './app/uploads/' + file.filename
    file.save(filename)
    zf = zipfile.ZipFile(filename, 'r')
    startThreads()
    joinThreads()
    print(f'Enviando clave al servidor: {finalpass}')
    return {
        "password": finalpass
    }

