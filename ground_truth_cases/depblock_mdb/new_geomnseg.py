""" Sets nseg in each section to an odd value
   so that its segments are no longer than 
     d_lambda x the AC length constant
   at frequency freq in that section.

   Be sure to specify your own Ra and cm before calling geom_nseg()

   To understand why this works, 
   and the advantages of using an odd value for nseg,
   see  Hines, M.L. and Carnevale, N.T.
        NEURON: a tool for neuroscientists.
        The Neuroscientist 7:123-135, 2001.
"""
from neuron import h
from math import sqrt
# these are reasonable values for most models
freq = 100.0    # Hz, frequency at which AC length constant will be computed
d_lambda = 0.1

PI = 3.14159

def lambda_f(arg,s):
        if h.n3d(sec=s) < 2:
                return 1e5*sqrt(s.diam/(4*PI*arg*s.Ra*s.cm))
              
# above was too inaccurate with large variation in 3d diameter
# so now we use all 3-d points to get a better approximate lambda
        x1 = h.arc3d(0,sec=s)
        d1 = h.diam3d(0,sec=s)
        lam = 0
        for i in range(1,int(h.n3d(sec=s))):
                x2 = h.arc3d(i,sec=s)
                d2 = h.diam3d(i,sec=s)
                lam += (x2 - x1)/sqrt(d1 + d2)
                x1 = x2
                d1 = d2
        
        #  length of the section in units of lambda
        lam *= sqrt(2.0) * 1e-5*sqrt(4*PI*arg*s.Ra*s.cm)

        return s.L/lam

def geom_nseg(nrnobj):
  #soma area(0.5) # make sure diam reflects 3d points
  for s in nrnobj.all:
	  s.nseg = int((s.L/(d_lambda*lambda_f(freq,s))+0.9)/2.0)*2 + 1
	  #print s, s.nseg
