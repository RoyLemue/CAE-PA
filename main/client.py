# -*- coding: utf-8 -*-
#   Erstellt von Roy Ledermüller mit PyCharm Community Edition 
#   Erstelldatum:   30.05.2017
#   Projektname:    CAE-PA
#   Getestet mit Python 3.5
import time

import os, sys
import subprocess
import threading

from main.models import *

PROJCET_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
BUILD_DIR = os.path.join(PROJCET_ROOT, 'build')



class OpcServerThread(threading.Thread):
    def __init__(self, stdout, name, port):
        threading.Thread.__init__(self)
        self.stdout = stdout
        self.stderr = None
        self.name = name
        self.port = port

    def run(self):
        subprocess.call([os.path.join(BUILD_DIR, "uamoduleserver_"+self.name), str(self.port), self.name])

def main():
    # xmldata = XmlParser(os.path.join(PROJCET_ROOT, *['main', 'xml', 'example.xml']))
    # parse command line options
    mixName = "mixer"
    reactorName = "reactor"
    mixerThread = OpcServerThread(sys.stdout, mixName, MIXER_PORT)
    mixerThread.start()
    reactorThread = OpcServerThread(sys.stdout, reactorName, REACTOR_PORT)
    reactorThread.start()
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
