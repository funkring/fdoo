'''
Created on 04.08.2012

@author: martin
'''
import math

def distance(longlat1,longlat2):
    """ Calculate distance from start (longitude,latitude) to end (longitude,latitude) in kilometer 
        longitude and latitude are in decimal degrees
    """        
    slat=  longlat1[1]
    slon=  longlat1[0]
    elat = longlat2[1]
    elon = longlat2[0]
    dlat = math.radians(elat-slat)
    dlon = math.radians(elon-slon)
    slat = math.radians(slat)
    elat = math.radians(elat)    
    a = math.sin(dlat/2)**2 + math.cos(slat)*math.cos(elat)*math.sin(dlon/2)**2
    c= 2*math.asin(math.sqrt(a))
    return 6371*c

def distancem(longlat1,longlat2):
    """ Calculate distance from start (longitude,latitude) to end (longitude,latitude) in meter 
        longitude and latitude are in decimal degrees
    """   
    return distance(longlat1,longlat2)*1000

lat1 = 47.248637
lon1 = 16.050541

lat2 = 47.248368
lon2 = 16.041350

print distancem((lon1,lat1), (lon2,lat2))
