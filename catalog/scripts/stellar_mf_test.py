#!/usr/bin/env python

# DESCQA catalog test: read mock galaxy catalog from an N-body simulation and
# generate the stellar mass function. Plot it and an observational stellar mass function.

import numpy as np
import matplotlib.pyplot as mp
from astropy import units as u
import sys
from GalaxyCatalogInterface import loadCatalog
from descqaGlobalConfig import *
from descqaTestConfig import *

def usage():
    print("usage: stellar_mf_test.py sim-catalog obs-catalog zlo zhi")
    sys.exit(1)

def gen_stellar_mf(fn, zlo, zhi):
    Nbins = 25      # might need to choose this another way
    gc = loadCatalog(fn)
    if gc:
        masses = gc.get_quantities("stellar_mass", {'zlo': zlo, 'zhi': zhi})
        logm = np.log10(masses)
        mhist, mbins = np.histogram(logm, Nbins)
        binctr = (mbins[1:] + mbins[:Nbins])/2.
        binwid = mbins[1:] - mbins[:Nbins]
        Vhi = gc.get_cosmology().comoving_volume(zhi)
        Vlo = gc.get_cosmology().comoving_volume(zlo)
        dV = float((Vhi - Vlo)/u.Mpc**3)
        # TODO: need to consider sky coverage and completeness in volume
        mhmin = (mhist - np.sqrt(mhist)) / binwid / dV
        mhmax = (mhist + np.sqrt(mhist)) / binwid / dV
        print 'binctr = ', binctr
        print 'mhist = ', mhist
        mhist = mhist / binwid / dV
        return binctr, binwid, mhist, mhmin, mhmax
    else:
        print("could not read galaxy catalog from %s" % fn)
        sys.exit(1)

def read_obs_mf(fn):
    binctr, mhist, mhmax, mhmin = np.genfromtxt(fn, unpack=True, usecols=[0,1,2,3])
    return binctr, mhist, mhmin, mhmax

def write_file(fn, binctr, hist, hmin, hmax, comment=""):
    f = open(fn, 'w')
    if comment:
        f.write('# '+comment+'\n')
    for b, h, hn, hx in zip(binctr, hist, hmin, hmax):
        f.write("%13.6e %13.6e %13.6e %13.6e\n" % (b, h, hn, hx))
    f.close()

#------------------------------------------------------------------------------

#if len(sys.argv) != 5:
#    usage()

#sim_catalog = sys.argv[1]
#obs_catalog = sys.argv[2]
#zlo         = sys.argv[3]
#zhi         = sys.argv[4]

sbinctr, sbinwid, shist, shmin, shmax = gen_stellar_mf(sim_catalog, zlo, zhi)
shist = np.log10(shist)
shmin = np.log10(shmin)
shmax = np.log10(shmax)
obinctr, ohist, ohmin, ohmax = read_obs_mf(obs_catalog)

sim_catalog_short = os.path.basename(sim_catalog)
sim_catalog_short = sim_catalog_short[:15] + (sim_catalog_short[15:] and '...')
obs_catalog_short = os.path.basename(obs_catalog)
obs_catalog_short = obs_catalog_short[:15] + (obs_catalog_short[15:] and '...')

mp.step(sbinctr, shist, where="mid", label=sim_catalog_short)
mp.errorbar(obinctr, ohist, yerr=[ohmin, ohmax], label=obs_catalog_short, fmt='o')
mp.legend()
mp.title(r'Stellar mass function, $%4.2f < z < %4.2f$' % (zlo, zhi))
mp.xlabel(r'$\log M_*\ (M_\odot)$')
mp.ylabel(r'$dN/dV\, d\log M\ ({\rm Mpc}^{-3}\,{\rm dex}^{-1})$')
mp.savefig("stellar_mf_test.png")

write_file("theory_output.txt", sbinctr, shist, shmin, shmax)
write_file("plot_output.txt", obinctr, ohist, ohmin, ohmax)
