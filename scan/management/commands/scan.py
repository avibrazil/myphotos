# -*- Mode: Python; py-indent-offset: 4 -*-
# vim: tabstop=4 shiftwidth=4 expandtab

import os.path
from datetime import datetime
import re
from gi.repository import GExiv2

from django.core.management.base import NoArgsCommand, BaseCommand, CommandError
from gallery.models import Container, Folder, Item, PictureRegion, Properties, Geolocation, Metadata2Item

class Command(NoArgsCommand):
#    args = '<containerID poll_id ...>'
    help = 'Scans the containers for changes'
        
    foldersByID=dict()
    foldersByINode=dict()
    foldersByName=dict()
    
    itemsByID=dict()
    itemsByINode=dict()
    itemsByName=dict()
    
    valid_extensions=dict()
    ignore_folders=dict()
    
    # This one will be __init__ialized with compiled patterns from _ignoredTags
    ignoredTags = None

    _ignoredTags = [
       '^Exif\.Canon.*?\.0x.*',
       '^Exif\.Sony.*?\.0x.*',       
       '^Exif\.Nikon.*?\.0x.*',
       '^Exif\.Photo\.MakerNote',
       '^Exif\.Canon.*?\.CameraInfo',
       '^Exif\.Canon.*?\.AFInfo'
    ]
    
    saveTags = []
        
    def findFolder(self,itemInfo,parent,relativePath):
        f = None

        # Compute file/folder name
        if  (relativePath=="." or relativePath==""):
            name=""
        else:
            name=os.path.basename(relativePath)

        # Try to find file through its iNode and then by parentID+name
        if  (itemInfo.st_ino in self.foldersByINode):
            # Found. Now compare other properties of the file
            f=self.foldersByINode[itemInfo.st_ino]
            f.verified=1

            if  (f.path != relativePath):
                f.path = relativePath
                f.changed=1
        elif (isinstance(parent,Folder) and str(parent.id)+name in self.foldersByName):
            # Found. Now compare other properties of the file
            f=self.foldersByName[str(parent.id)+name]
            f.verified=1

            f.inodeid = itemInfo.st_ino
            f.changed=1

            self.foldersByINode[f.inodeid]=f

        return f


    def findItem(self,itemInfo,parent,name):
        i = None

        if  (itemInfo.st_ino in self.itemsByINode):
            # Found. Now compare other properties of the file
            i=self.itemsByINode[itemInfo.st_ino]
            i.verified=1

            if  (i.name != name):
                i.name = name
                i.changed=1

        elif (str(parent.id)+name in self.itemsByName):
            # Found. Now compare other properties of the file
            i=self.itemsByName[str(parent.id)+name]
            i.verified=1

            i.iNodeID = itemInfo.st_ino
            i.changed=1

            self.itemsByINode[i.iNodeID]=i

        return i


    @staticmethod
    def _convert_to_degrees(value):
        # Convert lat/lon from '23/1 32/1 806115/32768' into a float
        parts=value.split(' ')
        d=0
        for c in range(0,3):
            part=parts[c].split('/')
            d+=(float(part[0])/float(part[1]))/float(60**c)
		
        return d




    def handlePictureOtherMetadata(self,f,metadata):
        # Insert on DB all other tags
        
        index=0
        
        dbTags = []
        pictureTags=set(metadata.get_tags())
        pictureTags&=self.valid_tags
        
#        print(pictureTags)
        
        for k in pictureTags:
            if metadata[k]==None or metadata[k]=="":
            	continue
            dbTags.append(Metadata2Item(
                itemid=f,
                weight=index,
                name=k,
                value=metadata[k]
            ))
        
            ++index
            
        Metadata2Item.objects.bulk_create(dbTags)


    @staticmethod
    def handlePictureGeolocation(i,metadata):
    	if (not 'Exif.GPSInfo.GPSLatitude' in metadata):
    		return
    	
    	lat=float(0)
    	lon=float(0)
    	
    	# Algorithm from http://eran.sandler.co.il/2011/05/20/extract-gps-latitude-and-longitude-data-from-exif-using-python-imaging-library-pil/
    	
    	lat = Command._convert_to_degrees(metadata['Exif.GPSInfo.GPSLatitude'])
    	if (metadata['Exif.GPSInfo.GPSLatitudeRef'] != 'N'):
    		lat = 0 - lat


    	lon = Command._convert_to_degrees(metadata['Exif.GPSInfo.GPSLongitude'])
    	if (metadata['Exif.GPSInfo.GPSLongitudeRef'] != 'E'):
    		lon = 0 - lon
    	
    	
		altitude = None
		if ('Exif.GPSInfo.GPSAltitude' in metadata):
			altitude = metadata['Exif.GPSInfo.GPSAltitude']
			altitude = altitude.split('/')
			altitude = float(altitude[0])/float(altitude[1])

		g=Geolocation(
			itemid = i,
			latitude = lat,
			longitude = lon,
			altitude = altitude
		)
		
		g.save()
		
		metadata.clear_tag('Exif.GPSInfo.GPSLatitude')
		metadata.clear_tag('Exif.GPSInfo.GPSLatitudeRef')
		metadata.clear_tag('Exif.GPSInfo.GPSLongitude')
		metadata.clear_tag('Exif.GPSInfo.GPSLongitudeRef')
		metadata.clear_tag('Exif.GPSInfo.GPSAltitude')
		metadata.clear_tag('Exif.GPSInfo.GPSAltitudeRef')



        
    @staticmethod
    def handlePictureRegions(i,metadata):
		regs=i.pictureregion_set.all();
		regs.delete()
		
		# Handle Regions under MWG-RS domain (http://www.exiv2.org/tags-xmp-mwg-rs.html)
		index=1
		while True:
			if (not 'Xmp.mwg-rs.Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:x' % (index) in metadata):
				break
			r=PictureRegion(
				itemid = i,
				index  = index,
				schema = 'XMP-MWG-RS',
				type   = metadata['Xmp.mwg-rs.Regions/mwg-rs:RegionList[%d]/mwg-rs:Type' % (index)],
				name   = metadata['Xmp.mwg-rs.Regions/mwg-rs:RegionList[%d]/mwg-rs:Name' % (index)],
				top    = float(metadata['Xmp.mwg-rs.Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:y' % (index)]),
				left   = float(metadata['Xmp.mwg-rs.Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:x' % (index)]),
				width  = float(metadata['Xmp.mwg-rs.Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:w' % (index)]),
				height = float(metadata['Xmp.mwg-rs.Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:h' % (index)])
			)
			r.save()
			
			metadata.clear_tag('Xmp.mwg-rs.Regions/mwg-rs:RegionList[%d]/mwg-rs:Type' % (index))
			metadata.clear_tag('Xmp.mwg-rs.Regions/mwg-rs:RegionList[%d]/mwg-rs:Name' % (index))
			metadata.clear_tag('Xmp.mwg-rs.Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:y' % (index))
			metadata.clear_tag('Xmp.mwg-rs.Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:x' % (index))
			metadata.clear_tag('Xmp.mwg-rs.Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:w' % (index))
			metadata.clear_tag('Xmp.mwg-rs.Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:h' % (index))
			
			index+=1



		# Handle Regions under MP (Microsoft) domain (http://www.exiv2.org/tags-xmp-MP.html)			
		index=1
		while True:
			if (not 'Xmp.MP.RegionInfo/MPRI:Regions[%d]/MPReg:Rectangle' % (index) in metadata):
				break
			rectangle=metadata['Xmp.MP.RegionInfo/MPRI:Regions[%d]/MPReg:Rectangle' % (index)]
			rectangle=rectangle.split(',')
			r=PictureRegion(
				itemid = i,
				index  = index,
				schema = 'XMP-MP',
				type   = 'Face',
				name   = metadata['Xmp.MP.RegionInfo/MPRI:Regions[%d]/MPReg:PersonDisplayName' % (index)],
				top    = float(rectangle[0]),
				left   = float(rectangle[1]),
				width  = float(rectangle[2]),
				height = float(rectangle[3])
			)
			r.save()
			
			metadata.clear_tag('Xmp.MP.RegionInfo/MPRI:Regions[%d]/MPReg:Rectangle' % (index))
			metadata.clear_tag('Xmp.MP.RegionInfo/MPRI:Regions[%d]/MPReg:PersonDisplayName' % (index))
			
			index+=1
			

    def __init__(self, *args, **kwargs):
		super(Command, self).__init__(*args, **kwargs)
        
		self.valid_extensions=Properties.objects.get(name="scan.valid_extensions").value
		self.valid_extensions.split(',')
		
		self.ignore_folders=Properties.objects.get(name="scan.ignore_folders").value
		self.ignore_folders.split(',')
		
		self.ignoredTags=[re.compile(pat) for pat in self._ignoredTags]

		self.valid_tags=Properties.objects.get(name="scan.valid_tags").value
		self.valid_tags=frozenset(self.valid_tags.split('\n'))
		
		

    def handle_noargs(self, **options):
		for container in Container.objects.all():
			self.stdout.write('Container "%s"' % container)

			# Load in memory all Container's objects from database
			for folder in Folder.objects.filter(containerid=container):
				# Now include the pulled Folder in 3 lists
				self.foldersByID[folder.id]                        = folder
				self.foldersByINode[folder.inodeid]                = folder
				self.foldersByName[str(folder.parentfolderid) + folder.name] = folder

			for item in Item.objects.filter(containerid=container):
				# Now include the pulled Item in 3 lists
				self.itemsByID[item.id]                        = item
				self.itemsByINode[item.inodeid]                = item
				self.itemsByName[str(item.folderid) + item.name] = item

			# Walk the filesystem and create a record in memory for each file found
			for r, dirs, files in os.walk(container.containerpath):
				if os.path.basename(r) in self.ignore_folders:
					continue

				print("Walk iteration")

				current=None

				# Compute complete path relative to container's path
				relativePath=os.path.relpath(r,container.containerpath)
				relativePath=os.path.normpath(relativePath)

				statStruct=os.stat(r)

				if  (relativePath=="." or relativePath==""):
					relativePath=""

				current=self.findFolder(statStruct,None,relativePath)					

				if  (current == None):
					# Create entry on DB if it couldn't be found already
					current=Folder(inodeid=statStruct.st_ino,
						containerid=container,
						parentfolderid=None,
						path=relativePath,
						dateadded=datetime.now(),
						dateupdated=datetime.now())
					current.save()
					print "Created ", current.id

					self.foldersByID[current.id]                     = current
					self.foldersByINode[current.inodeid]             = current
					self.foldersByName[str(0) + current.name]        = current
				else:
					print "Found parent", current.id
###					if (current.changed):
###						current.save();
				
				for d in dirs:
					if d in self.ignore_folders:
						continue

					# Compute complete path relative to container's path
					rPath=os.path.join(r,d)

					statStruct=os.stat(rPath)

					# Compute complete path relative to container's path
					rPath=os.path.relpath(rPath,container.containerpath)
					rPath=os.path.normpath(rPath)

					f=self.findFolder(statStruct,current,rPath)

					if  (f == None):
						# Create entry on DB
						f=Folder(inodeid=statStruct.st_ino,
							containerid=container,
							parentfolderid=current,
							path=rPath,
							dateadded=datetime.now(),
							dateupdated=datetime.now())
						f.save()
						print "Created folder ", f.id

						# Insert it in our indexes
						self.foldersByID[f.id]                       = f
						self.foldersByINode[f.inodeid]               = f
						self.foldersByName[str(current.id) + f.name] = f
					else:
						print "Found folder ", f.id
###						if (f.changed):
###							f.save();
				
				f = None
				
				for i in files:
				
					if i.split(".")[-1].strip().lower() not in self.valid_extensions:
						continue
				
					# Compute complete path relative to container's path
					rPath=os.path.join(r,i)
					statStruct=os.stat(rPath)

					# Compute complete path relative to container's path
					rPath=os.path.relpath(rPath,container.containerpath)
					rPath=os.path.normpath(rPath)

					f=self.findItem(statStruct,current,rPath)

					if  (f == None):
						# Create entry on DB
						f=Item(inodeid=statStruct.st_ino,
							containerid=container,
							folderid=current,
							name=i,
							dateadded=datetime.now(),
							dateupdated=datetime.now())
						f.save()
						print "Created item %s[%d]" % (f.name, f.id)

						# Insert it in our indexes
						self.itemsByID[f.id]                       = f
						self.itemsByINode[f.inodeid]               = f
						self.itemsByName[str(current.id) + f.name] = f
						
						# Now handle picture metadata
						try:
							metadata = GExiv2.Metadata(os.path.join(r,i))
							Command.handlePictureRegions(f,metadata)
							Command.handlePictureGeolocation(f,metadata)
							self.handlePictureOtherMetadata(f,metadata)
						except:
							pass
					else:
						print "Found item ", f.id
###						if (f.changed):
###							f.save();
