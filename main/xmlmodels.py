# -*- coding: utf-8 -*-
#   Erstellt von Roy Ledermüller mit PyCharm Community Edition
#   Erstelldatum:   05.07.2017
#   Projektname:    CAE-PA
#   Getestet mit Python 3.5

import xml.etree.ElementTree as et
from enum import Enum

class XmlServiceInterface:
    def __init__(self, InterfaceNode):
        self.name = InterfaceNode.find('ServiceName').text
        self.opcName = InterfaceNode.find('OPC_UA_Methodenname').text
        self.continous = bool(InterfaceNode.find('Konti').text)
        self.parameters = {}
        for paramNode in InterfaceNode.findall('parameter'):
            paramType = paramNode.find('type').text
            paramName = paramNode.find('name').text
            self.parameters[paramName] = paramType

class XmlModulInterface:
    def __init__(self, InterfaceNode):
        self.name = InterfaceNode.find('Modulschnittstellenabfrage').text
        self.opcName = InterfaceNode.find('OPC_UA_Name').text
        self.services = []
        for service in InterfaceNode.findall('Dienst'):
            self.services.append(XmlServiceInterface(service))

class XmlRecipeInterface:
    def __init__(self, InterfaceNode):
        self.name = InterfaceNode.find("Schnittstellenabfrage").text
        self.modules = []
        for module in InterfaceNode.findall('Modulschnittstelle'):
            self.modules.append(XmlModulInterface(module))

    def getServiceInterface(self, ServiceName):
        for module in self.modules:
            for service in module.services:
                if service.name == ServiceName:
                    return service
        return None

class BlockType(Enum):
    SERIAL = 1
    PARALLEL = 2

class XmlServiceInstance:
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

class XmlBlock(Enum):
    def __init__(self, Node, interface):
        self.name = Node.find('Name').text
        if Node.find('Type').text == 'SeriellerBlock':
            self.type = BlockType.SERIAL
        else:
            self.type = BlockType.PARALLEL
        self.childs = []
        for child in Node.find('Childs'):
            if child.tag == 'Dienst':
                self.childs.append(XmlServiceInstance(child, interface))
            if child.tag == 'Block':
                self.childs.append(XmlBlock(child, interface))

class XmlRecipeInstance:
    def __init__(self, Node, interface):
        self.name = Node.find('Rezeptname').text
        self.RunBlock = XmlBlock(Node.find('RunBlock', interface))
        self.StopBlock = XmlBlock(Node.find('StopBlock', interface))


class XmlParser:
    def __init__(self, xmlFile):
        tree = et.parse(xmlFile)
        root = tree.getroot() #ComosXmlExport Element
        anlage = root.find('plant')
        self.interface = XmlRecipeInterface(anlage.find('interface'))
        self.recipe = XmlRecipeInstance(anlage.find('recipe'), self.interface)
