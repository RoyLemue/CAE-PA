# -*- coding: utf-8 -*-
#   Erstellt von Roy Ledermüller mit PyCharm Community Edition 
#   Erstelldatum:   05.05.2017
#   Projektname:    CAE-PA
#   Getestet mit Python 3.5


from enum import Enum
from opcua import Client, ua, Node
import os
import main.settings

from main.xmlmodels import *

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

class OpcService:

    def __init__(self, node, client):
        self.node = node
        self.stateNode = self.node.get_child(["1:CurrentState"])
        self.client = client
        self.commands = node.get_child(["1:Commands"])

        self.name = str(node.get_display_name().Text.decode("utf-8", "ignore"))
        self.stateMap = {}
        for state in node.get_child(["1:States"]).get_children():
            self.stateMap[state.nodeid] = STATE_MAP[state.get_display_name().Text]

        self.StateHandler = StateChangeHandler(self)
        self.sub = client.create_subscription(500, self.StateHandler)
        self.handle = self.sub.subscribe_data_change(self.stateNode)



        self.parameterNode = self.node.get_child(["1:ParameterList"])
        self.parameters = {}
        for p in self.parameterNode.get_children():
            self.parameters[p.get_display_name()] = p


    def setParam(self, name, value):
        self.parameters[name].set_value(value)

    @property
    def State(self):
        return self.__state

    def setState(self, nodeval):
        self.__state = self.stateMap[nodeval]
        self.Methods = []
        if self.__state in RUN_STATES:
            self.Methods.append(OpcMethod.HOLD)
        if  self.__state in NORMAL_STATES:
            self.Methods.append(OpcMethod.ABORT)
        if self.__state in ACTIVE_STATES:
            self.Methods.append(OpcMethod.STOP)

        if self.__state == OpcState.IDLE:
            self.Methods.append(OpcMethod.START)
        elif self.__state == OpcState.RUNNING:
            self.Methods.append(OpcMethod.PAUSE)
        elif self.__state == OpcState.PAUSED:
            self.Methods.append(OpcMethod.RESUME)
        elif self.__state == OpcState.HELD:
            self.Methods.append(OpcMethod.UNHOLD)
        elif self.__state == OpcState.ABORTED:
            self.Methods.append(OpcMethod.CLEAR)
        elif self.__state == OpcState.ABORTED or self.__state == OpcState.STOPPED or self.__state == OpcState.COMPLETE:
            self.Methods.append(OpcMethod.RESET)

    def StateChange(self):
        nodeval = self.stateNode.get_value()
        self.setState(nodeval)

    def callMethod(self, method):
        methodName = method.lower()
        recipeType = RECIPE_COMMAND[METHOD_MAP[methodName]]
        test = ''
        if self.State in recipeType.start:
            self.commands.call_method("1:"+method)





class OpcClient(Client):
    """
    Default Client-> connects to a Server-Module with Services
    """

    def __init__(self, adress, type):
        '''

        :param adress: Server Adress
        '''
        super(OpcClient, self).__init__(adress)

        self.connect()
        self.root = self.get_root_node()
        self.ServiceList = []  # list with opcServices
        self.type = type
        for service in self.root.get_child(["0:Objects","1:"+type,"1:ServiceList"]).get_children():
            self.ServiceList.append(OpcService(service, self))
    def getService(self, serviceName):
        for s in self.ServiceList:
            if s.name == serviceName:
                return s
        return None

    def __del__(self):
        self.disconnect()

class OpcPlant:
    def __init__(self, nodes):
        self.parts = {}
        for node in nodes:
            self.parts[node['name']] = OpcClient("opc.tcp://"+node['adress']+":" + node['port'], node['name'])

class StateChangeHandler(object):

    """
    Subscription Handler. To receive events from server for a subscription
    data_change and event methods are called directly from receiving thread.
    Do not do expensive, slow or network operation there. Create another
    thread if you need to do such a thing
    """
    def __init__(self, service):
        self.service = service

    def datachange_notification(self, node, val, data):
        self.service.setState(val)


class RecipeState(Enum):
    WAIT = 1
    RUN = 2
    FAILED = 3
    ABORTED = 4
    COMPLETED = 5

class RecipeCommand(Enum):
    START = 1
    STOP = 2
    PAUSE = 3

class RecipeElementState(Enum):
    WAITING = 1
    RUNNING = 2
    COMPLETED = 3
    ABORTED = 4

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

class RecipeElement:
    def __init__(self, service, method):
        self.service = service
        self.methodName = method.lower()
        self.type = RECIPE_COMMAND[METHOD_MAP[self.methodName]]
        self.state = RecipeElementState.WAITING

    def execute(self):
        if self.service.State in self.type.start:
            self.service.callMethod(self.methodName)

class Recipe:
    def __init__(self, filename):
        self.id = id
        self.filename = filename
        self.parser = XmlRecipeParser(filename)

class Topology:
    def __init__(self, filename):
        self.id = id
        self.fileName = filename
        self.parser = XmlTopologyParser(filename)

class BlockType(Enum):
    SERIAL = 1
    PARALLEL = 2

class RecipeHandler:
    instance = None
    def __init__(self, anlage):
        if not RecipeHandler.instance:
            RecipeHandler.instance = RecipeHandler.__RecipeHandler(anlage)
    def __getattr__(self, name):
        return getattr(self.instance, name)

    class __RecipeHandler:
        def __init__(self, anlage):
            self.recipes = []
            self.recipeId = 0
            self.anlage = anlage
            for file in os.listdir(main.settings.RECIPE_DIR):
                self.recipes.append(Recipe(os.path.join(main.settings.RECIPE_DIR,file)))
            self.topologyId = 0
            self.topologies = []
            for file in os.listdir(main.settings.TOPOLOGY_DIR):
                self.topologies.append(Topology(os.path.join(main.settings.TOPOLOGY_DIR,file)))
                self.topologyId += 1
            self.actualTopology = self.topologies[0]
            self.actualRecipe = None
            self.validTopology = self.checkTopology()

        #check opcua services
        def checkTopology(self):
            for module in self.actualTopology.parser.interface.modules:
                anlagenModul = self.anlage.parts[module.name]
                for service in module.services:
                    opcService = anlagenModul.getService(service.opcName)
                    if not opcService:
                        return False
                    else:
                        print(anlagenModul.name+' '+opcService.name+' gefunden')
            return True

        def startRecipe(self, recipeIndex):
            recipe = self.recipes[recipeIndex]
            for index, topoModule in self.actualTopology.interface.modules:
                recipeModule = recipe.interface.modules[index]
                if topoModule.position != recipeModule.position:
                    return {'status' : False, 'message' : 'Modulverschaltung des Rezeptes stimmt nicht mit aktueller Verschaltung überein'}
                for serviceIndex, topoService in topoModule.services:
                    if topoService.name != recipeModule.services[serviceIndex].name:
                        return {'status': False,
                                'message': 'Modulverschaltung des Rezeptes stimmt nicht mit aktueller Verschaltung überein'}
                    # TODO check parameter
            # walk trough Tree and create RecipeElements

        def __addRecipeElementOnChilds(self, node):
            for child in node.childs:
                if isinstance(child, XmlRecipeServiceInstance):
                    child.recipeElement = RecipeElement()



