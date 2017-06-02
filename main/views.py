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
import configobj, os
import logging
logger = logging.getLogger('django')

@login_required
def home(request):
    return TemplateResponse(request, 'home.html', {})