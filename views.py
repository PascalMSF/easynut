# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import get_object_or_404, render, render_to_response,redirect
from django.template import loader, RequestContext
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from operator import itemgetter
from django.template.context_processors import request
from DAO import *
from EasyDBObjects import *
from django.utils.encoding import smart_str
from django.http import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator

def loginview(request):
    context = RequestContext(request)
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/emr/')
            else:
                return render(request, 'emr/login.html', {'wrongcrendentials' : 'Your account is disabled.'})
        else:
            return render(request, 'emr/login.html', {'wrongcrendentials' : 'Invalid username / password combination provided'})
    else:
        return render(request, 'emr/login.html', {'wrongcrendentials' : ''})


def logoutbutton(request):
    logout(request)    
    return render(request, 'emr/login.html', {'wrongcrendentials' : ''})
    
@login_required
def index(request):
    template_name = 'emr/index.html'
    daoobject = DAO()
    daoobject.set_tables_config()
    return render(request, template_name, {'edbtables': daoobject.tables_config_lite, 'lastId' : daoobject.getLastId('tabla_1', 'campo_1')})

@login_required
def results(request):
    template_name = 'emr/results.html'
    search_query = request.GET.get('searchstring')
    daoobject = DAO()
    daoobject.set_tables_config()    
    if daoobject.doesIdExist(search_query):
        return patient(request, daoobject.doesIdExist(search_query))    
    else:
        return render(request, template_name, {'searchresults': daoobject.search(search_query, '1'), 'lastId' : daoobject.getLastId('tabla_1', 'campo_1')})

@login_required
def patient(request, record_id):
    template_name = 'emr/patient.html'    
    daoobject = DAO()
    daoobject.set_tables_config()
    daoobject.set_tables_relationships()
    return render(request, template_name, {
        'record': daoobject.get_record_with_type('1', record_id, True), 
        'relatedrecords' : daoobject.get_related_records('1', record_id),
        'lastId' : daoobject.getLastId('tabla_1', 'campo_1')
        })
    
@login_required
def detail(request, table_id, record_id):
    template_name = 'emr/detail.html'
    daoobject = DAO()
    daoobject.set_tables_config()
    daoobject.set_tables_relationships()
    return render(request, template_name, {
        'record': daoobject.get_record_with_type(table_id, record_id, False), 
        'relatedrecords' : daoobject.get_related_records(table_id, record_id),
        'lastId' : daoobject.getLastId('tabla_1', 'campo_1')
        })

@login_required
def edit(request, table_id, record_id):
    template_name = 'emr/edit.html'
    daoobject = DAO()
    daoobject.set_tables_config()    
    return render(request, template_name, {'record': daoobject.get_record_with_type(table_id, record_id, False), 'lastId' : daoobject.getLastId('tabla_1', 'campo_1')})

@login_required
def save(request):
    record_id = request.GET.get('record_id')
    table_id = request.GET.get('table_id')
    daoobject = DAO()
    daoobject.set_tables_config()
    fieldstochange = []
    for tablec in daoobject.tables_config:
        if tablec.id == table_id:
            for fieldc in tablec.fields:
                if fieldc.name == 'MSF ID':
                    patientId = daoobject.getPatientIdFromMsfId(request.GET.get(fieldc.field_id))
                fieldstochange.append([fieldc.field_id, request.GET.get(fieldc.field_id), fieldc.type])
    if record_id != "0":
        daoobject.editrecord(table_id, record_id, fieldstochange)
    else:
        record_id = daoobject.insertrecord(table_id, fieldstochange)
    return patient(request, patientId)

@login_required
def addrecord(request, table_id, related_record_entry, related_record_field):
    template_name = 'emr/addrecord.html'
    daoobject = DAO()
    daoobject.set_tables_config()
    daoobject.set_tables_relationships() 
    if (related_record_entry == '0') and (table_id == '1'):
        related_record_entry = daoobject.getNewId('tabla_1', 'campo_1')
        related_record_field = 'campo_1'
    if table_id != "0":
        return render(request, template_name, {
            'recordform': daoobject.getrecordform(table_id),
            'related_record_entry' : related_record_entry,
            'related_record_field' : related_record_field,
            'lastId' : daoobject.getLastId('tabla_1', 'campo_1')
            })
    return index(request)

@login_required
def deleterecord(request, table_id, record_id):
    daoobject = DAO()
    daoobject.set_tables_config()
    daoobject.delete(table_id, record_id)
    return index(request)

@login_required
def downloadexport(request):
    daoobject = DAO()
    daoobject.set_tables_config()
    zip = daoobject.generateExport()+'.zip'
    if os.path.exists(zip):
        with open(zip, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/zip")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(zip)
            return response
    raise Http404

           
