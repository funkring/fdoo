# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-

#############################################################################
#
#    Copyright (c) 2007 Martin Reisenhofer <martin.reisenhofer@funkring.net>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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
    
    
if __name__ == '__main__':    
    print distancem((16.058303,47.244695),(16.069679,47.122273))    
