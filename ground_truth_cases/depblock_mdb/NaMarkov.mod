TITLE Markov sodium channel of NaV 1.6 

COMMENT

from Balbi et al 2017, modified by Carol Upchurch and Christopher Knowlton

ENDCOMMENT

NEURON {
       SUFFIX NaMark
       USEION na WRITE ina
       RANGE gnabar, gna,  ina, o1, shift, scale,hshift,dist, oinit,DISABLE,c1c2,c2c1,o1c2,c2o1,hinit, BALBI
       :GLOBAL zhalf
}

UNITS {
	(mV) = (millivolt)
	(mA) = (milliamp)
	(nA) = (nanoamp)
	(pA) = (picoamp)
	(S)  = (siemens)
	(uS) = (microsiemens)
	(nS) = (nanosiemens)
	(pS) = (picosiemens)
	(um) = (micron)
	(molar) = (1/liter)
	(mM) = (millimolar)		
}

CONSTANT {
}

PARAMETER {
	v (mV)
	celsius (degC)
	ena = 50 (mV)
	gnabar = 550.0e-6
	shift = 0
	dist = 100
	scale = 1
	hshift = 0
	oinit=-1
	DISABLE = 1
	BALBI = 0
}

ASSIGNED {
	ina (mA/cm2)
    gna (pS/um2) 
    c1c2
    c2c1
    i1c1
    c1i1
    i2i1
    i1i2
    o1i1
    i1o1 : 0
    o1c2
    c2o1
    
    c2i1
    i1c2
}

STATE {
	c1   FROM 0 TO 1
	c2   FROM 0 TO 1
	i1   FROM 0 TO 1
	i2   FROM 0 TO 1
	o1   FROM 0 TO 1
}

INITIAL {
	rates(v)
	if(oinit < 0) { 
		SOLVE kin
		STEADYSTATE sparse
	} else {
	c1 = 0.5-2e-6
	c2 = 1e-6
	i1 = 0.5 - oinit
	i2 = 1e-6
	o1 = oinit
	}
}

BREAKPOINT {
	SOLVE kin METHOD sparse
    gna = gnabar*o1  
	ina = gna * (v - ena)
}

KINETIC kin {
	rates(v)
	~ c1 <-> c2 (c1c2,c2c1)
	~ o1 <-> c2 (o1c2,c2o1)
	~ o1 <-> i1 (o1i1,i1o1)
	~ i1 <-> c1 (i1c1,c1i1)	
	~ i1 <-> i2 (i1i2,i2i1)
	~ i1 <-> c2 (i1c2,c2i1)

	CONSERVE c1 + o1 + c2 + i1 + i2 = 1
}


:DERIVATIVE states {
:	rates(v)
:	o1 = 1.0 - c1 - c2 - i1 - i2
:	c1' = c2c1*c2 + i1c1*i1 - (c1c2+c1i1)*c1:
:	c2' = c1c2*c1 + o1c2*o1 - (c2c1+c2o1)*c2
:	i2' = i1i2*i1 - i2i1*i2
:	i1' = i2i1*i2 + o1i1*o1 + c1i1*c1 - (i1o1 + i1i2 + i1c1)*i1 
:}

PROCEDURE rates( v (mV) ) {
	LOCAL vm
	vm = v+shift
	
	if(BALBI<1+1e-6 && BALBI > 1-1e-6) {

	c1c2 = scale*DoubSig(vm,0,0,0,16.0,-5.0,-10.0)
	c2c1 = scale*DoubSig(vm,3.0,-35.0,10.0,16.0,-5.0,-10.0) :38

	c2o1 = scale*DoubSig(vm,0,0,0,16.0, -10,-10.0)
	o1c2 = scale*DoubSig(vm,3.0,-40.0,10.0,16.0,-10,-10.0) : 18

	o1i1 = DISABLE*scale*DoubSig(vm,3.0,-41.0+hshift,12.0,16.0, -11.0+hshift,-12.0) : 10 -18
	i1o1 = DISABLE*scale*DoubSig(vm,1.0e-5,-42.0+hshift,10.0,0,0,0) : control

	i1c1 = DISABLE*scale*DoubSig(vm,0.55,-65.0,7.0,0,0,0)
	c1i1 = DISABLE*scale*DoubSig(vm,0,0,0,0.55,-65.0,-11.0)

	i1i2 = dist*scale*DoubSig(vm,0,0,0,2.2e-3,-90.0,-5.0) :1000x : or here :above -50, it accumulates
	i2i1 = scale*DoubSig(vm,1.7e-2,-90.0,15.0,0,0,0) : 100x : add parameter here
	
	} else {

	c1c2 = 0.75*scale*DoubSig(vm,0,0,0,16.0,-8.0,-10.0)
	c2c1 = 0.25*scale*DoubSig(vm,2.0,-50.0,9.0,0.0,-8.0,-10.0) :38

	c2o1 = 1*scale*DoubSig(vm,0,0,0,14.0, 0,-6.0)
	o1c2 = 1*scale*DoubSig(vm,4.0,-48.0,9.0,0,0,0) : 18

	o1i1 = 0.5*DISABLE*scale*DoubSig(vm,1.0,-42.0+hshift,12.0,5.0, 10.0+hshift,-12.0) : 10 -18
	i1o1 = 0

	i1c1 = DISABLE*scale*DoubSig(vm,0.2,-65.0,10.0,0,0,0)
	c1i1 = DISABLE*scale*DoubSig(vm,0,0,0,0.2,-65.0,-11.0)
	
	c2i1 = 0.3*c1i1 : required to match Ding steady state data, not required otherwise.
	i1c2 = 0

	i1i2 = 2.0*dist*DoubSig(vm,0,0,0,2.0e-2,-25.0,-5.0) :1000x : or here :above -50, it accumulates
	i2i1 = 2.0*DoubSig(vm,1.8e-3,-50.0,10.0,0,0,0) : 100x : add parameter here 50/5
	


	
	}
}

FUNCTION boltz(x,y,z) {
               LOCAL arg
                arg= -(x-y)/z
                if (arg > 50) {boltz = 0}
				else {if (arg < -50) {boltz = 1}
                else {boltz = 1.0/(1.0 + exp(arg))}}
}

FUNCTION DoubSig(v,bh,vh,kh,bd,vd,kd){
	LOCAL boltz1, boltz2
	if(bh > 0){
		boltz1 = bh*boltz(v,vh,-kh)
	} else {
	    boltz1 = 0
	}
	if(bd > 0){
		boltz2 = bd*boltz(v,vd,-kd)
	} else {
	    boltz2 = 0
	}
	DoubSig = boltz1 + boltz2
	
}
