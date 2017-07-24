# -*- coding: utf-8 -*-
#   Erstellt von Roy Ledermüller mit PyCharm Community Edition 
#   Erstelldatum:   03.05.2017
#   Projektname:    FSR_Studienordnung
#   Getestet mit Python 3.5

from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
#from .forms import *
from .models import *
from .settings import *
from .urls import *
from .jsonencoders import JsonDataEncoder
import os, json
import logging

logger = logging.getLogger('django')

@login_required
def getState(request, moduleName, serviceName):
    TeilAnlage = RecipeHandler.instance.anlage
    service = TeilAnlage.parts[moduleName].getService(serviceName)
    stringMethods = []
    for m in service.Methods:
        stringMethods.append(str(m).split('.')[1])
    return JsonResponse({'status' : 'OK', 'state' : str(service.State).split('.')[1], 'methods' : stringMethods})

def getJsonInformation(request):
    TeilAnlage = RecipeHandler.instance.anlage
    if(RecipeHandler.instance.actualRecipeThread):
        recipe = RecipeHandler.instance.actualRecipeThread.recipe
    elif(RecipeHandler.instance.completeRecipe):
        recipe = RecipeHandler.instance.completeRecipe
    else:
        recipe = None
    #RecipeHandler.instance.startRecipeFromFilename('opcRecipe2.XML')
    encoder =JsonDataEncoder()
    jsonData = encoder.encode({'status': 'OK',
            'anlage': TeilAnlage.parts,
            'recipe': recipe,
            'topology':RecipeHandler.instance.actualTopology})

    return JsonResponse(jsonData)

@login_required
def methodCall(request, moduleName, serviceName, methodName):
    """
    Json Command to call a Service-Method via OpcClient.
    :param request:
    :param moduleName:
    :param serviceName:
    :param methodName:
    :return:
    """
    TeilAnlage = RecipeHandler.instance.anlage
    methodName = methodName.lower()
    if methodName in METHOD_MAP.keys():
        service = TeilAnlage.parts[moduleName].getService(serviceName)
        service.callMethod(methodName)
        state = service.State
        return JsonResponse({'status' : 'OK', 'state' : str(state).split('.')[1]})
    return JsonResponse({'status' : 'ERROR'})

@login_required
def home(request):
    """
    Get the default view.
    :param request:
    :return:
    """
    recipes = []
    for file in os.listdir(RECIPE_DIR):
        recipes.append(file)

    topologies = []
    for file in os.listdir(TOPOLOGY_DIR):
            topologies.append(file)
    TeilAnlage = RecipeHandler.instance.anlage
    return TemplateResponse(request, 'Home.html', {"Teilanlage" : TeilAnlage, "Recipes" : recipes, 'Topologies' : topologies })

@login_required
def uploadRecipes(request):
    #TODO check form name
    if request.method == 'POST':
        RecipeHandler.instance.saveUploadedRecipe(request.FILES['file'])

    return HttpResponseRedirect('/')

@login_required
def uploadStructure(request):
    #TODO check form name
    if request.method == 'POST':
        RecipeHandler.instance.saveUploadedTopology(request.FILES['file'])
    return HttpResponseRedirect('/')
    #return home(request)

@login_required
def showExample(request):
    """
    UnitTest to execute single RecipeQueue
    :param request:
    :return:
    """
    recipes = []
    for file in os.listdir(RECIPE_DIR):
        recipes.append(file)

    topologies = []
    for file in os.listdir(TOPOLOGY_DIR):
            topologies.append(file)

    TeilAnlage = RecipeHandler.instance.anlage

    fillService = TeilAnlage.parts['Mixer'].getService('fill')
    doseService = TeilAnlage.parts['Mixer'].getService('dose')
    dispenseService = TeilAnlage.parts['Mixer'].getService('dispense')
    recipeQueue = [
        RecipeElementThread(sys.stdout, fillService, 'start'),
        RecipeElementThread(sys.stdout, doseService, 'start'),
        RecipeElementThread(sys.stdout, fillService, 'reset'),
        RecipeElementThread(sys.stdout, doseService, 'stop'),  # has to be stopped before dispense
        RecipeElementThread(sys.stdout, doseService, 'reset'),
        RecipeElementThread(sys.stdout, dispenseService, 'start'),
        RecipeElementThread(sys.stdout, dispenseService, 'reset'),
        RecipeElementThread(sys.stdout, doseService, 'reset'),
    ]
    RecipeHandler.instance.startRecipeWithQueue(recipeQueue)
    return TemplateResponse(request, 'Example.html', {"Teilanlage": TeilAnlage, "Recipes": recipes})


@login_required
def recipeStart(request, recipeName):
    if RecipeHandler.instance.startRecipeFromFilename(recipeName):
        return JsonResponse({'status' : 'OK'})
    return JsonResponse({'status': 'ERROR', 'message': RecipeHandler.instance.message})

@login_required
def recipeParse(request, recipeName):
    parsedRecipe = RecipeHandler.instance.parseRecipe(recipeName)
    if parsedRecipe.isValid:
        return JsonResponse({'status' : 'OK',})
    return JsonResponse({'status': 'ERROR', 'message': parsedRecipe.message})





