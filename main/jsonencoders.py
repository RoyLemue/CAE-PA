# -*- coding: utf-8 -*-
#   Erstellt von Roy Ledermüller mit PyCharm Community Edition
#   Erstelldatum:   05.07.2017
#   Projektname:    CAE-PA
#   Getestet mit Python 3.5

from django.core.serializers.json import DjangoJSONEncoder
from .models import *
from .xmlmodels import *
import json

class JsonDataEncoder:
    def encode(self, obj):
        if isinstance(obj, list):
            p = []
            for val in obj:
                p.append(self.encode(val))
            return p
        elif isinstance(obj, dict):
            p = {}
            # version dependent
            for key, value in obj.items():
                p[key] = self.encode(value)
            return p
        elif isinstance(obj, OpcPlant):
            return self.encode(obj.parts)

        elif isinstance(obj, OpcService):
            return {
            'name' : obj.name,
            'module': obj.client.opcName,
            'state': self.encode(obj.State),
            'methods': self.encode(obj.getMethods()),
            'parameters': self.encode(obj.parameters)
        }
        elif isinstance(obj, OpcClient):
            return {
            'name' : obj.opcName,
            'services': self.encode(obj.ServiceList)
        }

        elif isinstance(obj, XmlRecipeParser):
            return {
            'valid': obj.isValid,
            'instance': self.encode(obj.recipe),
            'interface': self.encode(obj.interface)
        }
        elif isinstance(obj, RecipeType):
            return {
            'start': self.encode(obj.start),
            'running': self.encode(obj.running),
            'complete': self.encode(obj.complete)
        }
        elif isinstance(obj, RecipeElementThread):
            return {
            'method': obj.methodName,
            'service': obj.service.name,
            'type': self.encode(obj.type),
            'state': self.encode(obj.state),
            'timeout': obj.timeout
            }
        elif isinstance(obj, XmlTopologyParser):
            return self.encode({
            'valid': obj.isValid,
            'interface': self.encode(obj.interface)
        })
        elif isinstance(obj, XmlRecipeInstance):
            return {
            'name': obj.name,
            'date': obj.date,
            'author': obj.author,
            'runBlock': self.encode(obj.runBlock)
        }
        elif isinstance(obj, XmlRecipeBlock):
            return {
            'name': obj.name,
            'type': obj.blockType,
            'childs': self.encode(obj.childs),
            'state': self.encode(obj.state),
            'order': self.encode(obj.sortList),
        }
        elif isinstance(obj, XmlRecipeServiceInstance):
            return {
            'name': obj.name,
            'method' : obj.method,
            'state': self.encode(obj.state),
            'serviceType': self.encode(obj.type),
            'timeout': obj.timeout,
            'opcService': self.encode(obj.opcServiceNode)
        }
        elif isinstance(obj, XmlRecipeInterface):
            return {
            'name': obj.name,
            'modules': self.encode(obj.modules)
        }
        elif isinstance(obj, XmlInterfaceModul):
            return {
            'name': obj.name,
            'position': obj.position,
            'services': self.encode(obj.services)
        }
        elif isinstance(obj, XmlInterfaceService):
            return {
            'name': obj.name,
            'opcName': obj.opcName,
            'continous': obj.continous,
            'parameters': self.encode(obj.parameters)
        }
        elif isinstance(obj, RecipeTreeThread):
            return {
                "state" : obj.state,
                "root" : obj.root
            }
        elif isinstance(obj, OpcState):
            return str(obj)
        elif isinstance(obj, OpcMethod):
            return str(obj)
        elif isinstance(obj, RecipeState):
            return str(obj)
        elif isinstance(obj, RecipeCommand):
            return str(obj)
        elif isinstance(obj, RecipeElementState):
            return str(obj)
        elif isinstance(obj, BlockType):
            return str(obj)
        return obj

