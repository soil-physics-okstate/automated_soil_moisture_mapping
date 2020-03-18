import numpy as np

def exponV(h, nugget, sill, range):
    return nugget + sill*(1 - np.exp(-3*h/range))

def gaussV(h, nugget, sill, range):
    return nugget + sill*(1 - np.exp(-(np.sqrt(3.)*h/range)**2))

def spherV(h, nugget, sill, range):
    v = nugget + sill*((3./2.)*(h/range) - (1./2.)*(h/range)**3)
    v[h > range] = nugget + sill
    return v
