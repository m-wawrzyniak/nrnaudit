TITLE Calcium dependent potassium channel (small conductance SK)
 

UNITS {
        (molar) = (1/liter)
        (pA) =  (picoamp)
	(mV) =	(millivolt)
        (S)  =  (siemens)
	(mA) =	(milliamp)
	(mM) =	(millimolar)
}


:INDEPENDENT {v FROM -100 TO 50 WITH 50 (mV)}
INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
	SUFFIX kca
	USEION ca READ cai
	USEION cask READ caski VALENCE 0
	USEION k WRITE ik
	RANGE  gkbar,km,oinf,n, ik,tausk, gk
 
}


PARAMETER {
        dt  (ms)
        cai (mM)
        caski (mM)
        celsius = 35   (degC)
        gkbar = 59.00e-6 (S/cm2)
        ek = -90.0      (mV)
        km = 0.00019   (mM)
        n  = 4.0       (1)
        tausk = 27.0 (ms)
        
        
}

ASSIGNED { 
           ik		(mA/cm2)
           gk (S/cm2)
           oinf           
}

STATE {
        m <1e-4>
}


BREAKPOINT {
        SOLVE states METHOD cnexp
        :oinf = 1/(1 + pow(km/caski,n))
        :oinf = 1/(1 + pow(km/cai,n))
        gk = m*gkbar
	    ik = gk*(v - ek)
	    :ik = oinf*gkbar*(v - ek)
}

DERIVATIVE states {
   LOCAL minf
   :minf = 1/(1 + pow(km/caski,n))
   minf = 1/(1 + pow(km/cai,n))
   m' = (minf-m)/tausk



}
