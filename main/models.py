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
    """
    The OpcPlant contains all the Modules with their Services.
    """
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

class RecipeElementThread(threading.Thread):
    def __init__(self,stdout, node, condition):
        threading.Thread.__init__(self)
        self.stdout = stdout
        self.stderr = None
        self.node = node
        self.node.state = RecipeElementState.WAITING
        self.condition = condition


    def run(self):
        print('start Element Thread, '+self.node.name+':'+self.node.methodName)

        if self.node.opcServiceNode.State not in self.node.type.start:
            self.condition.acquire()
            self.node.state = RecipeElementState.ABORTED
            self.condition.notify()  # wake the parent block handler thread
            self.condition.release()
            return

        self.node.state = RecipeElementState.RUNNING
        print('call Method')
        self.node.opcServiceNode.callMethod(self.node.methodName)
        validStates = self.node.type.running + self.node.type.start + self.node.type.complete
        while self.node.opcServiceNode.State not in self.node.type.complete:
            stateCopy = self.node.opcServiceNode.State
            if stateCopy not in validStates:
                self.condition.acquire()
                print(self.node.opcServiceNode.State in self.node.type.complete)
                print(self.node.opcServiceNode.State in self.node.type.running)
                self.node.state = RecipeElementState.ABORTED
                self.condition.notify()
                self.condition.release() # wake the parent block handler thread
                return
        self.condition.acquire()
        self.node.state = RecipeElementState.COMPLETED
        self.condition.notify()
        self.condition.release() # wake the parent block handler thread
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
        self.condition = condition
    def run(self):
        print('start Tree Thread, '+self.root.name)
        self.root.state = RecipeElementState.RUNNING
        if self.executeServiceTree(self.root):
            self.root.state = RecipeElementState.COMPLETED
        else:
            self.root.state = RecipeElementState.ABORTED
        print('end Tree Thread, '+self.root.name)
        self.condition.acquire() # lock
        self.condition.notify()
        self.condition.release() # unlock

    def executeService(self, serviceNode):
        condition = threading.Condition()
        condition.acquire() # lock
        re = RecipeElementThread(sys.stdout, serviceNode, condition)
        re.start()
        condition.wait(serviceNode.timeout) # unlock, relock on notify or timeout
        condition.release()
        if serviceNode.state != RecipeElementState.COMPLETED:
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
            else:
                return True

        for elementId in parentNode.sortList:
            node = parentNode.childs[elementId]
            if isinstance(node, XmlRecipeBlock):
                if node.blockType == 'ParallelerBlock':
                    threadCount = len(node.childs)
                    condition = threading.Condition()
                    condition.acquire() # lock
                    threads = []
                    for p in node.childs.values():
                        thread = RecipeTreeThread(self.stdout, p, condition)
                        threads.append(thread)
                        thread.start()
                    #wait for every block finished
                    while  threadCount > 0:
                        condition.wait() # unlock, lock if awaken
                        threadCount -=1
                    # all Threads finished, check normal Complete
                    condition.release()
                    for thread in threads:
                        if thread.root.state != RecipeElementState.COMPLETED:
                            logger.error('Child Thread failed')
                            node.state = RecipeElementState.ABORTED
                            return False
                    node.state = RecipeElementState.COMPLETED

                if node.blockType == 'SeriellerBlock':
                    runningNormal = self.executeServiceTree(node)
                    if runningNormal == False:
                        logger.error('Serial-Block failed')
                        node.state = RecipeElementState.ABORTED
                        return False
                    node.state = RecipeElementState.COMPLETED
            elif isinstance(node, XmlRecipeServiceInstance):
                self.executeService(node)
                if node.state == RecipeElementState.ABORTED:
                    return False

        return True

class RecipeRootThread(threading.Thread):
    """
    Extra Thread to separate Blocking from Non-Blocking.
    Server -> RecipeHandler -> starts Root Thread -> respsonse
    Root Thread waits until Recipe is finished. Simply start a Tree Thread.
    """
    def __init__(self,stdout, recipe):
        threading.Thread.__init__(self)
        self.stdout = stdout
        self.recipeParser = recipe

    def run(self):
        runBlockNode = self.recipeParser.recipe.runBlock
        print('start Root Recipe Thread, '+self.recipeParser.recipe.name)
        condition = threading.Condition()
        condition.acquire() # lock

        thread = RecipeTreeThread(self.stdout, runBlockNode, condition)
        thread.start()
        condition.wait() # unlock, relock if awaken
        condition.release() # unlock
        RecipeHandler.instance.finishRecipe()
        print('end Root Recipe Thread, ' + self.recipeParser.recipe.name)


class RecipeFileObject:
    def __init__(self, filename):
        self.fileName = filename
    def getParsed(self, topology, plant):
        return XmlRecipeParser(self.fileName, topology, plant)

class TopologyFileObject:
    def __init__(self, filename):
        self.fileName = filename
    def getParsed(self, plant):
        return XmlTopologyParser(self.fileName, plant)




class RecipeHandler:
    """
    Singleton Pattern
    The Handler is responsible for the Recipes and the Topologies.
    Also the Execution of the Recipes.
    It is initialized with an OpcPlant
    """
    anlage = None
    instance = None
    def __init__(self):
        if not RecipeHandler.instance:
            RecipeHandler.instance = RecipeHandler.__RecipeHandler(RecipeHandler.anlage)
    def __getattr__(name):
        return getattr(RecipeHandler.instance, name)

    class __RecipeQueueThread(threading.Thread):
        def __init__(self, stdout, recipeQueue):
            threading.Thread.__init__(self)
            self.stdout = stdout
            self.stderr = None
            self.recipeQueue = recipeQueue
        def run(self):
            """
            Executes all ThreadElements after another.
            Was just for debugging.
            :return:
            """
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
            Loads a Recipe from the Recipe-Directory with given Filename and returnes the parsed RecipeFileObject.
            :param filename: Name of a File in the Recipe Directory
            :return: parsed XmlRecipeParser
            """
            return RecipeFileObject(os.path.join(main.settings.RECIPE_DIR,filename)).getParsed(self.actualTopology, self.anlage)

        def __init__(self, anlage):
            self.recipes = []
            self.actualRecipeThread = None
            self.completeRecipe = None
            self.anlage = anlage
          #  for file in os.listdir(main.settings.RECIPE_DIR):
          #      self.recipes.append(Recipe(os.path.join(main.settings.RECIPE_DIR,file)))
            self.topologyId = 0
            self.topologies = []
            for file in os.listdir(main.settings.TOPOLOGY_DIR):
                self.topologies.append(TopologyFileObject(os.path.join(main.settings.TOPOLOGY_DIR,file)))
                self.topologyId += 1
            parsedTopology = self.topologies[0].getParsed(self.anlage)
            if parsedTopology.isValid:
                self.actualTopology = parsedTopology
            else:
                logger.error("Invalid Topology")
            self.active = False

        def startRecipeFromFilename(self, filename):
            """
            Create RecipeFileObject and starts it with an RecipeRootThread,
            if the FileObject is valid and no other Recipe is active.
            :param filename: Name of a File in the Recipe Directory
            :return: XmlRecipeParser
            """
            recipe = RecipeFileObject(os.path.join(main.settings.RECIPE_DIR, filename)).getParsed(self.actualTopology, self.anlage)
            if recipe.isValid:
                if self.actualRecipeThread == None:
                    thread = RecipeRootThread(sys.stdout, recipe)
                    self.actualRecipeThread = thread
                    thread.start()
                else:
                    self.message = 'Rezept läuft noch.'
                    return False
            else:
                self.message = recipe.message
                return False
            return True

        def finishRecipe(self):
            """
            "Callback" is started by RecipeRootThread when all RecipeSteps are finished or the Recipe is aborted.
            :return:
            """
            self.completeRecipe = self.actualRecipeThread
            self.actualRecipeThread = None

        def getServices(self, recipeNode):
            """
            Gets a List with all Service-Calls from a given Recipe-Tree. Order is probably not right and parallelBlocks are serialized.
            Just for Debugging.
            :param recipeNode:
            :return:
            """
            services = []
            for child in recipeNode.childs.values():
                if isinstance(child, XmlRecipeBlock):
                    services.append(self.getServices(child))
                elif isinstance(child, XmlRecipeServiceInstance):
                    services.append(child)
            return services

        def startRecipeWithQueue(self, recipeElements):
            """
            Starts a QueueThread with the given Limain.settings.
            :param recipeElements: List of RecipeElementThreads
            :return: None
            """
            thread = RecipeHandler.__RecipeQueueThread(sys.stdout, recipeElements)
            thread.start()


        """
        TODO Upload files with json and check xml syntax (not the topology)
        and dont read directory every Get-Request (make the lists persistent)
        """
        def saveUploadedRecipe(self, file):
            """
            Copies the uploaded File from the tempDir to the RecipeDir
            :param file: Uploaded File Handle
            :return:
            """
            filename =  str(file)
            with open(os.path.join(main.settings.RECIPE_DIR, filename), 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

        def saveUploadedTopology(self, file):
            """
            Copies the uploaded File from the tempDir to the RecipeDir
            :param file: Uploaded File Handle
            :return:
            """
            filename =  str(file)
            with open(os.path.join(main.settings.TOPOLOGY_DIR, filename), 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)