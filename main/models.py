# -*- coding: utf-8 -*-
#   Erstellt von Roy Ledermüller mit PyCharm Community Edition 
#   Erstelldatum:   05.05.2017
#   Projektname:    CAE-PA
#   Getestet mit Python 3.5


from enum import Enum
from opcua import Client, ua, Node
import os, sys, time, json
import main.settings
import xml.etree.ElementTree as et

from main.xmlmodels import *
import threading

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
        self.sub = client.create_subscription(200, self.StateHandler)
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
        if self.State in recipeType.start:
            # call from opcua node
            self.commands.call_method("1:"+method)

    def getMethods(self):
        return self.Methods

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
        self.ServiceList = {}  # list with opcServices
        self.opcName = type
        for service in self.root.get_child(["0:Objects","1:"+type,"1:ServiceList"]).get_children():
            obj = OpcService(service, self)
            self.ServiceList[obj.name] = obj
    def getService(self, serviceName):
        return self.ServiceList[serviceName]

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

class RecipeElementThread(threading.Thread):
    def __init__(self,stdout, node, condition):
        threading.Thread.__init__(self)
        self.stdout = stdout
        self.stderr = None
        self.node = node
        self.methodName = node.method.lower()
        self.type = RECIPE_COMMAND[METHOD_MAP[self.methodName]]
        self.condition = condition

    def run(self):
        self.condition.acquire()
        print('start Element Thread, '+self.node.name+':'+self.methodName)
        self.node.state = RecipeElementState.RUNNING
        self.node.opcServiceNode.callMethod(self.methodName)
        while self.node.opcServiceNode.State not in self.type.complete:
            pass
        self.condition.notify() # wake the parent block handler thread
        self.condition.release()
        print('end Element Thread, ' + self.node.name)

class RecipeTreeThread(threading.Thread):
    """
    Separated Thread iterating trought the Block Elements.
    Waits till all parallel elements are finished.
    """
    def __init__(self, stdout, recipeRoot, condition):
        """

        :param stdout: normally sys.stdout
        :param recipeRoot: Parent XmlNode
        :param condition: Thread.Condition to wait until a Thread is finished
        """
        threading.Thread.__init__(self)
        self.stdout = stdout
        self.stderr = None
        self.root = recipeRoot
        self.state = RecipeElementState.WAITING
        self.condition = condition
    def run(self):
        self.condition.acquire()
        print('start Tree Thread, '+self.root.name)
        self.state = RecipeElementState.RUNNING
        self.executeServiceTree(self.root)
        self.state = RecipeElementState.COMPLETED
        print('end Tree Thread, '+self.root.name)
        self.condition.notify()
        self.condition.release()

    def executeService(self, serviceNode):
        condition = threading.Condition()
        condition.acquire()
        timeout = 10.0
        re = RecipeElementThread(sys.stdout, serviceNode, condition)
        re.start()
        condition.wait(serviceNode.timeout)
        condition.release()
        if not re.is_alive() and serviceNode.opcServiceNode.State in re.type.complete:
            serviceNode.state = RecipeElementState.COMPLETED
        else:
            serviceNode.state = RecipeElementState.ABORTED
            if re.is_alive():
                logger.error('TimeOut Thrown, MethodCall went too long')
                # TODO Set Kill instructions
                # re.stop()
            else:
                logger.error('Service State has not a valid CompleteState for the Method')
                return False

    def executeServiceTree(self, parentNode):
        """
        :param parentNode: XmlRecipeBlock
        :return: True, if all went good
        """

        # for ParallelBlocks, could be optimized if started directly
        # but Threadhandling differs (see executeService)
        if isinstance(parentNode, XmlRecipeServiceInstance):
            self.executeService(parentNode)
            if parentNode.state == RecipeElementState.ABORTED:
                self.state = parentNode.state
                return False

        for elementId in parentNode.sortList:
            node = parentNode.childs[elementId]
            if isinstance(node, XmlRecipeBlock):
                if node.blockType == 'ParallelerBlock':
                    threadCount = len(node.childs)
                    condition = threading.Condition()
                    condition.acquire()
                    threads = []
                    for p in node.childs.values():
                        thread = RecipeTreeThread(self.stdout, p, condition)
                        threads.append(thread)
                        thread.start()
                    #wait for finish
                    while  threadCount > 0:
                        condition.wait()
                        threadCount -=1
                    # all Threads finished, check normal Complete
                    condition.release()
                    for thread in threads:
                        if thread.state != RecipeElementState.COMPLETED:
                            logger.error('Child Thread failed')
                            return False

                if node.blockType == 'SeriellerBlock':
                    runningNormal = self.executeServiceTree(node)
                    if runningNormal == False:
                        logger.error('Serial-Block failed')
                        return False
            elif isinstance(node, XmlRecipeServiceInstance):
                self.executeService(node)
                if node.state == RecipeElementState.ABORTED:
                    self.state = node.state
                    return False

        return True

class RecipeRootThread(threading.Thread):
    """
    Extra Thread to separate Blocking from Non-Blocking.
    Server -> RecipeHandler -> starts Root Thread -> respsonse
    Root Thread waits until Recipe is finished. Simply start a Tree Thread.
    """
    def __init__(self,stdout, node):
        threading.Thread.__init__(self)
        self.stdout = stdout
        self.node = node

    def run(self):
        print('start Root Recipe Thread, '+self.node.name)
        condition = threading.Condition()
        condition.acquire()

        thread = RecipeTreeThread(self.stdout, self.node, condition)
        thread.start()
        condition.wait()
        condition.release()
        print('end Root Recipe Thread, ' + self.node.name)


class RecipeFileObject:
    def __init__(self, filename):
        self.fileName = filename
        try:
            self.parser = XmlRecipeParser(filename)
        except et.ParseError or et.KeyError or et.AttributeError as e:
            logger.error(e)

class TopologyFileObject:
    def __init__(self, filename):
        self.fileName = filename
        try:
            self.parser = XmlTopologyParser(filename)
        except et.ParseError or et.KeyError or et.AttributeError as e:
            logger.error(e)



class RecipeHandler:
    instance = None
    def __init__(self, anlage):
        if not RecipeHandler.instance:
            RecipeHandler.instance = RecipeHandler.__RecipeHandler(anlage)
    def __getattr__(self, name):
        return getattr(self.instance, name)

    class __RecipeQueueThread(threading.Thread):
        def __init__(self, stdout, recipeQueue):
            threading.Thread.__init__(self)
            self.stdout = stdout
            self.stderr = None
            self.recipeQueue = recipeQueue
        def run(self):
            for re in self.recipeQueue:
                startTime = time.clock()
                elapsedTime = 0
                re.start()
                re.join(timeout = re.timeout)
                while re.isAlive():
                    pass

                if re.service.State in re.type.complete:
                    self.state = RecipeElementState.COMPLETED
                else:
                    self.state = RecipeElementState.ABORTED

    class __RecipeHandler:


        def parseRecipe (self,filename):
            """
            :param filename: Name of a File in the Recipe Directory
            :return: parsed RecipeFileObject
            """
            return RecipeFileObject(os.path.join(main.settings.RECIPE_DIR,filename))

        def __init__(self, anlage):
            self.recipes = []
            self.actualRecipeId = -1
            self.anlage = anlage
          #  for file in os.listdir(main.settings.RECIPE_DIR):
          #      self.recipes.append(Recipe(os.path.join(main.settings.RECIPE_DIR,file)))
            self.topologyId = 0
            self.topologies = []
            for file in os.listdir(main.settings.TOPOLOGY_DIR):
                self.topologies.append(TopologyFileObject(os.path.join(main.settings.TOPOLOGY_DIR,file)))
                self.topologyId += 1
            if self.checkTopology(self.topologies[0]):
                self.actualTopology = self.topologies[0]
            else:
                logger.error("Invalid Topology")
            self.active = False

        def checkTopology(self, topology):
            """
            check topology against opcua namespace
            :param topology: TopologyFileObject
            :return Boolean: True when Topology is valid
            """
            lostServices = 0
            for module in topology.parser.interface.modules.values():
                anlagenModul = self.anlage.parts[module.name]
                for service in module.services.values():
                    opcService = anlagenModul.getService(service.opcName)
                    if not opcService:
                        logger.info(service.opcName + ' nicht gefunden')
                        lostServices +=1
                    else:
                        logger.info(anlagenModul.name+' '+opcService.name+' gefunden')
            if lostServices == 0:
                return True
            else:
                return False

        def checkRecipe(self, recipe):
            """
            check Recipe against Topology
            :param recipe: RecipeFileObject
            :return Boolean: True when Topology is valid
            """
            for index, topoModule in self.actualTopology.interface.modules:
                recipeModule = recipe.interface.modules[index]
                if topoModule.position != recipeModule.position:
                    logger.error('Modulverschaltung des Rezeptes stimmt nicht mit aktueller Verschaltung überein')
                    return False
                for serviceIndex, topoService in topoModule.services:
                    if topoService.opcName != recipeModule.services[serviceIndex].name:
                        logger.error('Modulverschaltung des Rezeptes stimmt nicht mit aktueller Verschaltung überein')
                        return False
            return True

        def startRecipeFromFilename(self, filename):
            recipe = RecipeFileObject(os.path.join(main.settings.RECIPE_DIR, filename))
            thread = RecipeRootThread(sys.stdout, recipe.parser.recipe.runBlock)
            self.actualRecipeThread = thread
            thread.start()
            # Do not Wait, maybe set a Callback?
            self.actualRecipeThread = None



        def getServices(self, recipeNode):
            services = []
            for child in recipeNode.childs.values():
                if isinstance(child, XmlRecipeBlock):
                    services.append(self.getServices(child))
                elif isinstance(child, XmlRecipeServiceInstance):
                    services.append(child)
            return services

        def startRecipeWithQueue(self, recipeElements):
            for re in recipeElements:
                topoService = self.actualTopology.parser.interface.modules[re.service.client.type].services[re.service.opcName]
                if topoService.continous == False and OpcState.IDLE in re.type.start:
                    re.type = RecipeType([OpcState.IDLE], [OpcState.STARTING, OpcState.RUNNING, OpcState.PAUSING, OpcState.PAUSED], [OpcState.COMPLETE])

            thread = RecipeHandler.__RecipeQueueThread(sys.stdout, recipeElements)
            thread.start()

