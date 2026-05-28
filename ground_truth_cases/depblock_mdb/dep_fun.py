from mpi4py import MPI
from neuron import h, gui, run
from math import ceil

import sys
import numpy as np
import pylab as pl
import os
affix = sys.argv[5]

v_init = -60
RUN = 0
PRINT = 1
IofV = 0
FGI = 0
RANDOM=0
PULSE = 0
STEADY = 0
SYNAPTIC = 0
SYNSTEPS = 0
DINGRUN = 0
DOCUMENT = 1
STEP2=0
STEPLEN=1000
OFFSET = 500
HOLD=0
VSTEP=0
JAC = 0
ARRAY = 0
NTHREADS=64 # lower this if not run on a cluster
FAST=0
GRAPH =0
USEOLD=0
VHOLD=-60

BIFURCATION =0
VERBOSE=0

READVALS = 1
ALIGN=0
ALIAT=5000


from paramsdict import p_init as pstable

  

EXTERN = 'iamp_other_parms.py'
affix2=''
for things in sys.argv:
	if len(things.split('='))>1:
		blah = things.split('=')[0]
		try:
			val = float(things.split('=')[1])
		except:
			val=0
		if blah in pstable:
			if blah == 'both':
				pstable['gnahh']=pstable['gnahh']*val
				pstable['gkhh']=pstable['gkhh']*val
			else:
				#print 'pstable[\'%s\'] = %s' % (things.split('=')[0], things.split('=')[1])
				exec('pstable[\'%s\'] = %s' % (things.split('=')[0], things.split('=')[1]))
			affix2+='_'
			affix2+=things.split('=')[0]
			affix2+=things.split('=')[1]
			continue
		else:
			try: 
				exec(things)
			except:
				exec('%s =\'%s\'' % (things.split('=')[0],things.split('=')[1]))
			if things.split('=')[0] in ['VSTEP','STEP2','STEPLEN','OFFSET','SYNAPTIC']:
				temp = things.split('=')
				affix2+='_%s%s' % (temp[0],temp[1])



if DOCUMENT:
	path = os.getcwd() + '/' + affix+ '/'
	try:
		os.mkdir(path)
	except:
		pass
	os.system('cp blockhh3.mod %s.' %path)
	os.system('cp NaMarkov.mod %s.' %path)
	os.system('cp paramsdict.py %s.' %path)
	
	
	

h.load_file("nrngui.hoc")
h.load_file("template_simple.hoc")

from init_cell_depblock import init, to_shreds_you_say


class dopa:
	def __init__(self,i, args, parms):
		h.pop_section()
		self.p1 = args[0]
		self.p2 = args[1]
		self.internal = parms
		self.nrn = (h.SIMPLE()) 
		self.dt = 0.05 # 20khz
		init(self.nrn,self.internal) # from initcell - using dict parameters
		
		if len(args)>3:
			if args[2] in parms:
				exec('self.internal[\'%s\'] = %s' % (args[2], args[3]))
			if args[2] == 'gnmda':
				for s in self.nrn.all:
					s.insert('nmda')
					s.gnmdabar_nmda = self.internal['gnmda']
					s.cMg_nmda = self.internal['cmg']
					s.cafrac_nmda = parms['cafrac']
		self.srec = h.Vector()# spike times

		self.ntc = h.NetCon(self.nrn.soma(0.5)._ref_v,None,sec=self.nrn.soma)
		self.ntc.threshold = -20
		self.ntc.record(self.srec)

		for s in self.nrn.somatic:
			s.L = parms['size']
			s.dist_NaMark = parms['slow']
			s.v = -50 # -40 starts in db
			s.cai = 1e-9
			s.hshift_NaMark = self.internal['na_hshift']
			s.nslope_hhb = self.internal['nslope']
			s.nshift_hhb = self.internal['nshift']
			if h.ismembrane('kca',sec=s):
				s.tausk_kca = 5
				s.km_kca *=1.0
				
			if h.ismembrane('calhh', sec=s):
				s.gcalbar_calhh *=1
				s.mhalf_calhh = -30
				s.mslope_calhh = 5.0
				s.pf_calhh = 0.6
				
				
			if h.ismembrane('canchan'):
				s.gcanbar_canchan = 50e-6

			if h.ismembrane("hcn",sec=s):
				s.scale_hcn =3.0
				s.mhalf_hcn = -75.0
				
			if h.ismembrane('cabalstore',sec=s): # convert to instant buffering
				#s.MitoBuffer_cabalthin = 0.03
				for seg in s:
					seg.TotalBuffer_cabalstore = 0.03
					seg.SCALE_cabalstore = 1.0
					seg.shellfrac_cabalstore = min(0.1/seg.diam,1.0)
					seg.tog_cabalstore = 1
					seg.DCa_cabalstore = self.internal['dca'] # calcium diffusion constant (radial)
					
				
			if h.ismembrane('nmda'):
				s.cafrac_nmda = parms['cafrac']
				s.cMg_nmda = parms['cmg']
		
		
		self.areas = []
		for s in self.nrn.all:
			#s.ashift_hhb = -10.0
			if s.nseg > 1:
				locarea = 0
				for seg in s:
					locarea += h.area(seg.x,sec=s)
			else:
				locarea = h.area(0.5,sec=s)
			self.areas.append(locarea)

	def __del__(self):
		if VERBOSE:
			print 'killing', self.__class__.__name__
		else:
			pass
		



def run_func(STEPLEN): # long term this should use vectors and cv.solve()
	cell = dopa(0,[1,2],pstable)
	
	if not PRINT:
		return cell # use PRINT=0 if you want to fiddle with model in gui
		# cell needs to be returned to exist outside of function
	
	blah = h.IClamp(cell.nrn.soma(0.5))
	blah2 = h.IClamp(cell.nrn.soma(0.5))
	blah2.delay = 2*pstable['idel'] + 3*pstable['idur']#-4000
	blah2.amp = pstable['iamp']#- pstable['basal']
	blah2.dur = STEPLEN#pstable['idur']
	blah.delay = pstable['idel']
	blah.amp = pstable['iamp']#0e-3 # max at 3e-3
	blah.dur = pstable['idur']

	if STEADY or SYNAPTIC:
		dtime = pstable['idel']+STEPLEN-OFFSET
	else:
		dtime = 16000+STEPLEN-OFFSET

	if VSTEP:
		blah3 = h.SEClamp(cell.nrn.soma(0.5))
		blah3.amp1 = STEP2
		blah3.rs = 1e9 # turn off clamp
		blah3.dur1 = 1e9

	else:
		blah3 = h.IClamp(cell.nrn.soma(0.5))
		blah3.delay = dtime
		blah3.amp = 1e-3*STEP2
		blah3.dur = 200
	
	
	ampmax = pstable['iamp']
	ramp = []
	basal = pstable['basal']
	nc = h.NetCon(cell.nrn.soma(0.5)._ref_v,None,sec=cell.nrn.soma)
	nc.threshold = -10
	freqvec = h.Vector()
	nc.record(freqvec)
	times = np.arange(0,blah.dur+blah.delay,1)
	tvec = h.Vector(times)
	
	for i in range(pstable['idel']):
		ramp.append(basal)
	
	for i in range(int(blah.dur)):
		if i < (blah.dur)/2.0:
			ramp.append(basal+2.0*ampmax*(i)/float(blah.dur)) # @ i = blah.dur/2 this is basal + ampmax = 75
			#if i%100 == 0:
			#	print i, basal+2*ampmax*(i)/float(blah.dur)
		else:
			ramp.append(basal+2.0*ampmax*(blah.dur-i)/float(blah.dur))
	for i in range(pstable['idel']):
		ramp.append(basal)

	blah.dur = blah.dur+2*blah.delay
	blah.delay = 2000*STEADY
	if not STEADY:
		ampvec= h.Vector(ramp)
		ampvec.play(blah._ref_amp, 1)	
	else:
		blah.amp = 0
		blah2.delay = pstable['idel']
	
	
	if SYNAPTIC:
		#delete all the synaptic stuff
		blah = None
		blah2 = None
		#blah3 = None  # keep this one
		gnmdamax = pstable['gnmda']
		step = []
		for i in range(pstable['idel']):#+pstable['idur']):
			step.append(0)
		
		for i in range(STEPLEN):#pstable['idur']):
			step.append(gnmdamax)
			
		for i in range(pstable['idel']):
			step.append(0)
		
		ampvec = h.Vector(step)
		#add an NMDA channel to cell
		for s in cell.nrn.all:
			s.insert('nmda')
			s.cafrac_nmda = pstable['cafrac']
			s.cMg_nmda = pstable['cmg']
			#s.tog_nmda = 0 # set in variable conductance mode
			ampvec.play(s(0.5)._ref_gnmdabar_nmda,1)
			
			
		# create a square pulse waveform
		
		# scale waveform by NMDA conductance
		
	######### start run
	h.t = 0
	cv = h.CVode()
	cv.active(True)
	if JAC:
		cv.jacobian(1)
	#fp = open('pacing_%s.dat' %affix,'w')
	loc = cell.nrn.soma
	#while h.t < max(pstable['idel']-1600,500):
	#	h.fadvance()
	#while h.t < max(pstable['idel']-500,500):
	#	h.fadvance()
	#	fp.write('%e  %e  0  %e  %e  %e  %e  %e\n' %(h.t, loc.v, loc.o1_NaMark, loc.c1_NaMark, loc.c2_NaMark, loc.i1_NaMark,loc.i2_NaMark))
	#fp.close()
	h.finitialize()
	if not STEADY:
		if not SYNAPTIC:
			fp = open('ramp_%s_%f.dat' % (affix+affix2,pstable['iamp']),'w')
			while h.t < pstable['idel']-1000:
				h.fadvance()
		else:
			fp = open('nmda_%s_%.1f.dat' % (affix+affix2,1e6*pstable['gnmda']),'w')
			if HOLD:
				vc = h.SEClamp(cell.nrn.soma(0.5))
				vc.dur1 = pstable['idel']
				vc.dur2 = 0
				vc.dur3 = 0
				vc.amp1 = VHOLD
			h.finitialize()
	else:
		fp = open('steady_%s%s.dat' % (affix,affix2),'w')
		if HOLD:
			vc = h.SEClamp(cell.nrn.soma(0.5))
			vc.dur1 = pstable['idel']
			vc.dur2 = 0
			vc.dur3 = 0
			vc.amp1 = VHOLD
		h.finitialize()
		
	if VSTEP:
		def vfunc(val):
			blah3.rs = val
			return
		#cv.event(dtime,vfunc(1e-4),blah3,None)
		#cv.event(dtime+200,vfunc(1e9),blah3,None)
	vold = loc.v
	told = float(h.t)-0.02
	dvdtold = 0
	offset = 0
	FaA = 0

	while h.t < 3*pstable['idel']+3*pstable['idur']+STEPLEN:
		h.fadvance()
		if h.t > 2*pstable['idel']+STEPLEN and (SYNAPTIC or STEADY):
			break
		if dtime+3000 > h.t > dtime and VSTEP:
			blah3.rs=1e-3
		elif VSTEP:
			blah3.rs=1e9
		else:
			pass
			################### yeet this into its own function #################
		if JAC and (STEADY or SYNAPTIC) and h.t > pstable['idel']+STEPLEN - 100:
			pstates = h.Vector()
			cv.states(pstates)
			import neuron_jacobian as nj
			jac = h.Matrix()
			nj.get_jacobian(cv,jac,relstep=1e-6)
			temp = h.Vector()
			jac_p = []
			sz = int(jac.ncol())
			#print jac, jac.ncol()
			for i in range(sz):
				jac.getcol(i,temp)
				jac_p.append(temp.to_python())
				a = h.ref('')
				cv.statename(i,a)
				j=0
				for things in temp.x:
					b = h.ref('')
					cv.statename(j,b)
					print a, b, things
					j+=1
					
			jac_n = np.array(jac_p)
			jac_n.resize([sz,sz])
			
			
			from scipy import linalg
			a,b = linalg.eig(jac_n)
			print a
			quit()
			##################### end yeet #######################################
		if h.t - told > 0:
			dvdt = (loc.v-vold)/(float(h.t)-told)
		else:
			dvdt = dvdtold
		dvdtold = dvdt
		vold = loc.v
		told = float(h.t)
		rat = pstable['ratio']

		if not SYNAPTIC:
			if ALIGN and not FaA: # align to fixed point on AP to compare AHP, shape between models.
				if h.t < ALIAT:
					continue
				elif h.t > ALIAT and not FaA and loc.v <-40:
					continue
				elif ALIGN and loc.v > -40 and not FaA: # FaA = First spike after alignment offset
					offset = h.t
					FaA = 1		
			time = h.t-offset	
			#if (2000<h.t < 4000) or not STEADY:
			gkainf = pow(loc.pinf_hhb,3)*loc.qinf_hhb
			gka = pow(loc.p_hhb,3)*loc.q_hhb
			fp.write('%e  %e  %e  %e  %e  %e  %e  %e  %e  %e  %e  ' %(time, loc.v, blah.amp, loc.o1_NaMark, loc.c1_NaMark, loc.c2_NaMark, loc.i1_NaMark,rat*loc.i2_NaMark,loc.i1_NaMark + loc.i2_NaMark,dvdt,1.0/3.14159*1e6*(loc.ina+loc.ik+loc.ica+loc.ihcn_hcn)-1.0/3.14159*1e8*blah2.amp/h.area(0.5,loc)))
			fp.write('%e  %e  %e  %e  %e  %e  %e  %e' %(loc.ina_NaMark, loc.ikhh_hhb, loc.ika_hhb, loc.ik_kca, loc.ik, gka, gkainf, loc.ika_hhb+loc.ina_NaMark+loc.ik_leak+loc.ina_leak))
		else:
			#if (2000<h.t < 4000):
				fp.write('%e  %e  %e  %e  %e  %e  %e  %e  %e  %e  %e  %e  ' %(h.t, loc.v, loc.inmda_nmda+loc.ica_nmda, loc.o1_NaMark, loc.c1_NaMark, loc.c2_NaMark, loc.i1_NaMark,rat*loc.i2_NaMark, loc.i1_NaMark + loc.i2_NaMark, loc.m_kca,dvdt,1.0/3.14159*1e6*(loc.ina+loc.ik+loc.ica+loc.ihcn_hcn+loc.inmda_nmda)))
		fp.write('\n')
	fp.close()
	interval = -1
	minterval = 1e9
	if not SYNAPTIC:
		for t in freqvec:

			if interval < 0:
				try:
					interval = freqvec[1] - freqvec[0]
					told = freqvec[0]
					continue
				except:
					print 'no spikes'
					break
			else:
				interval = t - told
				if t < 6000 and pstable['idur'] > 1000 and not STEADY:
					print 1000/(t-told), ampvec[int(t+told)/2]
				if interval < minterval:
					minterval = interval
				told = t
	#print 1000.0/minterval


	
	return 0
	
if RUN:
	cell = run_func(STEPLEN)
	#print cell.nrn.soma.gkhhbar_hhb

def dingrun_fun():
	cells = [dopa(0,[1,2],pstable),dopa(0,[1,2],pstable)]
	i=0
	for cell in cells:
		for s in cell.nrn.all:
			s.L = pstable['size']
			s.dist_NaMark = pstable['slow']
			if i:
				s.gnabar_NaMark = 0
				#s.hshift_NaMark = -pstable['na_shift']"""
		i+=1
	blah0 = h.VClamp(cells[0].nrn.soma(0.5))
	blah0.dur[0] = 1e9
	blah1 = h.VClamp(cells[1].nrn.soma(0.5))
	blah1.dur[0] = 1e9
	
	recvecs = [h.Vector(),h.Vector()] 
	recvecs[0].record(blah0._ref_i,0.1)
	recvecs[1].record(blah1._ref_i,0.1)
	
	volpy = []
	
	for j in range(10000):
		volpy.append(-70)
	
	for i in range(10):
		for j in range(1000):
			volpy.append(-70)
		for j in range(30):
			volpy.append(0)
			
	for j in range(10000):
		volpy.append(-70)
		
	volh = h.Vector(volpy)
	volh.play(blah0._ref_amp[0],0.1)
	volh.play(blah1._ref_amp[0],0.1)
	cv = h.CVode()
	h.finitialize()
	while h.t < 0.1*len(volh):
		h.fadvance()
		#print h.t, cells[0].nrn.soma.v, blah0.i, blah1.i, cells[0].nrn.soma.i2_NaMark
		
	recvecs[0].sub(recvecs[1])
	
	for i in range(len(volpy)):
		print i*0.1, recvecs[0].x[i]/recvecs[0].min(), volpy[i]#"""
	return 0

if DINGRUN:
	dingrun_fun()




def array_func(extern_param_file):
	print extern_param_file
	if not extern_param_file.endswith('.py'):
		raise NameError('run parameter files must be python - refer to nmda-gaba-array.py for example')
		quit()
		return 'bad input'
	else:
		#from iamp-slow-parms import *
		exec('from %s import *' % extern_param_file.rstrip('.py'))
		try: var0
		except NameError: var0 = 'iamp'
		try: var1
		except NameError: var1 = 'slow'
		try: range0
		except NameError: range0 = np.arange(0,101e-3,2.5e-3)
		try: range1
		except NameError: range1 = np.arange(0.1,3.01,0.1)
		try: is_ramp
		except: is_ramp = 0
		
	numcells = len(range0)*len(range1)
	print var0, var1, numcells
	#quit()
	
	cells = []
	stims = []
	lvec = []
	tvec = []
	vvec = []
	
	pc = h.ParallelContext()
	pc.nthread(32)
	nhost = int(pc.nhost())

	stim_type = 0
	ramp = []
	if var0 in ['gnmda', 'ggaba'] or var1 in ['gnmda','ggaba']:
		step = []
		for i in range(pstable['idel']):#+pstable['idur']):
			step.append(0)
		for i in range(STEPLEN):#pstable['idur']):
			step.append(gnmdamax)		
		for i in range(pstable['idel']):
			step.append(0)
			#svec = h.Vector(ramp)
		stim_type = 2
	elif is_ramp:
		for i in range(pstable['idel']):
			ramp.append(0)
		for i in range(int(pstable['idur'])):
			if i < (pstable['idur'])/2.0:
				ramp.append(2*(i)/float(pstable['idur']))
			else:
				ramp.append(2*(pstable['idur']-i)/float(pstable['idur']))
		for i in range(pstable['idel']):
			ramp.append(0)
		#svec = h.Vector(ramp)
		stim_type = 1
	# max(ramp)
	parms = pstable.copy() # copying like lists only copies the reference to shared data
	try: STEPLEN
	except:
		STEPLEN=2000
	i=0
	for val0 in range0:
		for val1 in range1:
			parms[var0] = val0
			parms[var1] = val1
			if var1 == 'both':
				parms['gkhh'] = val1*pstable['gkhh']
				parms['gnahh'] = val1*pstable['gnahh']
			cells.append(dopa(0,[val0,val1],parms)) # cell creation
			cells[i].ntc.threshold = -20
			if stim_type in [0,1]:
				stims.append(h.IClamp(cells[i].nrn.soma(0.5)))
				if stim_type == 0:
					stims[i].dur = STEPLEN
					stims[i].delay = parms['idel']
					stims[i].amp = parms['iamp']
				if stim_type == 1:
					stims[i].dur = 2*parms['idel']+parms['idur']
					stims[i].delay = 0
					lvec.append(h.Vector(ramp))
					lvec[i].mul(parms['iamp'])
					lvec[i].add(parms['basal'])
					#print lvec[i].max()
					STEPLEN=parms['idur']
					lvec[i].play(stims[i]._ref_amp,1)
			if stim_type in [2]:
				lvec.append(h.Vector(step))
				if var0 not in ['gnmda','ggaba']:
					lvec.pop()
				else:
					lvec[i].mul(val0)
					exec('lvec[i].play(cell[i].nrn.soma._ref_%s' % (var0)+'bar_%s,1)' %(var0[1:])) # var0 = 'gndma' would yield _ref_gnmdabar_nmda
				lvec.append(h.Vector(step))
				if var1 not in ['gnmda','ggaba']:
					lvec.pop()
				else:
					lvec[i].mul(val0)
					exec('lvec[i].play(cell[i].nrn.soma._ref_%s' % (var1)+'bar_%s,1)' %(var1[1:]))
			# spike time recording is part of the dopa class, but not spike magnitude
			# to do spike magnitude recordings, we have to set up voltage recordings
			# this recording can trigger when a spike event happens
			vvec.append(h.Vector())
			tvec.append(h.Vector())		
			# going to try being tricky and dynamically setting voltage recording times
			vvec[i].record(cells[i].ntc._ref_x)
			tvec[i].record(h._ref_t) # these need not be identical under parallel context.
			i+=1


	print len(cells)
	#quit()
	h.finitialize()
	h.t = 0
	if stim_type in [0,1]:
		tstop = 2*parms['idel']+STEPLEN
	if stim_type in [2]:
		tstop = 2*parms['idel']+parms['idur']
		
	pc.psolve(tstop)
		
	# get number of spikes during each stimulus
	nspikes = []
	firstspikes = []
	lastspikes = []
	freq = []
	fp = open('%s_vs_%s_%s.dat' %(var0,var1,affix),'w')
	for i in range(len(cells)):
		#print len(tvec)
		temp = h.Vector()
		temp.where(cells[i].srec,'()',parms['idel'],tstop-parms['idel']) # get spikes in window
		start = tvec[i].indwhere('>=',parms['idel'])
		end = tvec[i].indwhere('>=',tstop-parms['idel']-1)
		tvec[i].remove(end,len(tvec[i])-1)
		tvec[i].remove(0,start-1)
		vvec[i].remove(end,len(vvec[i])-1)
		vvec[i].remove(0,start-1)
		#if is_ramp:
			#lvec[i].remove(end,len(lvec[i])-1)
			#lvec[i].remove(0,start-1)
		blockv = vvec[i][-1]
		try:
			first = temp[0]
		except:
			first = 0
			last = start
		try:
			last = temp[len(temp)-1]

		except:
			try:
				last = temp[0]
			except:
				last = 0
		print first, last

		# use spike times from spike recorder, and uses to create bounds on spike waveform
		# get max an min values of voltage over that interval to create spike magnitudes\
		if first and last:
			if len(temp) < 2:
				firstpeak = vvec[i].max(tvec[i].indwhere('>=',first),len(tvec[i])-1)
				firstahp = vvec[i].min(tvec[i].indwhere('>=',first),len(tvec[i])-1)
				lastpeak = firstpeak
				lastahp = firstahp
			elif len(temp) < 3 :
				#print len(tvec[i]), tvec[i][-1],tvec[i][0]
				firstpeak = vvec[i].max(tvec[i].indwhere('>=',first),min(tvec[i].indwhere('>=',temp[1]),len(tvec[i])-1))
				firstahp = vvec[i].min(tvec[i].indwhere('>=',first),min(tvec[i].indwhere('>=',temp[1]),len(tvec[i])-1))
				if tstop-parms['idel']-last < 10 and not is_ramp:
					lastpeak= vvec[i].max(tvec[i].indwhere('>=',temp[len(temp)-2]),len(tvec[i])-1) # x[-1] does not work as expected on neuron objects
					lastahp = vvec[i].min(tvec[i].indwhere('>=',temp[len(temp)-2]),len(tvec[i])-1)
				else:
					lastpeak = vvec[i].max(tvec[i].indwhere('>=',last),tvec[i].indwhere('>=',last+10)) # x[-1] does not work as expected on neuron objects
					lastahp = vvec[i].min(tvec[i].indwhere('>=',last),tvec[i].indwhere('>=',last+50)) # x[-1] does not work as expected on neuron objects
			else:
				#print len(tvec[i]), tvec[i][-1],tvec[i][0]
				firstpeak = vvec[i].max(tvec[i].indwhere('>=',first),min(tvec[i].indwhere('>=',temp[1]),tvec[i].indwhere('>=',temp[2])))
				firstahp = vvec[i].min(tvec[i].indwhere('>=',first),min(tvec[i].indwhere('>=',temp[1]),tvec[i].indwhere('>=',temp[2])))
				if tstop-parms['idel']-last < 10 and not is_ramp:
					lastpeak= vvec[i].max(tvec[i].indwhere('>=',temp[len(temp)-3]),tvec[i].indwhere('>=',temp[len(temp)-2])) # x[-1] does not work as expected on neuron objects
					lastahp = vvec[i].min(tvec[i].indwhere('>=',temp[len(temp)-3]),tvec[i].indwhere('>=',temp[len(temp)-2]))
				else:
					try:
						lastpeak = vvec[i].max(tvec[i].indwhere('>=',last),tvec[i].indwhere('>=',last+10)) # x[-1] does not work as expected on neuron objects
						lastahp = vvec[i].min(tvec[i].indwhere('>=',last),tvec[i].indwhere('>=',last+50)) # x[-1] does not work as expected on neuron objects
					except:
						pass # need to print when there is an error even if its 0,0
			firstmag = firstpeak - firstahp
			lastmag = lastpeak - lastahp
			ratio = lastmag/firstmag
		else:
			firstmag = 0
			lastmag = 0
			ratio = 1
		if last == first:
			freq = 0
		else:
			if is_ramp:
				maxfreq = 0
				for j in range(len(temp)-1):
					freq = 1e3/(temp[len(temp)-j-1]-temp[len(temp)-j-2])
					if freq > maxfreq:
						maxfreq = freq
				freq=maxfreq
			else:
				freq = 1e3*(len(temp)-1)/float(last-first)
		if freq > 0:
		  if tstop-parms['idel']-last < 2000.0/freq and not is_ramp:
			blockv = -60
			last = tstop-parms['idel']
		fp.write('%e  %e  %d  %e  %e  %e  %e  %e  %e  ' %(cells[i].p1, cells[i].p2, len(temp), freq, last, ratio, firstmag, lastmag, last-first))
		if is_ramp:
			fp.write('%e\n' % lvec[i][int(last)])
		else:
			fp.write('%e\n' % blockv)
		
	fp.close()


if ARRAY:
	array_func(EXTERN)	

if SYNSTEPS:
	# create arrays of equal length for dc current ampa, nmda say 10 to 200 in steps of 10
	cells = []
	gidlist = []

	NSTEPS = 500
	PARALLEL = 1
	if PARALLEL:
		pc = h.ParallelContext() # clean up PC
		pc.nthread(64)
		nhost = int(pc.nhost())	#pc.nthread(20)
			
	STEP = 1e-6 #
	CHONK=STEPLEN
	step = []
	for i in range(pstable['idel']):#+pstable['idur']):
		step.append(0)
	
	#for i in range(pstable['idur']):
	for i in range(CHONK):

		step.append(1)
		
	for i in range(pstable['idel']):
		step.append(0)
		
	ampvec = h.Vector(step)
	#add an NMDA channel to cell
	nmdavec = []
	stimvec = []
	recvec = []
	nc = []

	for i in range(NSTEPS):
		gnmdabar = (i+1)*STEP
		dc = gnmdabar*(5) # need to adjust for area S/cm2 = mA/cm2
		nmdavec.append(ampvec.c())
		nmdavec[i].mul(gnmdabar)
		#print max(nmdavec[i])
		for j in range(3):
			cells.append(dopa(0,[1,2],pstable))
			nc.append(h.NetCon(cells[3*i+j].nrn.soma(0.5)._ref_v,None,sec=cells[3*i+j].nrn.soma))
			nc[3*i+j].threshold = -20
			recvec.append(h.Vector())
			nc[3*i+j].record(recvec[3*i+j])
			if j < 2:
				for s in cells[3*i+j].nrn.all:
					s.insert('nmda')
					s.cafrac_nmda = pstable['cafrac']
					nmdavec[i].play(s(0.5)._ref_gnmdabar_nmda,1)
					if j==1:
						s.cMg_nmda = 0 # convert to AMPA
						s.scale_nmda = 0.3
					else:
						s.cMg_nmda = 1.2
			else:
				stimvec.append(h.IClamp(cells[3*i+2].nrn.soma(0.5)))
				#stimvec[i].dur = pstable['idur']
				stimvec[i].dur = CHONK

				stimvec[i].delay = pstable['idel']
				stimvec[i].amp = dc*h.area(0.5,sec=cells[3*i+2].nrn.soma)*2e-2 # 1e-2 takes mA-um2/cm2 to pA
				#only works for 1 compartment model- would need to sum over sections for larger
	h.finitialize()

	#cv = h.CVode()
	#cv.active(True)
	h.t = 0
	
	if PARALLEL:
		pc.psolve(pstable['idel']+CHONK)
	else:
		cv = h.CVode()
		cv.active(True)
		cv.solve(pstable['idel']+CHONK)
	fp = open('synaptic_%s%s.dat' % (affix,affix2),'w')
	for i in range(NSTEPS):
		for j in range(3):
			temp = recvec[3*i+j]
			#print len(temp),
			nspikes = 0
			firstspike=0
			lastspike=1e9
			kstart = 0
			for times in temp:
				if times < pstable['idel'] or times > pstable['idel']+CHONK:#+pstable['idur']:
					kstart+=1
					continue
				nspikes += 1
				if firstspike < pstable['idel']:
					firstspike = times
				lastspike = times
			kend = kstart + nspikes
			if j == 0:
				print (i+1),
				fp.write('%i  ' % (i+1))
			elif j == 1:
				print (i+1)*STEP,#*0.1,
				fp.write('%e  ' % ((i+1)*STEP))
			else:
				print stimvec[i].amp,
				fp.write('%e  ' % (stimvec[i].amp))
			
			print nspikes,
			fp.write('%i  ' % (nspikes))
			if nspikes > 0:
			  print lastspike-pstable['idel'],
			  fp.write('%e  ' % float(lastspike-pstable['idel']))
			else:
			  print 0,
			  fp.write('0  ')
			if nspikes > 1:
				kmid = int((kstart+kend)/2)
				midisi= temp[kmid+1]-temp[kmid]
				fp.write('%e  ' % float(1000.0/midisi))
				print 1000.0/midisi,
				#print 1000*(nspikes-1)/(lastspike-firstspike),
				#fp.write('%e  ' % (float(1000*(nspikes-1))/float(lastspike-firstspike)))
			else:
				print 0,
				fp.write('0  ')
		print
		fp.write('\n')
	
	#print h.stopsw()
	# tune dc current such that current maps roughly to ampa current at -50 mV

def random_cells():
	from random import random
	variables = ['gkca','taukv4','ghcn','gkhh','slow']
	variables.sort()
	nvar = len(variables)
	ranges={'gkhh':[2,4],'ghcn':[0,1],'gkca':[0,1],'taukv4':[0.05,1],'slow':[0.5,2.5]}
	is_ramp = 1
		
	ncells = 1000
	#print var0, var1, numcells
	#quit()
	
	cells = []
	stims = []
	lvec = []
	tvec = []
	vvec = []
	
	pc = h.ParallelContext()
	pc.nthread(32)
	ramp = []
	if is_ramp:
		for i in range(pstable['idel']):
			ramp.append(0)
		for i in range(int(pstable['idur'])):
			if i < (pstable['idur'])/2.0:
				ramp.append(2*(i)/float(pstable['idur']))
			else:
				ramp.append(2*(pstable['idur']-i)/float(pstable['idur']))
		for i in range(pstable['idel']):
			ramp.append(0)
		#svec = h.Vector(ramp)
		stim_type = 1
	# max(ramp)
	parms = pstable
	try: STEPLEN
	except:
		STEPLEN=2000
	values = []
	for i in range(ncells):
			parms = pstable
			#randomize variable uniformly over intervals
			temp = {}
			for var in variables:
				parms[var] = ranges[var][0]+(ranges[var][1]-ranges[var][0])*random()
				temp[var] = parms[var]
			values.append(temp)
			cells.append(dopa(0,[1,2],parms)) # cell creation
			cells[i].ntc.threshold = -20
			if stim_type in [0,1]:
				stims.append(h.IClamp(cells[i].nrn.soma(0.5)))
				if stim_type == 0:
					stims[i].dur = STEPLEN
					stims[i].delay = parms['idel']
					stims[i].amp = parms['iamp']
				if stim_type == 1:
					stims[i].dur = 2*parms['idel']+parms['idur']
					stims[i].delay = 0
					lvec.append(h.Vector(ramp))
					lvec[i].mul(parms['iamp'])
					lvec[i].add(parms['basal'])
					STEPLEN=parms['idur']
					lvec[i].play(stims[i]._ref_amp,1)
			# spike time recording is part of the dopa class, but not spike magnitude
			# to do spike magnitude recordings, we have to set up voltage recordings
			# this recording can trigger when a spike event happens
			vvec.append(h.Vector())
			tvec.append(h.Vector())		
			# going to try being tricky and dynamically setting voltage recording times
			vvec[i].record(cells[i].ntc._ref_x)
			tvec[i].record(h._ref_t) # these need not be identical under parallel context.
			i+=1

	h.finitialize()
	h.t = 0
	if stim_type in [0,1]:
		tstop = 2*parms['idel']+STEPLEN
	if stim_type in [2]:
		tstop = 2*parms['idel']+parms['idur']
		
	pc.psolve(tstop)
		
	# get number of spikes during each stimulus
	nspikes = []
	firstspikes = []
	lastspikes = []
	freq = []
	fname = 'random_'
	for var in variables:
		fname += '%s_' % var
	fname += '%s.dat' % affix
	fp = open(fname,'w')
	for i in range(len(cells)):
		#print len(tvec)
		temp = h.Vector()
		temp.where(cells[i].srec,'()',parms['idel'],tstop-parms['idel']) # get spikes in window
		start = tvec[i].indwhere('>=',parms['idel'])
		end = tvec[i].indwhere('>=',tstop-parms['idel']-1)
		tvec[i].remove(end,len(tvec[i])-1)
		tvec[i].remove(0,start-1)
		vvec[i].remove(end,len(vvec[i])-1)
		vvec[i].remove(0,start-1)
		#if is_ramp:
			#lvec[i].remove(end,len(lvec[i])-1)
			#lvec[i].remove(0,start-1)
		blockv = vvec[i][-1]
		try:
			first = temp[0]
		except:
			first = 0
			last = start
		try:
			last = temp[len(temp)-1]

		except:
			try:
				last = temp[0]
			except:
				last = 0
		print first, last

		# use spike times from spike recorder, and uses to create bounds on spike waveform
		# get max an min values of voltage over that interval to create spike magnitudes\
		if first and last:
			if len(temp) < 2:
				firstpeak = vvec[i].max(tvec[i].indwhere('>=',first),len(tvec[i])-1)
				firstahp = vvec[i].min(tvec[i].indwhere('>=',first),len(tvec[i])-1)
				lastpeak = firstpeak
				lastahp = firstahp
			elif len(temp) < 3 :
				#print len(tvec[i]), tvec[i][-1],tvec[i][0]
				firstpeak = vvec[i].max(tvec[i].indwhere('>=',first),min(tvec[i].indwhere('>=',temp[1]),len(tvec[i])-1))
				firstahp = vvec[i].min(tvec[i].indwhere('>=',first),min(tvec[i].indwhere('>=',temp[1]),len(tvec[i])-1))
				if tstop-parms['idel']-last < 10 and not is_ramp:
					lastpeak= vvec[i].max(tvec[i].indwhere('>=',temp[len(temp)-2]),len(tvec[i])-1) # x[-1] does not work as expected on neuron objects
					lastahp = vvec[i].min(tvec[i].indwhere('>=',temp[len(temp)-2]),len(tvec[i])-1)
				else:
					lastpeak = vvec[i].max(tvec[i].indwhere('>=',last),tvec[i].indwhere('>=',last+10)) # x[-1] does not work as expected on neuron objects
					lastahp = vvec[i].min(tvec[i].indwhere('>=',last),tvec[i].indwhere('>=',last+50)) # x[-1] does not work as expected on neuron objects
			else:
				#print len(tvec[i]), tvec[i][-1],tvec[i][0]
				firstpeak = vvec[i].max(tvec[i].indwhere('>=',first),min(tvec[i].indwhere('>=',temp[1]),tvec[i].indwhere('>=',temp[2])))
				firstahp = vvec[i].min(tvec[i].indwhere('>=',first),min(tvec[i].indwhere('>=',temp[1]),tvec[i].indwhere('>=',temp[2])))
				if tstop-parms['idel']-last < 10 and not is_ramp:
					lastpeak= vvec[i].max(tvec[i].indwhere('>=',temp[len(temp)-3]),tvec[i].indwhere('>=',temp[len(temp)-2])) # x[-1] does not work as expected on neuron objects
					lastahp = vvec[i].min(tvec[i].indwhere('>=',temp[len(temp)-3]),tvec[i].indwhere('>=',temp[len(temp)-2]))
				else:
					try:
						lastpeak = vvec[i].max(tvec[i].indwhere('>=',last),tvec[i].indwhere('>=',last+10)) # x[-1] does not work as expected on neuron objects
						lastahp = vvec[i].min(tvec[i].indwhere('>=',last),tvec[i].indwhere('>=',last+50)) # x[-1] does not work as expected on neuron objects
					except:
						pass # need to print when there is an error even if its 0,0
			firstmag = firstpeak - firstahp
			lastmag = lastpeak - lastahp
			ratio = lastmag/firstmag
		else:
			firstmag = 0
			lastmag = 0
			ratio = 1
		if last == first:
			freq = 0
		else:
			if is_ramp:
				maxfreq = 0
				for j in range(len(temp)-1):
					freq = 1e3/(temp[len(temp)-j-1]-temp[len(temp)-j-2])
					if freq > maxfreq:
						maxfreq = freq
				freq=maxfreq
			else:
				freq = 1e3*(len(temp)-1)/float(last-first)
		if freq > 0:
		  if tstop-parms['idel']-last < 2000.0/freq and not is_ramp:
			blockv = -60
			last = tstop-parms['idel']
		if freq > 0: # only include cells that produce spikes
			for var in variables:
				fp.write('%e  ' % values[i][var])
			fp.write('%d  %e  %e  %e  %e  %e  %e  ' %(len(temp), freq, last, ratio, firstmag, lastmag, last-first))
			if is_ramp:
				fp.write('%e\n' % lvec[i][int(last)])
			else:
				fp.write('%e\n' % blockv)
		
	fp.close()
	
if RANDOM:
	random_cells()


def pulse_func(): # simulates activation/ (fast) inactivation experiments on nucleated patch
	msteps = np.arange(-120,31,5)
	hsteps = np.arange(-120,31,5)
	mln = len(msteps)
	hln = len(hsteps)
	hhold = -100
	mhold = -100
	htest = 0
	warm = 1000
	condpulse = 50
	spikepulse = 5
	cells = []
	clamps = []
	recvectors = []
	i=0
	h.dt = 0.02
	mtrecord = np.arange(0,warm+condpulse+spikepulse+100, 0.01)
	mtvec = h.Vector(mtrecord)
	htvec = h.Vector(mtrecord)
	#print mtvec.x[0]
	
	mt1 = warm
	mt2 = warm+spikepulse
	
	ht1 = warm+condpulse
	ht2 = warm+condpulse+spikepulse
	
	mt1*=100
	mt2*=100
	ht1*=100
	ht2*=100
	
	mt1+=5
	mt2-=5
	
	ht1+=5
	ht2-=5
	
	
	for j in range(2*mln):
		h.pop_section() # kludge fix to section stack overflow
		cells.append(dopa(0,[1,2],pstable))
		cells[i].nrn.soma.L = 0.1 # required to have space clamp
		clamps.append(h.SEClamp(cells[i].nrn.soma(0.5)))
		clamps[i].dur1 = warm
		clamps[i].dur2 = spikepulse
		clamps[i].dur3 = condpulse
		clamps[i].amp1 = mhold
		if j >= mln:
			clamps[i].amp2 = msteps[j-mln]
			for s in cells[i].nrn.all:
				s.gnabar_NaMark = 0
				s.gnabar_FastNaMark=0
		else:
			clamps[i].amp2 = msteps[j]
		clamps[i].amp3 = mhold
		recvectors.append(h.Vector())
		recvectors[i].record(clamps[i]._ref_i,mtvec)
		i+=1

	for j in range(2*hln):
		cells.append(dopa(0,[1,2],pstable))
		clamps.append(h.SEClamp(cells[i].nrn.soma(0.5)))
		cells[i].nrn.soma.L = 0.1
		clamps[i].dur1 = warm
		clamps[i].dur2 = condpulse
		clamps[i].dur3 = spikepulse
		clamps[i].amp1 = hhold
		if j >= hln:
			clamps[i].amp2 = hsteps[j-hln]
			for s in cells[i].nrn.all:
				s.gnabar_NaMark = 0
				s.gnabar_FastNaMark=0
		else:
			clamps[i].amp2 = hsteps[j]
		clamps[i].amp3 = htest
		recvectors.append(h.Vector())
		recvectors[i].record(clamps[i]._ref_i,htvec)
		i+=1
		

	pc = h.ParallelContext()
	pc.nthread(NTHREADS)
	#cv = h.CVode()
	h.finitialize()
	h.t = 0
	TSTOP = warm + condpulse+spikepulse
	while h.t < warm + condpulse+spikepulse+100:
		h.fadvance()
	#pc.psolve(TSTOP)
	
	for i in range(mln):
		recvectors[i].sub(recvectors[i+mln])
	

	for i in range(hln):
		recvectors[i+2*mln].sub(recvectors[i+hln+2*mln])
	
	#pc.nthread(1)
	dln = len(recvectors[0])
	maxmcur = 0
	

	fp=open('mdiff_%s.dat' % affix,'w')

	for j in range(dln):
		if mt1 > j or j > mt2:
			continue
		#if abs(j-100*warm) <20 or abs(j-100*(warm+spikepulse))<20: # ignore data within 0.2 ms?
		#	continue
		fp.write('%e  ' % (0.01*j))	
		for i in range(mln):
			#if i==1 and j>warm*100:
				#print j, recvectors[i].x[j], recvectors[i+mln].x[j]
			fp.write('%e  ' % recvectors[i][j])
		fp.write('\n')
	fp.close()
	for i in range(mln):
		temp = recvectors[i].min(mt1,mt2)/(msteps[i]-50.0)
		if abs(temp) > abs(maxmcur) and i > 0:
			maxmcur = temp
	for i in range(mln):
		if mln != hln:
			print msteps[i], abs(recvectors[i].min(mt1,mt2)/(maxmcur*(msteps[i]-50.0))) 
	
	fp=open('hdiff_%s.dat' % affix,'w')
	maxhcur = 0
	for i in range(hln):
		temp =recvectors[i+2*mln].min(ht1,ht2)
		if abs(temp) > abs(maxhcur):
			maxhcur = temp
	for i in range(hln):
		if mln != hln:
			print hsteps[i], recvectors[i+2*mln].min(int((condpulse)*50),len(recvectors[i+2*mln])-1)/maxhcur
	for j in range(len(recvectors[2*mln])):
		if j < mt1 or j > mt2:
			continue
		fp.write('%e  ' % (0.01*j))
		for i in range(hln):
			fp.write('%e  ' % recvectors[i+2*mln][j])
		fp.write('\n')
	fp.close()
	if hln==mln:
		for i in range(hln):
			print hsteps[i], recvectors[i].min(mt1,mt2), recvectors[i+2*mln].min(ht1,ht2), abs(recvectors[i].min(mt1,mt2)/(maxmcur*(msteps[i]-50.0))),recvectors[i+2*mln].min(ht1,ht2)/maxhcur
	# for each pair find difference and max (according to abs) current
	
if PULSE:
	pulse_func()


if FGI:	# older FI curve output to stdout
	Iarray1 = np.arange(-8e-3,5e-3,1e-4)
	Iarray2 = np.arange(6e-3,101e-3,1e-3)
	Iarray = np.concatenate([Iarray1,Iarray2])

	iln = len(Iarray)
	cv = h.CVode()
	pc = h.ParallelContext()
	pc.nthread(64)
	pcnt = int(pc.nthread())
	nspikes = []
	freq = []

	nbatches = int(ceil(len(Iarray)/float(pcnt)))
	#print nbatches
	breakcon = 0
	anit = 0
	prespikes = 0
	WARMUP = 2000
	RUNTIME = 8000 # note that Nyquist frequency is 0.25 hz
	for i in range(nbatches):
		if breakcon:
			break
		ncs = []
		rvs = []
		cells = []
		clamps = []
		for j in range(pcnt):
			h.pop_section() # kludge fix to section stack overflow
			# without this neuron thinks all cells sections are part of an ever expanding subtree
			cells.append(dopa(0,[1,2],pstable))
			clamps.append(h.IClamp(cells[j].nrn.soma(0.5)))
			clamps[j].dur = 1e9
			clamps[j].delay = WARMUP # 0 for 'from rest'
			for s in cells[j].nrn.all:
				if s in cells[j].nrn.somatic:
					s.L = pstable['size']
				else:
					s.L = 1e-6
				s.dist_NaMark = pstable['slow']
				s.v = -45 #-60
			try:
				clamps[j].amp = Iarray[j+pcnt*i]
			except: # klude to kill cells out range
				#print 'nope'
				cells[j] = None
				clamps[j] = None
				break
			ncs.append(h.NetCon(cells[j].nrn.soma(0.5)._ref_v,None,sec=cells[j].nrn.soma))
			ncs[j].threshold = -20
			rvs.append(h.Vector())
			ncs[j].record(rvs[j])
		
		 
		h.finitialize()
		h.frecord_init()
		h.t = 0
		#while h.t < RUNTIME:
		#	h.fadvance()
		pc.psolve(RUNTIME+WARMUP)
		#print 'batch %d of %d done' % (i, nbatches)
		for j in range(len(cells)):
			if j == len(rvs):
				break
			if len(rvs[j].x) < 3:
				tfreq1 = 0
				tfreq2 = 0
			elif rvs[j].x[-2] < WARMUP:
				tfreq1 = 0
				tfreq2 = 0
			else:
				tfreq1 = 1000.0/(rvs[j].x[-1] - rvs[j].x[-2])
				tfreq2 = 1000.0/(rvs[j].x[-2] - rvs[j].x[-3])
			
			freq.append(tfreq1)
			if not anit: # only need to check number of spike in warmup once as it is identical
				for k in range(len(rvs[j])):
					if rvs[j].x[k] > WARMUP:
						anit = 1
						prespikes = k
					break
			tnum = len(rvs[j]) -  prespikes# number of spikes after square wave starts
			nspikes.append(tnum)
			if tfreq1 > 0:
				if 2*(rvs[j].x[-1] - rvs[j].x[-2]) < RUNTIME-rvs[j].x[-1] or (rvs[j].x[-1] - rvs[j].x[-2]) > 5*(rvs[j].x[1]-rvs[j].x[0]):
					#print (rvs[j].x[-1] - rvs[j].x[-2]),  RUNTIME-rvs[j].x[-1], rvs[j].x[1] - rvs[j].x[0], rvs[j].x[-1] - rvs[j].x[-2]
					continue

			print clamps[j].amp, 
			print max(tfreq1,tfreq2), min(tfreq1,tfreq2), tnum, 
			if len(rvs[j].x) > 0:
				print rvs[j].x[-1]
			else:
				print -1
			
	

if IofV: # get steadystate
	v_array = np.arange(-85,45,1)
	import nullcline_funcs as nf
    
	f, vout, iout, cells = nf.IV_curve(dopa,args=(0,[1,2],pstable),volt_bounds=[-70,-30],voltstep=0.1)
    
    
	ln = len(vout)
    
	try:
		fp = open('%s/IofV_%s_%s.dat' % (affix, affix,affix2),'w')
	except:
		fp = open('IofV_%s_%s.dat' % (affix,affix2),'w')
		
	for i in range(ln):
		iout[i] -= pstable['iamp']
		fp.write('%e  %e  %e\n' % (vout[i],iout[i],f(vout[i])))
		
	fp.close()
			

	
if BIFURCATION:
	import nullcline_funcs as nf
	

	if SYNAPTIC:
		iarray = np.arange(0,200e-6, 1e-6)
	else:
		iarray = np.arange(-20e-3, 50e-3, 1.0e-4)
	
	cells = []
	
	
	# create IV curve or equivalent
	if SYNAPTIC: # USEOLD is th
		if USEOLD and (os.path.exists('%s/nmda_v_nullcline_%s.dat' %(affix,affix)) or os.path.exists('nmda_v_nullcline_%s.dat' %(affix))):
			gvpairs = []
			try:
				fp = open('%s/nmda_v_nullcline_%s.dat' %(affix,affix),'r')
			except:
				fp = open('nmda_v_nullcline_%s.dat' %(affix),'r')
			
			for lines in fp:
				temp = lines.split()
				g = float(temp[0])
				v = float(temp[1])
				print g, v
				gvpairs.append([g,v])
			
			fp.close()		
			
		else: # this part is time consuming so only do it once per problem if possible
			gvpairs = []
			for conductance in iarray:
				if cells ==[]:
					test, cells = nf.v_root(dopa, args=(0,[1,2,'gnmda',conductance],pstable),volt_bounds=[-50,-20],voltstep=1)
				else:
					for cell in cells:
						for s in cell.nrn.all:
							s.gnmdabar_nmda = conductance
					test, cells = nf.v_root(dopa, cells=cells, args=(0,[1,2],pstable),volt_bounds=[-50,-20],voltstep=1)
				print conductance, test[0]
				gvpairs.append([conductance,test[0]])
			
			fp = open('nmda_v_nullcline_%s.dat' % affix,'w')
			for pairs in gvpairs:

				fp.write('%e  %e\n' % (pairs[0],pairs[1]))
			fp.close()

	else:
		f, varray, curarray, cells = nf.IV_curve(dopa,args=(0,[1,2],pstable))
	    	    
		#print cells
		vb = [-80,-20]
		fs, extrema, iex, cells = nf.VI_curves(dopa,args=(0,[1,2],pstable),volt_bounds=vb)
		# last bit allows for sampling over a uniform current step
	
	
	ncells = len(cells)
	#print ncells
	
	if not SYNAPTIC:
		stim = []

		
	kicks = []
	vecs = []
	i = 0
	for current in iarray:
		if i >= ncells:
			cells.append(dopa(0,[1,2],pstable))
			ncells+=1
		vecs.append(h.Vector())
		vecs[i].record(cells[i].nrn.soma(0.5)._ref_v, 0.1)
		kicks.append(h.IClamp(cells[i].nrn.soma(0.5)))
		kicks[i].amp = -50e-3
		kicks[i].dur = 50
		kicks[i].delay = 50
		if SYNAPTIC:
			for s in cells[i].nrn.all:
				if not h.ismembrane('nmda',sec=s):
					s.insert('nmda')
				s.gnmdabar_nmda = current
				s.cMg_nmda = pstable['cmg']
				s.cafrac_nmda=pstable['cafrac']
				s.v = -60
				kicks[i] = None
				kicks[i] = h.SEClamp(cells[i].nrn.soma(0.5))
				kicks[i].amp1 = -50
				kicks[i].dur1 = 1000
				kicks[i].dur2 = 0
				kicks[i].dur3 = 0
		else: # previous currents SHOULD only exist in function
			stim.append(h.IClamp(cells[i].nrn.soma(0.5)))
			stim[i].amp = current
			if current <= 0:
				kicks[i] = None
				kicks[i] = h.SEClamp(cells[i].nrn.soma(0.5))
				kicks[i].amp1 = -50
				kicks[i].dur1 = 1000
				kicks[i].dur2=0
				kicks[i].dur3=0
				kicks[i].rs = 1e-3
			if current > 0:
				kicks[i].amp -= current
			stim[i].delay = 0
			stim[i].dur = 1e9
		i+=1
	
	while len(cells) > len(iarray):
		cells[-1] = None
		cells.pop()
		ncells-=1
			
	pc = h.ParallelContext()
	pc.nthread(64)
	
	h.finitialize()

	pc.psolve(STEPLEN)
	
	
	#free up some un-needed currents
	
	del kicks
	if not SYNAPTIC:
		del stim
	
	print affix, affix2
	fp = open('envelope_%s.dat' %(affix+affix2) , 'w')
	
	print len(cells), ncells, len(vecs)
	
	for i in range(ncells):
		if STEPLEN > 2000:
			vecs[i].remove(0,10*(STEPLEN-2000)) # remove all but last second of data
		lmin = vecs[i].min()
		lmax = vecs[i].max()
		fp.write('%e  %e  %e\n' % (iarray[i],lmin,lmax))

	
	del vecs
	fp.close()


	fp = open('IV_%s.dat' %(affix+affix2) , 'w')
	
	
	pc.nthread(1)
	del pc
	del cells
	#cv = h.CVode()
	
	
	if SYNAPTIC:
		for pairs in gvpairs:
			max_eig, comp, ncomp, eigs = nf.stability_check(dopa,pairs[1],args=(0,[1,2,'gnmda',pairs[0]],pstable))
			print pairs[0], pairs[1], max_eig, comp, ncomp
			fp.write('%e  %e  %e  %e  %d\n' % (pairs[0],pairs[1],max_eig,comp, ncomp))
	else:
		iex.sort()
		for i in iarray:
			if 3>len(iex)>1:
				fstemp = []
				if i < iex[1]:
					fstemp.append(fs[0])
				if i > iex[0]:
					fstemp.append(fs[2])
				if iex[0] < i <iex[1]:
					fstemp.append(fs[1])
				
			else:
				fstemp = fs
			for f in fstemp:
				try:
					v = f(i)
					if v < vb[0] or v > vb[1]:
						continue
				except:
					continue
				max_eig, comp, ncomp, eigs = nf.stability_check(dopa,v ,args=(0,[1,2],pstable),offset=i)
				print i, v, max_eig, comp, ncomp
				fp.write('%e  %e  %e  %e  %d\n' % (i,v,max_eig,comp,ncomp))
	
	#for i in range(len(varray)):
		#fp.write('%e  %e\n' %(varray[i],curarray[i]))
	fp.close()
	
	
	

if RUN and PRINT and GRAPH:
	if STEADY:
		os.system('xmgrace steady_%s_*.dat' % (affix))
	elif SYNAPTIC:
		os.system('xmgrace nmda_%s_*.dat' % (affix))
	else:
		os.system('xmgrace ramp_%s_*.dat' % (affix))

if DOCUMENT:
	try:
		os.system('mv *%s*.dat %s/.' % (affix, affix))
	except:
		pass

if not RUN or PRINT:

	quit()
