TITLE Calcium initiated calcium release module for interaction with a shell calcium module
 
                 
NEURON {
	SUFFIX cicr
	THREADSAFE
	RANGE  Vu, Ku, Vc, Kc, Kt, tc, tu
	POINTER cac_p, cas_p : passed from cabalshell_stores
}


UNITS {
	(molar) = (1/liter)
	(mM) =  (millimolar)
	(um) =  (micron)
	(mA) =  (milliamp)
	FARADAY = (faraday) (coulomb) 
	PI = (pi) (1)
}


PARAMETER {
        dt    (ms)
        celsius = 35  (degC)
		Vu = 4.0e-4 (mM/um2-ms)
		Vc = 3.0e-3 (/um2-ms) :
		Ku = 1.0e-3 (mM)
		Kc = 0.3e-3 (mM) :300 nM
		Tu = 1.0 (ms)
		Tc = 1.2 (ms)
		Kt = 0.2e-3 (mM)		
}

ASSIGNED {
  diam  (um)
  juinf (mM/um2-ms)
  jcinf (/um2-ms)
  cac_p
  cas_p
}

STATE {
  jcicr (mM/um2-ms) <1e-12>
  ju (mM/um2-ms) <1e-12>
}

BREAKPOINT {
  SOLVE states METHOD cnexp
}


LOCAL casq

PROCEDURE CICR(cac,cas) {
    casq = cac*cac
	juinf = Vu*(casq)/(Ku*Ku+casq)
	if (cac > Kt) {
	  jcinf = Vc*cac/(Kc+cac)*(cas-cac)
	} else {
	  jcinf = 0
	}
}

DERIVATIVE states {
  CICR(cac_p,cas_p)
  jcicr' = (jcinf-jcicr)/Tc
  ju' = (juinf-ju)/Tu
}
