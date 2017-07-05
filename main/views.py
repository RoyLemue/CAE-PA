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
import os
import logging
logger = logging.getLogger('django')

print("views")

RECIPE_DIR = os.path.join('recipe')#os.path.join(STATIC_ROOT, *['media', 'recipes'])

@login_required
def jsonMethodCall(request):
    module = request.post.get("modul")
    service = request.post.get("service")
    method = request.post.get("method")
    TeilAnlage
    return JsonResponse({'status' : 'OK'})

@login_required
def recipeStart(request, recipeName):
    module = request.post.get("modul")
    service = request.post.get("service")
    method = request.post.get("method")
    TeilAnlage
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
    return JsonResponse({'status' : 'OK'})

@login_required
def getState(request, moduleName, serviceName):
    service = TeilAnlage[moduleName].getService(serviceName)
    stringMethods = []
    for m in service.Methods:
        stringMethods.append(str(m).split('.')[1])
    return JsonResponse({'status' : 'OK', 'state' : str(service.State).split('.')[1], 'methods' : stringMethods})

@login_required
def methodCall(request, moduleName, serviceName, methodName):
    methodName = methodName.lower()
    if methodName in ['start', 'stop', 'pause', 'resume', 'reset']:
        service = TeilAnlage[moduleName].getService(serviceName)
        service.commands.call_method("1:"+methodName)
        state = service.State
        return JsonResponse({'status' : 'OK', 'state' : str(state).split('.')[1]})
    return JsonResponse({'status' : 'ERROR'})

@login_required
def home(request):
    if request.method == 'POST':
        selectedModule = ''
        if request.POST.get('module') == 'Mixer':
            selectedModule = TeilAnlage["Mixer"]
        else:
            selectedModule = TeilAnlage['Reactor']

        selectedService = ''
        for Service in selectedModule.ServiceList:
            if Service.name == request.POST['service']:
                selectedService = Service
                break
        if 'START' == request.POST.get('method'):
            selectedService._start()
        elif 'STOP' == request.POST.get('method'):
            selectedService._stop()
        elif 'RESET' == request.POST.get('method'):
            selectedService._reset()
        elif 'ABORT' == request.POST.get('method'):
            selectedService._abort()

    recipes = []
    for file in os.listdir(RECIPE_DIR):
        recipes.append(file)
    return TemplateResponse(request, 'Home.html', {"Teilanlage" : TeilAnlage, "Recipes" : recipes})

def uploadRecipes(request):
    if request.method == 'POST':
        handle_uploaded_recipe(request.FILES['file'], str(request.FILES['file']))

        recipes = []
        for file in os.listdir(RECIPE_DIR):
            recipes.append(file)
    return TemplateResponse(request, 'Home.html', {"Teilanlage" : TeilAnlage, "Recipes" : recipes})

    return HttpResponse("Failed")

def handle_uploaded_recipe(file, filename):
    if not os.path.exists('recipe/'):
        os.mkdir('recipe/')

    with open('recipe/' + filename, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
