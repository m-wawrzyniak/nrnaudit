# use CVode.f to approximate jacobian numerically 
# wildly inefficient but functional
# no way to apriori know 0's - 
# but could probably infer by section for multicompartment cells
# may need additional error handling for bounded values-
# eg hh or Markov states that range from 0 to 1,
# or concentrations that are positive definite
#
# Christopher Knowlton, 2020

# code assumes cvode instance is working on all the variables of interest
# if doing batch jobs, confirm the cvode instance doesn't refer to unrelated objects

from neuron import h
import numpy as np


def get_size(cvode_obj):
	states = h.Vector()
	cvode_obj.states(states)
	a =h.ref('')
	for i in range(len(states)):
		cvode_obj.statename(i,a)
		print a, states[i]
	return len(states)

def get_jacobian(cvode_obj,aor='rel',relstep=1e-6, steps=[]):
	if aor not in ['rel','abs']:
		print 'aor needs to be \'rel\' or \'abs\''
		quit(1)

	cv = cvode_obj
	states_n = h.Vector()
	cv.states(states_n)
	ns = len(states_n)
	#print 'ns=', ns
	if aor == 'abs':
		if len(absstep) != ns:
			print 'deal with this kind of error later, but the number of values in steps should be the size of the problem'
			print 'it would be better to maybe have specific steps be tuples of form \'name\', step down, step up'
			print 'and otherwise use relstep' 
			quit(2)
	
	dstates_n = h.Vector(len(states_n))
	cv.f(h.t, states_n, dstates_n)
	

	jac = np.zeros((ns,ns))
	#jac.resize(ns,ns)
	#jac.zero()
	splus_n = h.Vector()
	dplus_n = h.Vector()
	sminus_n = h.Vector()
	dminus_n = h.Vector()
	splus_n.copy(states_n)
	sminus_n.copy(states_n)
	dplus_n.copy(dstates_n)
	dminus_n.copy(dstates_n)
	a = h.ref('')

	
	for i in range(len(states_n)):
		if aor=='rel':
			if abs(states_n.x[i]) > 1e-3:
				splus_n.x[i] = splus_n.x[i]*(1+relstep)
				sminus_n.x[i] = sminus_n.x[i]*(1-relstep)
			else: # treat values near zero differently
				splus_n.x[i] = max(splus_n.x[i]+relstep,0)
				sminus_n.x[i]= min(splus_n.x[i]-relstep,0)
		if aor=='abs':
			print 'abs tolerance nyi'
			quit(2)		
		cv.f(h.t, splus_n, dplus_n)
		#print 'plus'
		cv.f(h.t,sminus_n,dminus_n)
		#print 'minus'
		diff = h.Vector()
		diff.copy(dplus_n)
		diff.sub(dminus_n)
		denom = (splus_n.x[i] - sminus_n.x[i])
		cv.statename(i,a)
		"""print a, denom, states_n[i]
		for j in range(len(splus_n)):
			cv.statename(j,a)
			print a, splus_n[j], sminus_n[j],dplus_n[j], dminus_n[j], diff[j]
		#input('press any key for next set\n') # for debugging """

		if denom != 0:
			diff.div(denom)
		elif splus_n[i] == sminus_n[i]:
			diff.x[i] = 0 
		else:
			print 'divide by zero, perturbations are identical somehow'
			quit(3)
		for j in range(len(states_n)):
			jac[i][j] = diff.x[j]
			
		splus_n.copy(states_n)
		sminus_n.copy(states_n)
	
	#print jac
	diff=None
	states_n=None
	dstates_n=None
	dplus_n=None
	dminus_n=None
	splus_n=None
	sminus_n=None
	return jac

