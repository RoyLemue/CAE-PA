# -*- coding: utf-8 -*-
#   Erstellt von Roy Ledermüller mit PyCharm Community Edition
#   Erstelldatum:   05.07.2017
#   Projektname:    CAE-PA
#   Getestet mit Python 3.5

import xml.etree.ElementTree as et
from enum import Enum
import re as regex

def sortNode(x, y):
       if x.id < y.id:
            return 1
       elif x.id == y.id:
            return 0
       else:
            return -1

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
    def __init__(self, Node, interface):
        #self.name = Node.find('recipename').text
        self.nodeList = {}
        self.serviceList ={}
        for stepNode in Node.iter('recipestep'):
            re_id = stepNode.attrib['RE_ID']
      #      print ('step'+re_id)
            self.nodeList[re_id] = stepNode

        for stepNode in Node.iter('service'):
            re_id = stepNode.attrib['RE_ID']
      #      print ('step'+re_id)
            self.serviceList[re_id] = stepNode

        rootId = Node.find('runblock').attrib['RE_ID']
        for node in self.nodeList.values():
            if rootId == node.attrib['ParentRE']:
                self.RunBlock = XmlRecipeBlock(node, interface,self.nodeList,self.serviceList)
                break

        #self.StopBlock = XmlRecipeBlock(Node.find('StopBlock', interface))


class XmlRecipeBlock():
    def __init__(self, Node,interface,nodeList,serviceList):
        self.name = Node.attrib['name']
        self.id = Node.attrib['RE_ID'] # root ID
        self.parentNode = Node.attrib['ParentRE'] # take the temp elem ( at first iteration = runblock
        self.childs ={}
        self.sortList = []
        keyList = []

      #  print (nodeList.keys())
        for node in nodeList.values():
            if str(node.attrib['ParentRE']) == self.id:
                blockTypeString = node.attrib['type']
                blockType = regex.split('\!|\|', blockTypeString)[-1:]

                if blockType[0] == 'ParallelerBlock' or blockType[0] == 'SeriellerBlock':
                     print ('block' +str(node.attrib['RE_ID']) + 'parent ' + str(node.attrib['ParentRE']))
                     child = XmlRecipeBlock(node, interface, nodeList,serviceList)

                else:
                    child = XmlRecipeServiceInstance(node, interface, nodeList, serviceList)
                self.childs[child.id] = child
        keys = []
        for key in self.childs.keys():
            keys.append(key)
        self.sortList = keys.sort()


class XmlRecipeServiceInstance:
    def __init__(self, Node, interface,nodeList,serviceList):
        self.id = Node.attrib['RE_ID']
        print(self.id)

        for node in serviceList.values():
           if node.attrib['RE_ID'] == self.id:
               #print(node.attrib['NameRE'])
               self.method = node.find('method').text
               self.serviceID = node.find('serviceID').text
               self.parentRE = node.attrib['ParentRE']  # should be parentRE
               #print('service ' +self.serviceID)
               self.opcserviceNode = interface.services[self.serviceID]
               self.parentModul = interface.modules[self.opcserviceNode.attrib['ParentID']]
               #print (self.parentModul.attrib['Type'])





#########################################################################
#Interface                                                              #
#########################################################################
class XmlRecipeInterface:
    def __init__(self, InterfaceNode):
       # self.interfaceName = InterfaceNode.attrib['name']
        self.modules = {}
        self.services ={}
        for module in InterfaceNode.iter('module'):
            self.modules[module.attrib['RE_ID']] = module

        for service in InterfaceNode.iter('opcservice'):
            self.name = service.attrib["RE_ID"]
            self.services[self.name] = service

class XmlInterfaceModul:
    def __init__(self, InterfaceNode):
        self.name = InterfaceNode.find('Modulschnittstellenabfrage')
        self.opcName = InterfaceNode.find('OPC_UA_Name')
#        self.position = int(InterfaceNode.find('Position'))
        self.services = []
        for service in InterfaceNode.findall('Dienst'):
            self.services.append(XmlInterfaceService(service))


class XmlInterfaceService:
    def __init__(self, InterfaceNode):
        self.name = InterfaceNode.find('service')
        self.opcName = InterfaceNode.find('OPC_UA_Methodenname').text
        self.continous = bool(InterfaceNode.find('Konti').text)
        self.parameters = {}
        for paramNode in InterfaceNode.findall('parameter'):
            # paramType = paramNode.find('type').text
            paramType = ''
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


