"""studienordnung URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin, auth
import django.contrib.auth.views
from django.conf.urls.static import static
from django.conf import settings
from . import views
from django.core.urlresolvers import reverse_lazy
urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.home, name="Home View"),
    #url(r'^pdf/module/(?P<moduleId>[\w-]+)/$', views.ShowModulePdf, name="Generate Module Pdf"),
    url(r'^login/$', django.contrib.auth.views.login,  name='studien_login'),
    url(r'^logout/$', django.contrib.auth.views.logout, name='studien_logout'),
    #url(static(settings.STATIC_URL, serve=True)),
    #url(r'^ajax/price/(?P<aktien>[0-9]+)/$', views.ajaxPrice, name="AjaxPreis"),
    # Catchall
    # url("^", views.Overview, name="Overview"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = "django.views.defaults.page_not_found"
handler500 = "django.views.defaults.server_error"