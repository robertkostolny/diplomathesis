#-------------------------------------------------------------------------------
# Name:        supportive functions for slants computations
# Purpose:     give support for main.py
#
# Author:      Michal Kacmarik, Institute of Geoinformatics, VSB-TUO
#
# Created:     2015, February
# Copyright:   (c) Michal Kacmarik 2015
# Licence:     GNU
#-------------------------------------------------------------------------------

import math
import os
import re
from datetime import date
import sys

#-------------------------------------------------------------------------------
#prepocet casu v sekundach do podoby hhmm, pouziva se pri praci se ZTD ve formatu TRO
def seconds_to_hours_minutes(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    cas= "%02d%02d" % (h, m)
    return cas

#-------------------------------------------------------------------------------
#prevod XYZ do geografickych souradnic, pokud se vezmou souradnice z TRO, presnost
#zpetne trasnformace do XYZ je dle testovani do 1 mm ve vsech slozkach souradnic
#postup prevzat z Hoffman-Wellenhof, provadi se dve iterace
def XYZ_to_LatLonH(X,Y,Z):
    X=float(X)
    Y=float(Y)
    Z=float(Z)

    a=6378137.0
    b=6356752.3142
    e_2=((a*a)-(b*b))/(a*a)
    e=math.sqrt(e_2)

    lon = math.atan(Y/X)
    lon_degrees = math.degrees(lon)
    p = math.sqrt(X*X+Y*Y)

    lat0=math.atan((Z/p)*(1/(1-e_2)))
    cos2lat0 = (1+math.cos(2*lat0))/2
    sin2lat0 = (1-math.cos(2*lat0))/2
    N0 = (a*a)/math.sqrt(a*a*cos2lat0 + b*b*sin2lat0)
    h0=(p/math.cos(lat0))-N0
    lat1=math.atan((Z/p)*(1/(1-(e_2)*(N0/(N0+h0)))))

    cos2lat1 = (1+math.cos(2*lat1))/2
    sin2lat1 = (1-math.cos(2*lat1))/2
    N1 = (a*a)/math.sqrt(a*a*cos2lat1 + b*b*sin2lat1)
    h1=(p/math.cos(lat1))-N1
    lat2=math.atan((Z/p)*(1/(1-(e_2)*(N1/(N1+h1)))))
    lat2_degrees = math.degrees(lat2)

    cos2lat2 = (1+math.cos(2*lat2))/2
    sin2lat2 = (1-math.cos(2*lat2))/2
    N2 = (a*a)/math.sqrt(a*a*cos2lat2 + b*b*sin2lat2)
    h2=(p/math.cos(lat2))-N2
    lat3=math.atan((Z/p)*(1/(1-(e_2)*(N2/(N2+h2)))))
    lat3_degrees = math.degrees(lat3)

    return lat3_degrees, lon_degrees, h2

#-------------------------------------------------------------------------------
#konverze geografickych souradnic v DDMMSS do DD.DDD
def dd_mm_ss_to_ddd(myList):
  D,M,S = myList.split(' ')
  DD = ((60/float(S)) + 60/float(M)) + float(D)
  return DD

#-------------------------------------------------------------------------------
#prevod geografickych souradnic do XYZ
def latlon_to_XYZ(latitude,longtitude,elevation):
    lat_rad = math.radians(latitude)
    lon_rad = math.radians(longtitude)
    a=6378137.0
##    b=6356752.3142 #wgs84
    b=6356752.314140 #etrs

    Njmenovatel1 = (a*a)*((1+math.cos(2*lat_rad))/2)
    Njmenovatel2 = (b*b)*((1-math.cos(2*lat_rad))/2)
    N=a*a/math.sqrt(Njmenovatel1+Njmenovatel2)

    X=(N+elevation)*math.cos(lat_rad)*math.cos(lon_rad)
    Y=(N+elevation)*math.cos(lat_rad)*math.sin(lon_rad)

    Z1 = (((b*b)/(a*a))*N) + elevation
    Z=Z1*(math.sin(lat_rad))
    return [X,Y,Z]

#-------------------------------------------------------------------------------
def computeIWV(Lat,H_GNSS,H_delta,Pres,Temp,ZTD):
  H_GNSS = float(H_GNSS)
  H_delta = float(H_delta)
  Temp = float(Temp)
  Pres = float(Pres)
  ZTD = float(ZTD)
##  print Lat,H_GNSS,H_delta,Pres,Temp,ZTD

  # Lattitude from DD.DDDDDDD to RADIANS
  LatRad = math.radians(Lat)


  # Heigth from m to km
  H = H_GNSS / 1000.0

  #Pressure at Meteo Station recalibrated to GNSS station altitutde - Berg model
  Pres_GNSS = Pres * (math.pow((1-(0.0000226*(H_delta*-1))),5.225))

  # Temperature stupne to 273.15K
  Temp += 0
  #Temperature at Meteo Station recalibrated to GNSS station altitude
  Temp_GNSS = Temp-0.0065*(H_delta*-1)

  ZHD = (0.0022768 * Pres_GNSS) /((1-0.00266 * (math.cos(2*LatRad)))-0.00028*H)
  ZWD = ZTD - ZHD

  #k - verze pouzivana vsemi skupinami v GNSS4SWEC WG3 (vztah z Askne and Nordius, 1987,
  #konstanty z Bevis et al. 1994)
  c2apo = (70.4 - 77.6)*0.621977
  k = math.pow(10,6) / ((373900/((70.2 + 0.72 * Temp_GNSS)+c2apo))*461.5)

  #k - moje verze pouzivana na DP, disertaci, rozdily ve vysledcich - nepouzivat
##  k = math.pow(10,6) / ((8.31434 / (18.0152 * math.pow(10,-3))) * ((3.776 * math.pow(10,5)) / (70.2 + 0.72 * Temp) + 17 - ((18.0152 * math.pow(10,-3)) / (28.9644 / 1000.0)) * 77.695))

  IWV = ZWD * k / 999.9720 * 100000
  return ZTD,round(Pres_GNSS,5),round(ZHD,5),round(ZWD,5),round(IWV,4)

