from django.shortcuts import render_to_response
from django.http import Http404
from gallery.models import Folder, Item, Container

def renderFolder(request, folderID, uri=None):
	# Tries to find the folder by its ID, if not found, try to resolv the URI.

	folder=Folder.objects.filter(id=folderID)
	
	if (folder == None):
		raise Http404
	
	fchildren=Folder.objects.filter(parentfolderid=folderID)
	ichildren=Item.objects.filter(folderid=folderID)

	return render_to_response('gallery/folder.html', {'fchildren': fchildren, 'ichildren': ichildren})