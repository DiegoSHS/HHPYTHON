from flask import Flask, request
import json
from brutesleuth import BruteChain
import string
import threading
import zipfile
from time import sleep
app = Flask(__name__)


finalpass = None
threads = []
tests = 0


def generate(len=3, dig=True, lw=False, up=False,  sp=False):
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


def calculate(pswdict, filename, stop_ev):
    print(f'Iniciando hilo con valor 0 de {len(pswdict)}: {pswdict[0]}')
    zf = zipfile.ZipFile(filename)
    for psw in pswdict:
        global finalpass, tests
        if finalpass != None:
            print('hilo finalizado')
            break
        try:
            tests += 1
            print(tests)
            zf.extractall(
                path='/tmp/',
                pwd=psw.encode())
            finalpass = psw
            break
        except:
            pass
    if finalpass is None:
        print('No valid password found.')
        return
    else:
        print('Encontrado :'+finalpass)
        stop_ev.set()
        return


def createThreads(iterables, filename, stop_ev):
    global threads
    for it in iterables:
        thread = threading.Thread(target=calculate, args=[
            it, filename, stop_ev])
        threads.append(thread)


def joinThreads():
    global threads
    for thread in threads:
        sleep(0.2)
        thread.join()


def initThreads():
    global threads
    global finalpass
    global tests
    tests = 0
    finalpass = None
    for thread in threads:
        sleep(0.2)
        thread.start()


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))


def startThreads(iterable, filename, stop_ev):
    pssses = list(iterable)
    length = len(pssses)
    print(f'Dict size {length}')
    sleep(1)
    if length < 16000:
        createThreads([pssses], filename, stop_ev)
    if length < 32000:
        iterables = list(split(pssses, 4))
        createThreads(iterables, filename, stop_ev)
    if length >= 32000 and length < 64000:
        iterables = list(split(pssses, 8))
        createThreads(iterables, filename, stop_ev)
    if length >= 64000 and length < 128000:
        iterables = list(split(pssses, 16))
        createThreads(iterables, filename, stop_ev)
    if length >= 256000 and length < 512000:
        iterables = list(split(pssses, 32))
        createThreads(iterables, filename, stop_ev)
    if length >= 512000 and length < 1024000:
        iterables = list(split(pssses, 64))
        createThreads(iterables, filename, stop_ev)
    if length >= 2048000 and length < 4096000:
        iterables = list(split(pssses, 128))
        createThreads(iterables, filename, stop_ev)
    if length >= 4096000 and length < 8192000:
        iterables = list(split(pssses, 256))
        createThreads(iterables, filename, stop_ev)
    if length >= 8192000:
        iterables = list(split(pssses, 256))
        createThreads(iterables, filename, stop_ev)


def iftr(string):
    if string == 'true':
        return True
    else:
        return False


@ app.route('/bruteforce/', methods=['POST'])
def bruteforce():
    global threads
    threads = []
    print('starts')
    stop_ev = threading.Event()
    file = request.files['file']
    typee = request.form['type']
    argum = json.loads(typee)
    passwords_dict = generate(
        len=int(argum['len']),
        dig=iftr(argum['dig']),
        lw=iftr(argum['lw']),
        up=iftr(argum['up']),
        sp=iftr(argum['sp'])
    )
    filename = './uploads/' + file.filename
    file.save(filename)
    startThreads(passwords_dict, filename, stop_ev)
    initThreads()
    if stop_ev.set():
        joinThreads()
    print(f'Enviando clave al servidor: {finalpass}')
    return {
        "password": finalpass
    }


@ app.route('/brutesingle/', methods=['POST'])
def brutesingle():
    print('Starting process')
    file = request.files['file']
    typee = request.form['type']
    argum = json.loads(typee)
    print(argum)
    print(
        int(argum['len']),
        iftr(argum['dig']),
        iftr(argum['lw']),
        iftr(argum['up']),
        iftr(argum['sp']))
    passwords_dict = generate(
        len=int(argum['len']),
        dig=iftr(argum['dig']),
        lw=iftr(argum['lw']),
        up=iftr(argum['up']),
        sp=iftr(argum['sp'])
    )
    filename = './uploads/' + file.filename
    file.save(filename)
    zf = zipfile.ZipFile(filename, metadata_encoding=None)
    finalpassw = None
    for psw in passwords_dict:
        try:
            print(psw)
            zf.extractall(
                path='/tmp/',
                pwd=psw.encode())
            finalpassw = psw
            break
        except:
            pass
    if finalpassw is None:
        print('No valid password found.')
    else:
        print(f'Password found {finalpassw}')
    return {
        "password": finalpassw
    }


app.run(debug=True)
