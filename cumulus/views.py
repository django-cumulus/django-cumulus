import cloudfiles
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse

from cumulus.models import Account
from cumulus.forms import CDNForm, CreateContainerForm, UploadForm

def edit_cloudfiles(request, account_id):
    """
    Gets a list of containers for the selected account.
    """
    if request.is_ajax():
        template = 'cumulus/includes/container_list.html'
    else:
        template = 'cumulus/edit_cloudfiles.html'
    account = get_object_or_404(Account, pk=account_id)
    conn = cloudfiles.get_connection(account.username, account.api_key)
    containers = conn.list_containers_info()
    container_count, bytes_used = conn.get_info() 
    return render_to_response(template, {
        'title': "Manage Cloud Files",
        'account': account,
        'containers': containers,
        'container_count': container_count,
        'bytes_used': bytes_used
    }, context_instance=RequestContext(request))


def container_info(request, account_id, container_name):
    """
    Gets the information for the specified container. Also allows user to set
    whether the container is available via the Limelight CDN.
    """
    if request.is_ajax():
        account = get_object_or_404(Account, pk=account_id)
        conn = cloudfiles.get_connection(account.username, account.api_key)
        container = conn.get_container(container_name)
        container_name = container.name
        is_public = container.is_public()
        public_uri = is_public and container.public_uri() or None
        
        if request.method == 'POST':
            f = CDNForm(request.POST)
            if f.is_valid():
                public = f.cleaned_data['public']
                if public:
                    container.make_public()
                    is_public = True
                    public_uri = container.public_uri()
                else:
                    container.make_private()
                    is_public = False
                    public_uri = None
        else:
            f = CDNForm(initial={'public':container.is_public()})
        
        return render_to_response('cumulus/container_info.html', {
            'account': account,
            'container': container,
            'container_name': container_name,
            'is_public': is_public,
            'public_uri': public_uri,
            'form': f
        })
    else:
        return HttpResponse("container_info should be accessed via ajax.")


def create_container(request, account_id):
    """
    Allows a user to create a new container for the specified account. This
    view should only be called via ajax.
    """
    if request.is_ajax():
        account = get_object_or_404(Account, pk=account_id)
        conn = cloudfiles.get_connection(account.username, account.api_key)
        container = None
        if request.method == 'POST':
            f = CreateContainerForm(request.POST)
            if f.is_valid():
                name = f.cleaned_data['name']
                container = conn.create_container(name)
                return HttpResponse("success")
        else:
            f = CreateContainerForm()
        return render_to_response('cumulus/create_container.html', {
            'account': account,
            'container': container,
            'form': f
        })
    else:
        return HttpResponse("create_container should be accessed via ajax.")


def container_objects(request, account_id, container_name):
    """
    Gets a list of objects within a container and their info.
    """
    if request.is_ajax():
        account = get_object_or_404(Account, pk=account_id)
        conn = cloudfiles.get_connection(account.username, account.api_key)
        container = conn.get_container(container_name)
        objects = container.list_objects_info()
        return render_to_response('cumulus/container_objects.html', {
            'account': account,
            'container': container,
            'objects': objects
        })
    else:
        return HttpResponse("container_objects should be accessed via ajax.")


def upload_file(request, account_id, container_name):
    """
    Allows a user to upload a file to the specified container.
    """
    account = get_object_or_404(Account, pk=account_id)
    conn = cloudfiles.get_connection(account.username, account.api_key)
    container = conn.get_container(container_name)
    
    if request.is_ajax():
        f = UploadForm()
        return render_to_response('cumulus/upload_file.html', {
            'account': account,
            'container': container,
            'container_name': container_name,
            'form': f
        })
    else:
        if request.method == 'POST':
            f = UploadForm(request.POST, request.FILES)
            if f.is_valid():
                upload = request.FILES['upload']
                if upload.multiple_chunks():
                    content_str = ''.join(chunk for chunk in upload.chunks())
                else:
                    content_str = upload.read()
                obj = container.create_object(upload.name)
                obj.content_type = upload.content_type
                obj.send(content_str)
                return HttpResponseRedirect(reverse('admin:cumulus-edit-cloudfiles', args=(account.id,)))
