# -*- coding: utf-8 -*-
#   Erstellt von Roy Ledermüller mit PyCharm Community Edition
#   Erstelldatum:   05.07.2017
#   Projektname:    CAE-PA
#   Getestet mit Python 3.5

import xml.etree.ElementTree as et
from lxml import etree
from enum import Enum
import re as regex
import main.models
import traceback
import logging

logger = logging.getLogger('django')

class OpcState(Enum):
    IDLE = 4
    STARTING = 3
    RUNNING = 6
    PAUSING = 13
    PAUSED = 5
    RESUMING = 14
    HOLDING = 10
    HELD = 11
    UNHOLDING = 12
    COMPLETING = 16
    COMPLETE = 17
    RESETTING = 15
    STOPPING = 7
    STOPPED = 2
    ABORTING = 8
    ABORTED = 9
    CLEARING = 1

RUN_STATES = [OpcState.RUNNING,
                  OpcState.PAUSING,
                  OpcState.PAUSED,
                  OpcState.RESUMING]

ACTIVE_STATES = [OpcState.RUNNING,
                  OpcState.PAUSING,
                  OpcState.PAUSED,
                  OpcState.RESUMING,
                 OpcState.IDLE,
                 OpcState.STARTING,
                 OpcState.HOLDING,
                 OpcState.HELD,
                 OpcState.UNHOLDING,
                 OpcState.RESETTING,
                 OpcState.COMPLETING,
                 OpcState.COMPLETE]

NORMAL_STATES = [OpcState.RUNNING,
                  OpcState.PAUSING,
                  OpcState.PAUSED,
                  OpcState.RESUMING,
                 OpcState.IDLE,
                 OpcState.STARTING,
                 OpcState.HOLDING,
                 OpcState.HELD,
                 OpcState.UNHOLDING,
                 OpcState.RESETTING,
                 OpcState.COMPLETING,
                 OpcState.COMPLETE,
                 OpcState.STOPPING,
                 OpcState.STOPPED,
                 OpcState.CLEARING]

class OpcMethod(Enum):
    START = 2
    PAUSE = 6
    RESUME = 7
    HOLD = 4
    UNHOLD = 5
    RESET = 1
    STOP = 3
    ABORT = 8
    CLEAR = 9

STATE_MAP = {
    b'idle' : OpcState.IDLE,
    b'complete' : OpcState.COMPLETE,
    b'aborting': OpcState.ABORTING,
    b'aborted': OpcState.ABORTED,
    b'running' : OpcState.RUNNING,
    b'pausing' : OpcState.PAUSING,
    b'paused' : OpcState.PAUSED,
    b'holding': OpcState.HOLDING,
    b'held': OpcState.HELD,
    b'unholding': OpcState.UNHOLDING,
    b'stopping': OpcState.STOPPING,
    b'stopped': OpcState.STOPPED,
}
METHOD_MAP = {
    'start' : OpcMethod.START,
    'pause': OpcMethod.PAUSE,
    'resume': OpcMethod.RESUME,
    'hold': OpcMethod.HOLD,
    'unhold': OpcMethod.UNHOLD,
    'reset': OpcMethod.RESET,
    'stop': OpcMethod.STOP,
    'abort': OpcMethod.ABORT,
    'clear': OpcMethod.CLEAR,
}

class RecipeElementState(Enum):
    WAITING = 1
    RUNNING = 2
    COMPLETED = 3
    ABORTED = 4

class BlockType(Enum):
    SERIAL = 1
    PARALLEL = 2

class RecipeType:
    def __init__(self, start, running, complete):
        self.start = start
        self.running = running
        self.complete = complete

#Allowed Starting States and Running States and the completing State
RECIPE_COMMAND = {
    OpcMethod.START : RecipeType([OpcState.IDLE], [OpcState.STARTING], [OpcState.RUNNING]),
    OpcMethod.PAUSE : RecipeType([OpcState.RUNNING],[OpcState.PAUSING],[OpcState.PAUSED]),
    OpcMethod.RESUME: RecipeType([OpcState.PAUSED],[OpcState.RESUMING],[OpcState.RUNNING]),
    OpcMethod.HOLD: RecipeType(RUN_STATES,[OpcState.HOLDING],[OpcState.HELD]),
    OpcMethod.UNHOLD: RecipeType([OpcState.HELD],[OpcState.UNHOLDING],[OpcState.RUNNING]),
    OpcMethod.RESET: RecipeType([OpcState.COMPLETE, OpcState.STOPPED, OpcState.ABORTED],[OpcState.RESETTING],[OpcState.IDLE]),
    OpcMethod.STOP: RecipeType(ACTIVE_STATES,[OpcState.STOPPING],[OpcState.STOPPED]),
    OpcMethod.ABORT: RecipeType(NORMAL_STATES,[OpcState.ABORTING],[OpcState.ABORTED]),
    OpcMethod.CLEAR: RecipeType([OpcState.ABORTED],[OpcState.CLEARING],[OpcState.STOPPED]),
}


class XmlTopologyParser:
    def __init__(self, xmlFile, plant):
        tree = et.parse(xmlFile)
        root = tree.getroot()  # ComosXmlExport Element
        anlage = root.find('plant')
        self.interface = XmlRecipeInterface(anlage.find('interface'))
        self.__valid = False
        try:
            self.checkMethods(plant)
        except et.ParseError or et.KeyError or et.AttributeError as e:
            logger.error(e)
            self.message = str(e)

    def checkMethods(self, plant):
        """
        Check topology against opcua namespace. Checks if all Services Exists
        :param client: OpcPlant
        :return Boolean: True when Topology is valid
        """
        lostServices = 0
        for module in self.interface.modules.values():
            anlagenModul = plant.parts[module.name]
            for service in module.services.values():
                opcService = anlagenModul.getService(service.opcName)
                if not opcService:
                    logger.info(service.opcName + ' nicht gefunden')
                    lostServices += 1
                else:
                    logger.info(anlagenModul.name + ' ' + opcService.name + ' gefunden')
        if lostServices == 0:
            self.__valid = True
            return True
        else:
            self.__valid = False
            return False
    @property
    def isValid(self):
        return self.__valid

class XmlRecipeParser:
    def __init__(self, xmlFile, topology, plant):
        self.__valid = False

        try:
            tree = et.parse(xmlFile)
            root = tree.getroot() #ComosXmlExport Element
            #anlage = root.findall('plant')
            self.anlage = root.find('plant')
            self.interface = XmlRecipeInterface(self.anlage.find('interface'))
            # instance has only to be parsed, if interface is valid

            self.checkTopology(plant, topology)

            self.recipe = XmlRecipeInstance(self.anlage.find('recipe'), self.interface)
            self.__valid = True
        except Exception as e:
            self.message = str(traceback.format_exc())
            logger.error(str(e))
      #  print (anlage.find('recipe').attrib['name'])



    def checkTopology(self, plant, topology):
        """
        Check Recipe against Topology
        :param plant: OpcPlant
        :param topology: XmlTopologyParser
        :return Boolean: True when Topology is valid
        """
        if not topology.isValid:
            if not topology.checkMethods(plant):
                return
        for index, topoModule in topology.interface.modules.items():
            recipeModule = self.interface.modules[index]
            if topoModule.position != recipeModule.position:
                logger.error('Modulverschaltung des Rezeptes stimmt nicht mit aktueller Verschaltung überein')
                self.__valid = False
                return False
            for serviceIndex, topoService in topoModule.services.items():
                if topoService.opcName != recipeModule.services[serviceIndex].name:
                    logger.error('Modulverschaltung des Rezeptes stimmt nicht mit aktueller Verschaltung überein')
                    self.__valid = False
                    return False
        self.__valid = True
        return True


    @property
    def isValid(self):
        return self.__valid

class XmlRecipeInstance:
    def __init__(self, node, interface):
        #self.name = Node.find('recipename').text
        self.id = node.attrib['RE_ID']
        self.parentId = node.attrib['ParentRE']
        self.name = node.attrib['name']
        self.date = node.find('creationDate').text
        self.author = node.find('author').text
        servicesPool = []
        for service in node.iter('service'):
            servicesPool.append(service)
        blockPool = node.iter('recipestep')

        self.runBlock = XmlRecipeBlock(node.find('runblock'), interface, blockPool, servicesPool)



class XmlRecipeBlock:
    def __init__(self, Node,interface,blockPool,servicesPool):
        if 'name' not in Node.attrib:
            self.name =""
        else:
            self.name = Node.attrib['name']
        self.id = Node.attrib['RE_ID'] # root ID
        self.parentId = Node.attrib['ParentRE'] # take the temp elem ( at first iteration = runblock
        self.childs ={}
        self.sortList = []
        keyList = []
        blockTypeString = Node.attrib['type']
        self.blockType = regex.split('\!|\|', blockTypeString)[-1:][0]

      #  print (nodeList.keys())
        for poolNode in blockPool:
            if str(poolNode.attrib['ParentRE']) == self.id:
                blockTypeString = poolNode.attrib['type']
                blockType = regex.split('\!|\|', blockTypeString)[-1:]

                if blockType[0] == 'ParallelerBlock' or blockType[0] == 'SeriellerBlock':
                     # print ('block' +str(poolNode.attrib['RE_ID']) + 'parent ' + str(poolNode.attrib['ParentRE']))
                     child = XmlRecipeBlock(poolNode, interface, blockPool,servicesPool)
                     self.childs[child.id] = child
                     self.sortList.append(child.id)
                else:
                    for service in servicesPool:
                        if poolNode.attrib['RE_ID'] == service.attrib['RE_ID']:
                            child = XmlRecipeServiceInstance(service, interface, blockPool, servicesPool)
                            self.childs[child.id] = child
                            self.sortList.append(child.id)
        self.sortList.sort()


class XmlRecipeServiceInstance:
    def __init__(self, Node, interface,blockPool,servicesPool):
        self.name = Node.attrib['NameRE']
        self.id = Node.attrib['RE_ID']
        self.parentId = Node.attrib['ParentRE']
        self.method = Node.find('method').text
        self.opcId = Node.find('linkedOPCID').text
        self.serviceId = Node.find('serviceID').text
        self.xmlInterfaceObject = interface.getServiceById(self.serviceId)
        self.state = RecipeElementState.WAITING
        self.opcServiceNode = main.models.RecipeHandler.anlage.parts[self.xmlInterfaceObject.parentModule.name].ServiceList[self.xmlInterfaceObject.opcName]

        self.timeout = 10.0

        self.methodName = self.method.lower()
        if self.methodName == 'start' and not self.xmlInterfaceObject.continous:
            # TODO all valid run
            self.type = main.models.RecipeType([main.models.OpcState.IDLE],
                                 [main.models.OpcState.STARTING, main.models.OpcState.RUNNING, main.models.OpcState.PAUSING, main.models.OpcState.PAUSED],
                                 [main.models.OpcState.COMPLETE])
        else:
            self.type = main.models.RECIPE_COMMAND[main.models.METHOD_MAP[self.methodName]]
        #print (self.parentModul.attrib['Type'])




#########################################################################
#Interface                                                              #
#########################################################################

class XmlRecipeInterface:
    def __init__(self, InterfaceNode):
        self.name = InterfaceNode.attrib['name']
        self.modules = {}
        self.services ={}
        servicesPool = InterfaceNode.findall('opcservice')
        for module in InterfaceNode.findall('module'):
            m = XmlInterfaceModul(module, servicesPool)
            self.modules[m.name] = m

    def getServiceById(self, serviceId):
        for module in self.modules.values():
            for service in module.services.values():
                if service.treeId == serviceId:
                    return service
        return None



class XmlInterfaceModul:

    def __init__(self, modulNode, servicesPool):
        self.id = modulNode.attrib['RE_ID']
        self.parentId = modulNode.attrib['ParentRE']
        self.name = modulNode.attrib['Type']
        self.position = modulNode.attrib['position']
        self.services = {}
        for service in servicesPool:
            if service.attrib['ParentRE'] == modulNode.attrib['RE_ID']:
                s = XmlInterfaceService(self, service)
                self.services[s.opcName]=s


class XmlInterfaceService:
    def __init__(self, parentNode, serviceNode):
        self.treeId = serviceNode.attrib['RE_ID']
        self.parentId = serviceNode.attrib['ParentRE']
        self.name = serviceNode.attrib['name']
        self.opcName = serviceNode.attrib['opcName']
        self.id = serviceNode.attrib['opcID']
        self.continous = int(serviceNode.find('contiType').text)
        self.parameters = {}
        self.parentModule = parentNode

        # TODO Check with COMOS
        for paramNode in serviceNode.findall('parameter'):
            # paramType = paramNode.find('type').text
            paramType = 'not set'
            paramName = paramNode.find('parameterdesc').text
            paramVal = paramNode.find('defaultvalue').text

            self.parameters[paramName] = {'default': paramVal, 'type': paramType}
