# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

# 

from __future__ import unicode_literals

from django.db import models
import os.path

class Container(models.Model):
    name = models.CharField(max_length=300)
    containerpath = models.CharField(max_length=800, db_column='containerPath', blank=True, null=True, verbose_name='Container Path')
    def __unicode__(self):  # Python 3: def __str__(self):
        return self.name
    class Meta:
        db_table = 'container'

class Folder(models.Model):
    inodeid = models.IntegerField(db_column='iNodeID', verbose_name='iNode ID', null=True, blank=True)
    containerid = models.ForeignKey('Container',db_column='containerID', verbose_name='Container ID', db_index=True)
    parentfolderid = models.ForeignKey('Folder', null=True, blank=True, db_column='parentFolderID', verbose_name='Parent Folder', db_index=True)
    items = models.IntegerField(null=True, blank=True)
    dateadded = models.DateTimeField(db_column='dateAdded', verbose_name='Date added')
    dateupdated = models.DateTimeField(db_column='dateUpdated', verbose_name='Date updated')
    path = models.CharField(max_length=800, db_index=True)
    def _get_name(self):
    	return self.containerid.name + " > " + os.path.basename(os.path.dirname(self.path)) + " > " + os.path.basename(self.path)
    name = property(_get_name)
    def __unicode__(self):  # Python 3: def __str__(self):
        return self.name
    class Meta:
        db_table = 'folder'

class Geolocation(models.Model):
    itemid = models.ForeignKey('Item',unique=True, db_column='itemID', db_index=True)
    latitude = models.FloatField(blank=True)
    longitude = models.FloatField(blank=True)
    altitude = models.FloatField(blank=True, null=True)
    def _get_name(self):
    	return "[%g,%g] @ %s" % (self.latitude,self.longitude,self.itemid.name)
    representation = property(_get_name)
    def __unicode__(self):  # Python 3: def __str__(self):
        return self.representation
    class Meta:
        db_table = 'geolocation'

class Item(models.Model):
    inodeid = models.IntegerField(db_column='iNodeID', verbose_name='iNode ID')
    containerid = models.ForeignKey('Container', db_column='containerID', verbose_name='Parent Container')
    folderid = models.ForeignKey('Folder', related_name='+', db_column='folderID', verbose_name='Parent Folder', db_index=True)
    type = models.CharField(max_length=100,blank=True)
    dateadded = models.DateTimeField(db_column='dateAdded', verbose_name='Date added')
    dateupdated = models.DateTimeField(db_column='dateUpdated', verbose_name='Date updated')
    mtime = models.DateTimeField(verbose_name='Last modification',null=True,blank=True)
    name = models.CharField(max_length=300, db_index=True)
    def __unicode__(self):  # Python 3: def __str__(self):
        return "%s/%s" % (self.folderid.path,self.name)
    class Meta:
        db_table = 'item'

class Metadata2Item(models.Model):
    itemid = models.ForeignKey('Item',db_column='itemID')
    weight = models.IntegerField(null=True, blank=True) # a sense of order of this metadata entry
    name = models.CharField(max_length=300, db_index=True)  # The EXIF/IPTC/XMP name of this attribute
    value = models.TextField(null=True, blank=True)
    def __unicode__(self):  # Python 3: def __str__(self):
        return self.name
    class Meta:
        db_table = 'metadata2item'

class PictureRegion(models.Model):
    name = models.CharField(max_length=800, db_index=True)
    type = models.CharField(max_length=30,blank=True, null=True)
    schema = models.CharField(max_length=30,blank=True, null=True)
    index = models.IntegerField()
    itemid = models.ForeignKey('Item',db_column='itemID', verbose_name='Item ID', db_index=True)
    top = models.FloatField(blank=True)
    left = models.FloatField(blank=True)
    width = models.FloatField(blank=True)
    height = models.FloatField(blank=True)
    def _get_name(self):
    	return "%s[%d] @ %s" % (self.name, self.index, self.itemid.name)
    representation = property(_get_name)
    def __unicode__(self):  # Python 3: def __str__(self):
        return self.representation
    class Meta:
        db_table = 'pictureregion'
        unique_together = ('itemid', 'index')

class Properties(models.Model):
    name = models.CharField(max_length=300, null=False)
    value = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    def __unicode__(self):  # Python 3: def __str__(self):
        return self.name
    class Meta:
        db_table = 'properties'

class Scanlog(models.Model):
    date = models.TextField()
    itemsadded = models.IntegerField(db_column='itemsAdded')
    itemsremoved = models.IntegerField(db_column='itemsRemoved')
    itemsupdated = models.IntegerField(db_column='itemsUpdated')
    foldersadded = models.IntegerField(db_column='foldersAdded')
    foldersremoved = models.IntegerField(db_column='foldersRemoved')
    foldersupdated = models.IntegerField(db_column='foldersUpdated')
    class Meta:
        db_table = 'scanlog'

