from neuron import h
import numpy as np

from new_geomnseg import *

def range_func(sect,typ,bounds):
	for seg in sect:
		exec "seg." + typ +"= np.interp(seg.x,[0,1],bounds)"

def init(neuron_obj, p):
  test = neuron_obj
  distalance = p['dst']
  cattog = p['gcat']
  hcntog = p['ghcn']
  taukv4 = p['taukv4']
  shift = -p['na_shift']
  hshift = -p['na_hshift']
  sshift = p['na_sshift']
  SCALE = p['scale']
  h.distance(0,test.soma(0.5)) # set 0 of distance to soma # may be redundant
  tcap = 0  
  for s in test.all:
	 #s.nseg = s.nseg*2+1
	 s.Ra = 100.0*p['ra']
	 s.cm = 1.0*p['cm']
	 s.insert('hhb') # for Kv4, Kdr
	 #s.insert('pump')
	 s.insert('leak')
	 #s.insert('nabalan')
	 #s.insert('Na12')
	 s.insert('NaMark')
	 #s.insert('Na16')
	 s.insert('cabalstore')
	 #s.insert('cicr') # requires cabalstore

	 s.insert('typem') # a module that creates a range variable that specifies compartment type by color
	 s.gnabar_NaMark = 1000e-6*p['gnahh']
	 if p['ratio'] < 1:
		s.insert('FastNaMark')
		s.gnabar_FastNaMark = 1000e-6*(1-p['ratio'])*p['gnahh']
		s.shift_FastNaMark = shift
		s.hshift_FastNaMark = hshift
		s.gnabar_NaMark = 1000e-6*p['ratio']*p['gnahh']

	 #s.DCa_cabalthin = 0.0
	 #s.shellfrac_cabalthin = min(0.1/s.diam,1.0) 
	 s.shift_hhb = shift
	 s.sshift_hhb = sshift 
	 s.hshift_hhb = hshift
	 s.ashift_hhb = 0
	 s.asshift_hhb = 0
	 s.gkabar_hhb = 300e-6*p['gka']
	 #s.scale_Na12 = 0.2
	 s.nspeed_hhb = p['nspeed']

	 s.scale_NaMark = SCALE
	 #s.shift_Na12 = -15.0
	 s.shift_NaMark = shift
	 s.hshift_NaMark = hshift

	 for seg in s:
	    tcap+=s.cm*h.area(seg.x,sec=s)
	 #s.ipumpmax_pump*=0.0

	 s.gkhhbar_hhb = 500e-6*p['gkhh']
	 s.gnabar_hhb = 0
	 #s.gnabar_Na12 = 1000e-6*p[5]

	 #s.scale_Na16 =0.2
	 #s.gnabar_Na16 = 1000e-6*p[5]
	 s.gkbar_leak=1.0e-6*p['glk']
	 s.gnabar_leak=1.0e-6*p['glna']
	 s.vhblock_hhb = 0
  
  s.nseg = 1
  #geom_nseg(test) # sets nseg based on geometry 
  """for s in test.all:
	  for seg in s:
		h.setpointer(seg._ref_ju_cicr,'ju_p', seg.cabalstore)
		h.setpointer(seg._ref_jcicr_cicr,'jcicr_p', seg.cabalstore)
		h.setpointer(seg._ref_cac_cabalstore,'cac_p', seg.cicr)
		h.setpointer(seg._ref_cast_cabalstore,'cas_p', seg.cicr)"""

  for s in test.somatic:
	s.insert('hcn')
	#s.insert('katp')
	#s.insert('skpool')
	s.insert('kca')
	#s.insert('catchan')
	s.insert('canchan')
	s.insert('calhh')
	  
	
	s.marker_typem = 0
	#s.gnabar_Na16 *= 1.0
	#s.gnabar_Na12 *= 0.5
	
	#s.prad_bkpool = 0.001
	#s.prad_skpool = 0.1
	
	#s.prad_cabalthin = s.prad_skpool
	s.TotalBuffer_cabalstore = 0.03
	
	#s.gkbar_bk = 0e-3
	s.gkbar_kca = 100e-6*p['gkca']
	s.tausk_kca = 5.0
	s.icapumpmax_cabalstore *= p['capump']
	
	s.gcanbar_canchan = 50e-6
	s.gcalbar_calhh =10.0e-6*p['gcal'] # 
	s.skcoup_calhh = 1.0 # coupling of L-type to SK pool
	s.mhalf_calhh = -30 # half activation
	
	s.gnabar_hhb *= 1.0
	s.gkbar_leak *=1.0
	s.gkhhbar_hhb *=1.0
	s.ghcnbar_hcn = 50.0e-6*hcntog
	s.taukv4_hhb = taukv4
	s.deptog_hhb = 1
	#s.gcatbar_catchan*=0
	s.gkabar_hhb *=2.0
	
	#s.gkbar_katp = 0
	#s.n_katp = 1.3
	
	#s.ghcnbar_hcn = hcntog*50e-6
	#s.tau1_hcn *=0.5
	#s.tau2_hcn *=0.5


def to_shreds_you_say(neuron_obj,chop_dist):  # removes sections whose midpoints are greater than chop distance, name is futurama reference.
	blest = neuron_obj
	h.distance(0,blest.soma(0.5))
	for s in blest.all:
		sref = h.SectionRef(sec = s)
		dist = h.distance(0.5, sec=s)
		if dist > chop_dist:
			h.disconnect(sref)
			h.delete_section(sref)
