from django.contrib import admin
from gallery.models import Container, Folder, Item, Properties, Geolocation, PictureRegion, Metadata2Item

class PictureRegionAdmin(admin.ModelAdmin):
	list_display = ('name','index','itemid')
	list_filter  = ['name', 'itemid']

class GeolocationAdmin(admin.ModelAdmin):
	list_display = ('latitude','longitude','itemid')

class Metadata2ItemAdmin(admin.ModelAdmin):
	list_display = ('name','value','itemid')
	list_filter  = ['name', 'itemid']


admin.site.register(Container)
admin.site.register(Folder)
admin.site.register(Item)
admin.site.register(Metadata2Item,Metadata2ItemAdmin)

admin.site.register(PictureRegion, PictureRegionAdmin)
admin.site.register(Geolocation, GeolocationAdmin)

admin.site.register(Properties)