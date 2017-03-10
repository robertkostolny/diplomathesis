
import pygrib


grib='gfs_4_20130505_0000_033.grb2';
grbs=pygrib.open(grib)

param =[]
types = []
for point in grbs:
    if point.parameterName == '200' and hasattr(point, 'values') and point.values.any():
        if point.typeOfLevel not in types:
            types.append(point.typeOfLevel)
                   
                 
print types
   
for point in grbs:
    if point.typeOfLevel == 'surface' and hasattr(point, 'values') and point.values.any():
        if point.parameterName not in param:
            param.append(point.parameterName)
                   
             
print param
   