# -*- coding: utf-8 -*-
#   Erstellt von Roy Ledermüller mit PyCharm Community Edition 
#   Erstelldatum:   05.05.2017
#   Projektname:    CAE-PA
#   Getestet mit Python 3.5


from enum import Enum, unique
from opcua import Client, ua, Node

MIXER_NAME = "mixer"
REACTOR_NAME = "reactor"

MIXER_PORT = 4840
REACTOR_PORT = 4842

print("models")

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


    def __del__(self):
        self.disconnect()

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
        self.service.StateChange()

    def event_notification(self, event):
        print("Python: New event", event)



class OpcService:

    def __init__(self, node, client):
        self.node = node
        self.stateNode = self.node.get_child(["1:CurrentState"])
        self.client = client
        self.commands = node.get_child(["1:Commands"])
        #TODO parse stateNode and subscribe currentState

        self.name = str(node.get_display_name().Text.decode("utf-8", "ignore"))
        self.StateChange()

        #self.StateHandler = StateChangeHandler(self)
        #self.sub = client.create_subscription(500, self.StateHandler)
        #self.handle = self.sub.subscribe_data_change(self.stateNode)

    @property
    def State(self):
        nodeval = self.stateNode.get_value()
        state = STATE_MAP[self.client.get_node(nodeval).get_display_name().Text]

        self.Methods = []
        if state in RUN_STATES:
            self.Methods.append(OpcMethod.HOLD)
        if  state in NORMAL_STATES:
            self.Methods.append(OpcMethod.ABORT)
        if state in ACTIVE_STATES:
            self.Methods.append(OpcMethod.STOP)

        if state == OpcState.IDLE:
            self.Methods.append(OpcMethod.START)
        elif state == OpcState.RUNNING:
            self.Methods.append(OpcMethod.PAUSE)
        elif state == OpcState.PAUSED:
            self.Methods.append(OpcMethod.RESUME)
        elif state == OpcState.HELD:
            self.Methods.append(OpcMethod.UNHOLD)
        elif state == OpcState.ABORTED:
            self.Methods.append(OpcMethod.CLEAR)
        elif state == OpcState.ABORTED or state == OpcState.STOPPED or state == OpcState.COMPLETE:
            self.Methods.append(OpcMethod.RESET)

        return state

    def StateChange(self):
        state = self.State
        self.Methods = []
        if state in RUN_STATES:
            self.Methods.append(OpcMethod.HOLD)
        if  state in NORMAL_STATES:
            self.Methods.append(OpcMethod.ABORT)
        if state in ACTIVE_STATES:
            self.Methods.append(OpcMethod.STOP)

        if state == OpcState.IDLE:
            self.Methods.append(OpcMethod.START)
        elif state == OpcState.RUNNING:
            self.Methods.append(OpcMethod.PAUSE)
        elif state == OpcState.PAUSED:
            self.Methods.append(OpcMethod.RESUME)
        elif state == OpcState.HELD:
            self.Methods.append(OpcMethod.UNHOLD)
        elif state == OpcState.ABORTED:
            self.Methods.append(OpcMethod.CLEAR)
        elif state == OpcState.ABORTED or state == OpcState.STOPPED or state == OpcState.COMPLETE:
            self.Methods.append(OpcMethod.RESET)

    def _start(self):
        s = self.State
        assert s.value == OpcState.IDLE.value
        self.commands.call_method("1:start")
        #autocompletes if not continous

    def _stop(self):
        assert self.State in ACTIVE_STATES
        self.commands.call_method("1:stop")

    def _pause(self):
        assert self.State == OpcState.RUNNING
        self.commands.call_method("1:pause")

    def _resume(self):
        assert self.State == OpcState.PAUSED
        self.commands.call_method("1:resume")

    def _hold(self):
        assert self.State in RUN_STATES
        self.commands.call_method("1:hold")

    def _unhold(self):
        assert self.State == OpcState.HELD
        self.commands.call_method("1:unhold")

    def _reset(self):
        assert self.State == OpcState.COMPLETE \
               or self.State == OpcState.STOPPED
        self.commands.call_method("1:reset")

    def _abort(self):
        assert self.State in NORMAL_STATES
        self.commands.call_method("1:abort")
    def _clear(self):
        assert self.State == OpcState.ABORTED
        self.commands.call_method("1:clear")
