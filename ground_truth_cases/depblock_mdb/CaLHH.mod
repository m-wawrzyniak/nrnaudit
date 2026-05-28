TITLE calcium channel (L type) 
 
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
        SUFFIX calhh
        NONSPECIFIC_CURRENT incal
        USEION ca READ cai WRITE ica
        RANGE  gcalbar,ica,ical,incal, mhalf, mslope,skcoup, pf
}
 
INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}
 
PARAMETER {
        v (mV)
        dt (ms)
        cai   (mM)
        celsius =  35.0      (degC)
        gcalbar =  11.196e-6  (S/cm2)
        km = 0.0001   (mM)
        kml = 0.00045  (mM)
        eca = 120 (mV)
        cao = 2.0 (mM)
        skcoup = 1.0
        mhalf = -30.0
        mslope = 8.0
        pf = 0.6
        
}
 
STATE {
        dl hl
}
 
ASSIGNED {
        ica (mA/cm2)
        ical (mA/cm2)
        incal (mA/cm2)
        gcal (S/cm2)
        dlinf
        hlinf 
 }
 
BREAKPOINT {
        SOLVE states METHOD cnexp
        gcal = dl*(1.0 - pf + pf*hl)
        ical = gcalbar*gcal*(v-eca)
        incal = (1-skcoup)*ical
        ica  = (skcoup)*ical
}
 
UNITSOFF
 
INITIAL {
        dl = boltz(v,mhalf,5.0)
        hl = boltz(v,-55,-2.0)
}

DERIVATIVE states {  :Computes state variables m, h, and n 
LOCAL dlinf,dhvainf,fhvainf,dltau,dhvatau,fhvatau,hltau,hlinf
        :dlinf = boltz(v,-39.0,5.0) : sharper dlinf needed for SOPs
        dlinf = boltz(v,mhalf,mslope)
        hlinf = boltz(v,-55,-2)
        dltau = gaussian(v,9.0,25.0,70.0,0.30)
        hltau = 100.0 + 100.0*boltz(v,-30,-5.0)
        :dltau = 5.0 + 50.0 * boltz(v,-40.0, -5.0)
        :dltau = gaussian(v,25.0,10.0,50.0,5.00)
        :dltau = 1.0
        dl'  = (dlinf-dl)/dltau
        hl' = (hlinf-hl)/hltau
}
 
 
FUNCTION gaussian(v,a,b,c,d) {
        LOCAL arg
        arg= a*exp(-(c+v)*(v+c)/(b*b)) +d
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

