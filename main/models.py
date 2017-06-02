# -*- coding: utf-8 -*-
#   Erstellt von Roy Ledermüller mit PyCharm Community Edition 
#   Erstelldatum:   05.05.2017
#   Projektname:    CAE-PA
#   Getestet mit Python 3.5


from . import settings
from enum import Enum, unique
from opcua import Client, ua, Node



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
        self.serviceList = []  # list with opcServices
        print(type)
        for service in self.root.get_child(["0:Objects","1:"+type,"1:ServiceList"]).get_children():
            self.serviceList.append(OpcService(service, self))


    def __del__(self):
        self.disconnect()



class OpcService:

    def __init__(self, node, client):
        self.stateNode = node.get_child(["1:CurrentState"])
        nodeval = node.get_child(["1:CurrentState"]).get_value()
        self.client = client
        self.commands = node.get_child(["1:Commands"])
        #TODO parse stateNode and subscribe currentState
        self.__state = STATE_MAP[self.client.get_node(nodeval).get_display_name().Text]
        print(str(node.get_display_name().Text)+" "+str(self.__state))

    def _start(self):
        assert self.__state == OpcState.IDLE
        self.commands.call_method("1:start")
        self.__state = OpcState.RUNNING
        #autocompletes if not continous

    def _stop(self):
        assert self.__state in ACTIVE_STATES
        self.__state = OpcState.STOPPING
        self.commands.call_method("1:stop")
        self.__state = OpcState.STOPPED

    def _pause(self):
        assert self.__state == OpcState.RUNNING
        self.__state = OpcState.PAUSING
        self.commands.call_method("1:pause")
        self.__state = OpcState.PAUSED

    def _resume(self):
        assert self.__state == OpcState.PAUSED
        self.commands.call_method("1:resume")
        self.__state = OpcState.RUNNING

    def _hold(self):
        assert self.__state in RUN_STATES
        self.__state = OpcState.HOLDING
        self.commands.call_method("1:hold")
        self.__state = OpcState.HELD

    def _unhold(self):
        assert self.__state == OpcState.HELD
        self.__state = OpcState.UNHOLDING
        self.commands.call_method("1:unhold")
        self.__state = OpcState.RUNNING

    def _reset(self):
        assert self.__state == OpcState.COMPLETE \
               or self.__state == OpcState.STOPPED
        self.commands.call_method("1:reset")
        self.__state = OpcState.IDLE

    def _abort(self):
        assert self.__state in NORMAL_STATES
        self.__state = OpcState.ABORTING
        self.commands.call_method("1:abort")
        self.__state = OpcState.ABORTED
    def _clear(self):
        assert self.__state == OpcState.ABORTED
        self.__state = OpcState.CLEARING
        self.commands.call_method("1:clear")
        self.__state = OpcState.STOPPED

