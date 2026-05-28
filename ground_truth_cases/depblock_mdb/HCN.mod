TITLE HCN model from Tarfa Evans and Khaliq 2017
 
UNITS {
       (molar) = (1/liter)
       (S)  = (siemens)
       (mA) = (milliamp)
       (mV) = (millivolt)
       (mM) = (millimolar)
        F = (faraday)  (coulomb)
        R = (mole k)   (mV-coulomb/degC)
       
}
 
NEURON {
        SUFFIX hcn
        NONSPECIFIC_CURRENT ihcn
        : make this sodium/potassium eventually
        RANGE  ghcnbar, ehcn, mhalf,tau1,aslope,tau2,bhalf,bslope,ghcn, minf,mtau,scale,km
        :GLOBAL minf : creates a shared lookup table
}
 
INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}
 
PARAMETER {
        v (mV)
        dt (ms)
        celsius =  35.0      (degC)
        gcahvabar =  0.0e-6 (S/cm2)
        ghcnbar =  11.196e-6  (S/cm2)
        km = -5.0 (mV)
        mhalf = -75.0 (mV) : 
        aslope = 10.2
        bhalf = -10
        bslope = -100
        tau1 = 2.0e-8
        tau2 = 7.6e-3
        :vtau = -80.0 (mV)
        :stau = 11.06 (mV)
        ehcn = -35 (mV)
        scale = 1.0
}
 
STATE {
        m
}
 
ASSIGNED {
        ihcn (mA/cm2)
        ghcn (S/cm2)
        minf
        mtau
        alpha
        beta
 }
 
BREAKPOINT {
        SOLVE states METHOD cnexp
        ghcn = ghcnbar*m
        ihcn = ghcn*(v-ehcn)
}
 
UNITSOFF
 
INITIAL {
      rates(v)
      :mtau = gaussian(v,tau1,tau2,vtau,stau)
      mtau = scale/(alpha+beta)
      minf = boltz(v,mhalf,km)
      m= minf
}

DERIVATIVE states {  :Computes state variables m
:LOCAL minf, mtau
   rates(v) : calculate alpha, beta
   minf = boltz(v,mhalf,km)
   :mtau = gaussian(v,tau1,tau2,vtau,stau)
   mtau = scale/(alpha+beta)
   m' = (minf-m)/mtau
   
}

PROCEDURE rates(vx) {
	alpha = tau1*exp(-vx/aslope)
	beta = tau2*boltz(vx,bhalf,-bslope)
}
 
 
FUNCTION gaussian(v,a,b,c,d) {
        LOCAL arg
        arg= b*exp(-0.5*(v-c)*(v-c)/(d*d)) +a
        gaussian = arg
}
 
 
FUNCTION boltz(x,y,z) {
               LOCAL arg
                arg= -(x-y)/z
                if (arg > 50) {boltz = 0}
                else {if (arg < -50) {boltz = 1}
                else {boltz = 1.0/(1.0 + exp(arg))}}
}

 
UNITSON

