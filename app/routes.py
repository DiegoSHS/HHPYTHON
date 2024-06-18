"""This module contains the routes for the Flask app"""

import time
import json
import string
import re
import threading
from queue import Queue
from random import shuffle
from zipfile import ZipFile, error
from brutesleuth import BruteChain
from flask import request, Blueprint
from flask_cors import cross_origin
main = Blueprint('main', __name__)

def timeit(function):
    """A decorator to print the time a function took to run"""
    def wrapper(*args, **kwargs):
        """The wrapper that is run instead of the function"""
        start_time = time.time()
        updated_function = function(*args, **kwargs)
        end_time = time.time()
        print(f'Time spent: {end_time - start_time} seconds')
        return updated_function
    return wrapper


def setup_threads(function,limit:int):
    """Setup threads for the function passed in the arguments"""
    threads = []
    for _ in range(1, limit):
        thread = threading.Thread(target=function, args=(_,), daemon=True)
        thread.start()
        threads.append(thread)
    return threads


def join_threads(threads:list):
    """Join the threads passed in the arguments"""
    for thread in threads:
        thread.join()

def start_threads(passwords_queue:Queue,function):
    """Start the threads for the function passed in the arguments"""
    length = passwords_queue.qsize()
    print(f'Dict size {length}')
    return setup_threads(limit=4,function=function)


def split(pass_list:list, num_parts:int):
    """Split a list into n parts"""
    kdiv, module = divmod(len(pass_list), num_parts)
    return (pass_list[i*kdiv+min(i, module):(i+1)*kdiv+min(i+1, module)] for i in range(num_parts))


def iftr(text:string):
    """Convert a string to a boolean value"""
    return text == 'true'


@timeit
def reorder(iterable, passwords_queue:Queue):
    """Reorder the dictionary to filter out the passwords that are not valid"""
    pass_words = [p for p in list(iterable) if not re.findall(
        pattern=r'(.)\1{2}|(.)\1{3}|(.)\1{4}|(.)\1{5}|(.)\1{6}|(.)\1{7}|(.)\1{8}', string=p
    )]
    shuffle(pass_words)
    passwords_queue.queue.extend(pass_words)
    print('Filtered')


def get_dict_option(
    digits=True,
    lowercase=False,
    uppercase=False,
    marks=False
    ):
    """Get the dictionary option for the bruteforce attack"""
    option = string.printable if digits and lowercase and uppercase and marks else ''
    if uppercase and lowercase and digits:
        option = string.ascii_letters+string.digits
    if uppercase and lowercase:
        option = string.ascii_letters
    if uppercase and digits:
        option = string.ascii_uppercase+string.digits
    if lowercase and digits:
        option = string.ascii_lowercase+string.digits
    if uppercase:
        option = string.ascii_uppercase
    if lowercase:
        option = string.ascii_lowercase
    if digits:
        option = range(0, 10)
    return option

def generate_dictionary(
    arguments,
    length=3,
    custom_string=''
    ):
    """Generate a dictionary for the bruteforce attack on a zip file"""
    digits=iftr(arguments['dig'])
    lowercase=iftr(arguments['lw'])
    uppercase=iftr(arguments['up'])
    marks=iftr(arguments['sp'])
    if custom_string != '':
        return BruteChain(length, list(bytes.fromhex(custom_string).decode('utf-8')))
    return BruteChain(length, list(get_dict_option(
        digits=digits, lowercase=lowercase,
        uppercase=uppercase,
        marks=marks
        )))


def worker(correct_password:dict, zip_file: ZipFile, passwords_queue:Queue):
    """The worker function for the bruteforce attack"""
    while not passwords_queue.empty():
        password = passwords_queue.get()
        try:
            zip_file.extractall(
                path='/tmp/',
                pwd=password.encode())
            correct_password.update(password=password)
            with passwords_queue.mutex:
                passwords_queue.all_tasks_done()
                passwords_queue.queue.clear()
            return
        except error:
            pass


@main.route('/bruteforce/', methods=['POST'])
@cross_origin()
def bruteforce():
    """The route for the bruteforce attack on a zip file"""
    passwords = Queue()
    correct_password = {"password":""}

    print('starts')
    file = request.files['file']
    password_type = request.form['type']
    arguments = json.loads(password_type)
    new_passwords = generate_dictionary(
        arguments=arguments,
        length=int(arguments['len']),
        custom_string=arguments['ct']
        )
    reorder(
        iterable=new_passwords,
        passwords_queue=passwords
        )
    filename = './app/uploads/' + file.filename
    file.save(filename)
    with ZipFile(filename, 'r') as zip_file:
        threads = start_threads(
            passwords_queue=passwords,
            function=lambda _: worker(
                zip_file=zip_file,
                correct_password=correct_password,
                passwords_queue=passwords
                )
            )
        join_threads(threads)
    print(f'Enviando clave al servidor: {correct_password.get("password")}')
    return {
        "password": correct_password.get('password')
    }
