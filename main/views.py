# -*- coding: utf-8 -*-
#   Erstellt von Roy Ledermüller mit PyCharm Community Edition 
#   Erstelldatum:   03.05.2017
#   Projektname:    FSR_Studienordnung
#   Getestet mit Python 3.5

from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from django.http import JsonResponse, HttpResponse
#from .forms import *
from .models import *
from .settings import *
from .urls import *
from .jsonencoders import JsonDataEncoder
import os, json
import logging

logger = logging.getLogger('django')

print("views")
@login_required
def jsonMethodCall(request):
    module = request.post.get("modul")
    service = request.post.get("service")
    method = request.post.get("method")
    return JsonResponse({'status' : 'OK'})

@login_required
def recipePause(request, recipeName):
    module = request.post.get("modul")
    service = request.post.get("service")
    method = request.post.get("method")
    TeilAnlage
    return JsonResponse({'status' : 'OK'})

@login_required
def recipeStop(request, recipeName):
    module = request.post.get("modul")
    service = request.post.get("service")
    method = request.post.get("method")
    TeilAnlage
    return JsonResponse({'status' : 'OK'}, encoder=JsonDataEncoder)

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
    encoder =JsonDataEncoder()
    jsonData = encoder.encode({'status': 'OK',
            'anlage': TeilAnlage.parts,
            'recipe': recipeQueue,
            'topology':RecipeHandler.instance.actualTopology})

    return JsonResponse(jsonData)

@login_required
def methodCall(request, moduleName, serviceName, methodName):
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
    recipes = []
    for file in os.listdir(RECIPE_DIR):
        recipes.append(file)

    topologies = []
    for file in os.listdir(TOPOLOGY_DIR):
            topologies.append(file)
    TeilAnlage = RecipeHandler.instance.anlage
    return TemplateResponse(request, 'Home.html', {"Teilanlage" : TeilAnlage, "Recipes" : recipes, 'Topologies' : topologies })

def uploadRecipes(request):
    if request.method == 'POST':
        handle_uploaded_recipe(request.FILES['file'], str(request.FILES['file']))

        recipes = []
        for file in os.listdir(RECIPE_DIR):
            recipes.append(file)

    return TemplateResponse(request, 'Home.html', {"Teilanlage" : TeilAnlage, "Recipes" : recipes})

def handle_uploaded_recipe(file, filename):
    if not os.path.exists('recipe/'):
        os.mkdir('recipe/')

    with open('recipe/' + filename, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

def uploadStructure(request):
    if request.method == 'POST':
        handle_uploaded_structure(request.FILES['file'], str(request.FILES['file']))

        recipes = []
        for file in os.listdir(RECIPE_DIR):
            recipes.append(file)

        topologies = []
        for file in os.listdir(TOPOLOGY_DIR):
            topologies.append(file)

    return TemplateResponse(request, 'Home.html', {"Teilanlage" : TeilAnlage, "Recipes" : recipes, "Topologies" : topologies})

def showExample(request):

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

def handle_uploaded_structure(file, filename):
    if not os.path.exists('topologie/'):
        os.mkdir('topologie/')

    with open('topologie/' + filename, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

@login_required
def recipeStart(request, recipeName):
    RecipeHandler.instance.startRecipeWithFilename(recipeName)
    return JsonResponse({'status' : 'OK'})

def recipeParse(request, recipeName):
    RecipeHandler.instance.parseRecipe(recipeName)
    return JsonResponse({'status' : 'OK',})





