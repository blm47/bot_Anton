from botaster.mods import *
from threading import Thread

tmppath = '/tmp/bot_anton_log/'

if __name == '__main__':
    cur_listdir = os.listdir(tmppath)

    while True:
        listdirr = os.listdir(tmppath)
        new_files = list(set(listdirr) - set(cur_listdir))
