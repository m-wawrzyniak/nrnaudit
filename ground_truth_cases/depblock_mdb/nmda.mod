TITLE nmda current

UNITS {
        (pA) = (picoamp)
        (molar) = (1/liter)
	(mV) =	(millivolt)
        (S)  =  (siemens)
	(mA) =	(milliamp)
	(mM) =	(millimolar)
         F = (faraday) (coulomb)
         R = (mole k)  (mV-coulomb/degC)
}


INDEPENDENT {v FROM -100 TO 50 WITH 50 (mV)}

NEURON {
	SUFFIX nmda
    NONSPECIFIC_CURRENT inmda
	USEION ca READ cai WRITE ica
	RANGE  gnmdabar,inmda,gnmda, nmdasyn, tog, cafrac, eca,ica,cMg,scale
	:POINTER nmdasyn
 
}

PARAMETER {
    dt      (ms)
    cai     (mM)
    celsius = 35      (degC)
	gnmdabar = 0 (S/cm2)
    enmda  =  0 (mV)
	eca = 120.0 (mV)
	cafrac = 0.02 (1)
	cMg = 1.2 (1)
	vslope = 0.062  (1/mV)
	Mgslope = 3.57  (1)
	scale = 1
        
}

ASSIGNED { 
           gnmda  (S/cm2)
		   ica (mA/cm2)
           inmda  (mA/cm2)
           nmdasyn (1)
}




BREAKPOINT {
	gnmda = gnmdabar*scale/(1.0+(cMg/Mgslope)*exp(-vslope*v))
	ica = cafrac*gnmda*(v-eca)
    inmda = gnmda*(v-enmda)-ica
}
