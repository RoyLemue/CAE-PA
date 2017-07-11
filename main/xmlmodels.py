# -*- coding: utf-8 -*-
#   Erstellt von Roy Ledermüller mit PyCharm Community Edition
#   Erstelldatum:   05.07.2017
#   Projektname:    CAE-PA
#   Getestet mit Python 3.5

import xml.etree.ElementTree as et
from enum import Enum

class XmlInterfaceService:
    def __init__(self, InterfaceNode):
        self.name = InterfaceNode.find('ServiceName').text
        self.opcName = InterfaceNode.find('OPC_UA_Methodenname').text
        self.continous = int(InterfaceNode.find('Konti').text)
        self.parameters = {}
        for paramNode in InterfaceNode.findall('parameter'):
            # paramType = paramNode.find('type').text
            paramType = 'not set'
            paramName = paramNode.find('parameterdesc').text
            paramVal = paramNode.find('defaultvalue').text

            self.parameters[paramName] = {'default': paramVal, 'type': paramType}

class XmlInterfaceModul:
    def __init__(self, InterfaceNode):
        self.name = InterfaceNode.find('Modulschnittstellenabfrage').text
        self.opcName = InterfaceNode.find('OPC_UA_Name').text
        self.position = int(InterfaceNode.find('Position').text)
        self.services = {}
        for service in InterfaceNode.findall('Dienst'):
            xmlService = XmlInterfaceService(service)
            self.services[xmlService.opcName] = xmlService

class XmlRecipeInterface:
    def __init__(self, InterfaceNode):
        self.name = InterfaceNode.find("Schnittstellenabfrage").text
        self.modules = {}
        for module in InterfaceNode.findall('Modulschnittstelle'):
            xmlModule = XmlInterfaceModul(module)
            self.modules[xmlModule.opcName] = xmlModule

    def getServiceInterface(self, ServiceName):
        for module in self.modules:
            for service in module.services:
                if service.name == ServiceName:
                    return service
        return None

class BlockType(Enum):
    SERIAL = 1
    PARALLEL = 2

class XmlRecipeServiceInstance:
    def __init__(self, Node, interface):
        self.name = Node.find('Service').text
        self.type = interface.getServiceInterface(self.name)
        self.parameters = []
        for p in Node.find('Parameter'):
            self.parameters.append({
                'type' : self.type.parameters[p.find('Name').text],
                'name' : self.type.parameters.name,
                'value': p.find('Value').text
            })

class XmlRecipeBlock(Enum):
    def __init__(self, Node, interface):
        self.name = Node.find('Name').text
        if Node.find('Type').text == 'SeriellerBlock':
            self.type = BlockType.SERIAL
        else:
            self.type = BlockType.PARALLEL
        self.childs = []
        for child in Node.find('Childs'):
            if child.tag == 'Dienst':
                self.childs.append(XmlRecipeServiceInstance(child, interface))
            if child.tag == 'Block':
                self.childs.append(XmlRecipeBlock(child, interface))

class XmlRecipeInstance:
    def __init__(self, Node, interface):
        self.name = Node.find('recipename').text
        #self.RunBlock = XmlRecipeBlock(Node.find('RunBlock', interface))
        #self.StopBlock = XmlRecipeBlock(Node.find('StopBlock', interface))


class XmlRecipeParser:
    def __init__(self, xmlFile):
        tree = et.parse(xmlFile)
        root = tree.getroot() #ComosXmlExport Element
        anlage = root.find('plant')
        self.interface = XmlRecipeInterface(anlage.find('interface'))
        self.recipe = XmlRecipeInstance(anlage.find('recipe'), self.interface)

class XmlTopologyParser:
    def __init__(self, xmlFile):
        tree = et.parse(xmlFile)
        root = tree.getroot() #ComosXmlExport Element
        anlage = root.find('plant')
        self.interface = XmlRecipeInterface(anlage.find('interface'))

