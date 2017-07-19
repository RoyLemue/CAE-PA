# -*- coding: utf-8 -*-
#   Erstellt von Roy Ledermüller mit PyCharm Community Edition
#   Erstelldatum:   05.07.2017
#   Projektname:    CAE-PA
#   Getestet mit Python 3.5

import xml.etree.ElementTree as et
from enum import Enum
import re as regex
import main.models

def sortNode(x, y):
       if x.id < y.id:
            return 1
       elif x.id == y.id:
            return 0
       else:
            return -1

class RecipeElementState(Enum):
    WAITING = 1
    RUNNING = 2
    COMPLETED = 3
    ABORTED = 4

class XmlRecipeParser:
    def __init__(self, xmlFile):
        tree = et.parse(xmlFile)
        root = tree.getroot() #ComosXmlExport Element
        #anlage = root.findall('plant')
        for child in root:
       #     print (child.tag)
            anlage = child
        self.interface = XmlRecipeInterface(anlage.find('interface'))
        self.recipe = XmlRecipeInstance(anlage.find('recipe'), self.interface)
      #  print (anlage.find('recipe').attrib['name'])

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
        self.parentModul = interface.modules[self.xmlInterfaceObject.parentId]
        self.state = RecipeElementState.WAITING
        self.opcServiceNode = main.models.RecipeHandler.instance.anlage.parts[self.parentModul.name].ServiceList[self.xmlInterfaceObject.opcName]

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
            self.modules[module.attrib['RE_ID']] = XmlInterfaceModul(module, servicesPool)

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



class BlockType(Enum):
    SERIAL = 1
    PARALLEL = 2


class XmlTopologyParser:
    def __init__(self, xmlFile):
        tree = et.parse(xmlFile)
        root = tree.getroot() #ComosXmlExport Element
        anlage = root.find('plant')
        self.interface = XmlRecipeInterface(anlage.find('interface'))

