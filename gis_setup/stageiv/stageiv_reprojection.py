### Grid information:

# Coordinate System is:
# PROJCS["unnamed",
#     GEOGCS["unknown",
#         DATUM["unknown",
#             SPHEROID["Sphere",6371200,0]],
#         PRIMEM["Greenwich",0],
#         UNIT["degree",0.0174532925199433]],
#     PROJECTION["Polar_Stereographic"],
#     PARAMETER["latitude_of_origin",90],
#     PARAMETER["central_meridian",-105],
#     PARAMETER["scale_factor",1],
#     PARAMETER["false_easting",0],
#     PARAMETER["false_northing",0],
#     UNIT["metre",1,
#         AUTHORITY["EPSG","9001"]]]

# Origin = (-173551.282702938828152,-6018125.302421377040446)

# Pixel Size = (5104.432159267162206,-5104.432210884740925)

# Metadata:
#   NC_GLOBAL#cdlDate=20060613
#   NC_GLOBAL#centralLat=90
#   NC_GLOBAL#centralLon=-105
#   NC_GLOBAL#Conventions=CF-1.5
#   NC_GLOBAL#Creation_datetime=2015-09-09 17:28:00
#   NC_GLOBAL#depictorName=TUA_localMPE@19486084
#   NC_GLOBAL#dxKm=4.0701828
#   NC_GLOBAL#dyKm=4.083715
#   NC_GLOBAL#feature_type=GRID
#   NC_GLOBAL#Generating_Model=P3   
#   NC_GLOBAL#history=XMRG to netCDF - ABRFC
#   NC_GLOBAL#lat00=33.603359
#   NC_GLOBAL#latDxDy=36.23304
#   NC_GLOBAL#latNxNy=38.027081
#   NC_GLOBAL#lon00=-106.4556
#   NC_GLOBAL#lonDxDy=-98.944794
#   NC_GLOBAL#lonNxNy=-90.678253
#   NC_GLOBAL#original_file_format=XMRG
#   NC_GLOBAL#Originating_center=US NOAA National Weather Service
#   NC_GLOBAL#Originating_subcenter=ABRFC
#   NC_GLOBAL#Product_Type=Precipitation Accumulation
#   NC_GLOBAL#projIndex=1
#   NC_GLOBAL#projName=STEREOGRAPHIC
#   NC_GLOBAL#rotation=0
#   NC_GLOBAL#title=Quantitative Precipitation Estimate
#   NC_GLOBAL#xMax=0.1205765
#   NC_GLOBAL#xMin=-0.01362002
#   NC_GLOBAL#yMax=-0.47229141
#   NC_GLOBAL#yMin=-0.53598458

#   Polar_Stereographic#_CoordinateAxisTypes=GeoX GeoY
#   Polar_Stereographic#_CoordinateTransformType=Projection
#   Polar_Stereographic#earth_radius=6371200
#   Polar_Stereographic#earth_shape=spherical
#   Polar_Stereographic#grid_mapping_name=polar_stereographic
#   Polar_Stereographic#latitude_of_projection_origin=90
#   Polar_Stereographic#longitude_of_projection_origin=-105
#   Polar_Stereographic#scale_factor_at_projection_origin=1
#   Polar_Stereographic#straight_vertical_longitude_from_pole=-105

#   x#_CoordinateAxisType=GeoX
#   x#grid_spacing=4762.5 m
#   x#long_name=x coordinate of projection
#   x#standard_name=projection_x_coordinate
#   x#units=m

#   y#_CoordinateAxisType=GeoY
#   y#grid_spacing=4762.5 m
#   y#long_name=y coordinate of projection
#   y#standard_name=projection_y_coordinate
#   y#units=m

# Corner Coordinates:
# Upper Left  ( -173551.283,-6018125.302) (106d39' 6.64"W, 39d25'10.86"N)
# Lower Left  ( -173551.283,-6829730.024) (106d27'20.30"W, 33d36'12.07"N)
# Upper Right ( 1536433.491,-6018125.302) ( 90d40'41.72"W, 38d 1'37.50"N)
# Lower Right ( 1536433.491,-6829730.024) ( 92d19'17.97"W, 32d25'58.77"N)
# Center      (  681441.104,-6423927.663) ( 98d56'41.24"W, 36d13'58.94"N)


from pyproj import Proj
import numpy as np

proj_params = {
    'proj': 'stere',
    'lat_ts': 90,
    'lat_0': 90,
    'lon_0': -105,
    'a': 6371200,
    'b': 6371200,
}

dx, dy = (5104.432159267162206, -5104.432210884740925)
x0, y0 = (-173551.282702938828152, -6018125.302421377040446)

p = Proj(**proj_params)

    
def get_stageiv_point(xs, ys):

    if x >= 335 or y >= 159:
        raise Exception('x must be less than 335, y must be less than 159')

    y = 158-y

    xs = x0 + xs*dx
    ys = y0 + ys*dy

    return p(xs, ys, inverse=True)


def get_stageiv_polygon(x, y):

    if x >= 335 or y >= 159:
        raise Exception('x must be less than 335, y must be less than 159')

    y = 158-y
    
    ul = np.array((x0 + x*dx, y0 + y*dy))
    ur = ul + np.array((dx, 0))
    lr = ur + np.array((0, dy))
    ll = ul + np.array((0, dy))

    xs, ys = zip(*(ul, ur, lr, ll))
    lons, lats = p(xs, ys, inverse=True)

    return zip(*(lons, lats))
