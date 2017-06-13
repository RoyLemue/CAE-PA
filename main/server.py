# -*- coding: utf-8 -*-
#   Erstellt von Roy Ledermüller mit PyCharm Community Edition 
#   Erstelldatum:   30.05.2017
#   Projektname:    CAE-PA
#   Getestet mit Python 3.5
import time
from opcua import ua, uamethod, Server
import os
from main.settings import *

class OpcServer(Server):
    def __init__(self, port):
        xmlpath = os.path.normpath(os.path.join(PROJECT_ROOT, *['main', 'xml', 'nodeset.xml']))
        libpath = os.path.normpath(os.path.join(PROJECT_ROOT, *['main', 'xml', 'lib.xml']))
        super(OpcServer, self).__init__()
        self.set_endpoint("opc.tcp://0.0.0.0:" + str(port) + "/freeopcua/server/")
        # setup our own namespace, not really necessary but should as spec
        self.uri = "http://caepa.fography.de"
        self.idx = self.register_namespace(self.uri)
        # get Objects node, this is where we should put our nodes
        self.import_xml(libpath)
        self.import_xml(xmlpath)
        self.objects = self.get_objects_node()


class OpcConnector:
    def fill201(self, nodeId):
        pass

    @classmethod
    @uamethod
    def fill202(self, nodeId):
        pass

    @classmethod
    @uamethod
    def fill203(self, nodeId):
        pass

    @classmethod
    @uamethod
    def fill204(self, ratio201, ratio202, ratio203, volume, flowRate):
        pass

    def __init__(self):

        self.mixer = OpcServer(4840)
        #self.moka.objects.get_child("0:")
        #self.moka.link_method(fill201, say_hello_xml)

        #self.reactor = OpcServer(4841)
        #self.filter = OpcServer(4842)
        #self.filler = OpcServer(4843)
        '''
        mixerObj = self.mixer.objects.add_object(self.mixer.idx, "Mixer")

        fill201 = mixerObj.add_method(self.mixer.idx, "Fill_B201", self.fill201)
        fill204 = mixerObj.add_method(self.mixer.idx, "Fill_B204", self.fill204, [ua.VariantType.Float,
                                                               ua.VariantType.Float,
                                                               ua.VariantType.Float,
                                                               ua.VariantType.Float,
                                                               ua.VariantType.Float])
        '''

        self.moka.start()
        #self.reactor.start()
        #self.filter.start()
        #self.filler.start()


def main():
    # parse command line options
    OpcCon = OpcConnector()
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
