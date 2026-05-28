# functions for creating bifurcation diagrams and nullcline pictures
# of NEURON models

import numpy as np
from neuron import h
import neuron_jacobian as nj
import gc
from mpi4py import MPI # for h.ParallelContext
from scipy import optimize, interpolate

VERBOSE = 0

def IV_curve(nrn_class, args=None, cells=[], volt_bounds=[-80,-20], voltstep=0.25): #nrn class assumed to have form in dep_fun.py
	
	v = min(volt_bounds)
	stimvec = []
	i=0

	h.t = 0
	h.dt = 0.2
	pc = h.ParallelContext(64)
	pc.nthread(64)
	keepcells=1
	
	if len(cells)>0:
		if not isinstance(cells[0],nrn_class):
			cells = []
		else:
			keepcells = 1
			
	while v <= max(volt_bounds):

		if len(cells) < i+1:
			cells.append(nrn_class(*args))
		stimvec.append(h.SEClamp(cells[i].nrn.soma(0.5)))
		stimvec[i].amp1 = v
		stimvec[i].dur1 =1e9
		stimvec[i].rs = 1e-3
		#print cells[i].nrn.soma.dist_NaMark
		#varray.append(cells[i].nrn.soma.v)
		v+=voltstep
		i+=1
	
	h.finitialize()
	pc.psolve(2000)
	varray = []
	iarray = []
	i=0
	for stim in stimvec:
		#print stim.i, cells[i].nrn.soma.v
		iarray.append(stim.i)
		varray.append(cells[i].nrn.soma.v)
		i+=1
	
	f = interpolate.InterpolatedUnivariateSpline(varray,iarray,k=3)
	
	if keepcells:
		return f, varray, iarray, cells
	else:
		return f, varray, iarray, []
		
def VI_curves(nrn_class, args=None, cells=[], volt_bounds=[-80,-20], voltstep=0.25):
	f, varray, iarray, cells = IV_curve(nrn_class, args=args, cells=cells, volt_bounds=volt_bounds, voltstep=voltstep)
	# find where df/dv = 0
	fp = f.derivative(1)
	fpp = f.derivative(2)
	step = 10
	v = min(volt_bounds)
	extrema = []
	fpl = fp(varray)
	fppl = fpp(varray)
	doit = True
	#print min(fpl), max(fpl), min(fppl), max(fppl), min(varray), max(varray)
	if not min(fpl) < 0 < max(fpl):
		doit = False
	

	
	while v < max(volt_bounds) and doit:
		temp = optimize.fsolve(fp,v)
		if len(extrema) == 0 and len(temp) > 0:
			extrema.append(temp[0])
		v += step

		for things in temp:
			isin=False
			for others in extrema:
				if abs(things-others) < 1e-6:
					isin = True
			if not isin:
				extrema.append(things)
	extrema.sort()		
	

	extrema = [things for things in extrema if min(volt_bounds) < things < max(volt_bounds)]

	iextrema = f(extrema)
	finverses = []			
	if len(extrema) == 0:
		finverses.append(interpolate.InterpolatedUnivariateSpline(iarray,varray,k=3))
	else:
		extremeold = min(volt_bounds)
		for extreme in extrema:
			vtemp = [things for things in varray if extremeold <= things <= extreme]
			vtemp.append(extreme)
			itemp = f(vtemp)
			if itemp[-1] < itemp[0]:
				temp = itemp[::-1]
				itemp = temp
				temp = vtemp[::-1]
				vtemp = temp
			finverses.append(interpolate.InterpolatedUnivariateSpline(itemp,vtemp,k=3))
			extremeold=extreme
		
	
		vtemp = [things for things in varray if extremeold <= things <= max(volt_bounds)]
		vtemp.append(max(volt_bounds))
		itemp = f(vtemp)
		if itemp[-1] < itemp[0]:
			temp = itemp[::-1]
			itemp = temp
			temp = vtemp[::-1]
			vtemp = temp
		finverses.append(interpolate.InterpolatedUnivariateSpline(itemp,vtemp,k=3))
	

	return finverses, extrema, iextrema, cells


def v_root(nrn_class, cells=[],args=None, init=-40, volt_bounds=[-80,-20],voltstep=1):
	if len(cells) > 0:
		keepcells = 1
	f, varray, iarray, cells = IV_curve(nrn_class,volt_bounds=volt_bounds,args=args,cells=cells,voltstep=voltstep)
	fp = f.derivative(1)
	zeros = optimize.fsolve(f,init,fprime=fp)

	return zeros, cells


def clear_cells(nrn_class, nuke=False):
	#for sec in h.allsec():
		#h.delete_section(sec=sec) # this kills ALL the neuron objects
	if nuke: # this kills all things in the class, probably slow.
		for obj in gc.get_objects():
			if isinstance(obj, nrn_class):
				for s in obj.nrn.all:
					h.delete_section(sec=s)
				del obj

def stability_check(nrn_class, voltage, args=None,offset=0):
	# need to ensure there are no objects created

	h.t = 0
	h.dt = 0.2
	clear_cells(nrn_class,nuke=True) # clear cells may be required

	cell = nrn_class(*args)
	cv = h.CVode()
	cv.active(1)
	h.t = 0
	h.dt = 0.1
	if offset != 0: # for stability under iclamp, though it should not affect jacobian
		stim = h.IClamp(cell.nrn.soma(0.5))
		stim.dur = 1e9
		stim.amp = offset
		stim.delay = 0
		
	vc = h.SEClamp(cell.nrn.soma(0.5))
	vc.amp1 = voltage
	vc.dur1 = 1e9
	vc.rs = 1e-3
	
	stat = h.SaveState()
	
	h.finitialize()
	cv.solve(1000)

	stat.save()

	vc = None # need to kill the voltage clamp as it 'counts' during the jacobian calculation
				# this could actually be very useful for find when voltage clamp is ineffective
				# as this amounts to the stability of coupled oscillators
	
	h.finitialize()
	
	stat.restore()
	
	#print cell.nrn.soma.v
	
	#sz = nj.get_size(cv)
	#print sz
	#quit()
	jac_obj = nj.get_jacobian(cv)
	
	eigs, eigvec = np.linalg.eig(jac_obj)
	
	#print eigs
	
	max_eig = -1e9
	ncomp = 0
	
	for i in range(len(eigs)):
		#print np.imag(eigs[i]),
		if abs(np.imag(eigs[i])) < 1e-12:
			eigs[i] = np.real(eigs[i])
			if abs(eigs[i]) < 1e-12:
				eigs[i] = 0 
		else:
			ncomp +=1
	#print
	comp = 0
	for things in eigs:
		if np.real(things) > max_eig and abs(np.real(things)) > 1e-12:
			max_eig = np.real(things)
			comp = np.imag(things)
	
	return max_eig, comp, ncomp, eigs
