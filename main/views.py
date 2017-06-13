# -*- coding: utf-8 -*-
#   Erstellt von Roy Ledermüller mit PyCharm Community Edition 
#   Erstelldatum:   03.05.2017
#   Projektname:    FSR_Studienordnung
#   Getestet mit Python 3.5

from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from django.http import JsonResponse, HttpResponse
from .forms import *
from .models import *
from .settings import *
import os
import logging
logger = logging.getLogger('django')

print("views")

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
    return TemplateResponse(request, 'home.html', {"Teilanlage" : TeilAnlage})