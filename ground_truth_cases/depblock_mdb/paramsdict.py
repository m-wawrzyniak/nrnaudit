


CONTOG=1
ALL = 0 # 1 for Fig 4C6

p_init = dict({})

p_init['gnmda'] =0e-6 #nmda
p_init['cmg'] = 1.2 #1.2 for NMDA, 0 for AMPA
p_init['cafrac']=0

p_init['both']=1

p_init['na_shift'] = 0.0 # mshift positive decreases excitability
p_init['na_hshift'] = 0#-5.0 # hshift
p_init['na_sshift'] = 0.0

p_init['ra'] = 1.0 # 1 = 100 ohm-cm
# making the cell smaller works?


p_init['glna'] =3.0 


p_init['capump'] = 0.4# CA pump
p_init['gka'] = 0.75 # does reduced KA improve rebound? 2 
p_init['gcal'] = 0.5 # L type
#p_init[16] = -0
p_init['ais_na'] = 3 # less is more
#p_init[12] = 0
#p_init[14] = 5 #3
p_init['gcat'] = 0.0 # CaV3
#0.5
catbuff = 0.0 # 1 means CaT is not coupled to SK
taukv4 = 0.6 # 25 ms inactivation time constant
capval =1 #
ashift = -10
SCALE =1





p_init['chop'] = 1
p_init['dst'] = 300  #'distal' distance


# atypical, conventional

phi_h = 1.5 # speed scale factor for CaT
p_init['cm'] = capval
p_init['scale'] =1


p_init['ratio'] = 1 # fraction of NaV that is slow inactivating

p_init['gnahh'] =15.0*(1+CONTOG) #poorly named
p_init['nafrac'] = 0.0


p_init['taukv4'] = 0.6 - 0.5*(CONTOG+ALL)#-0.5 # 0.6 0.1
p_init['ghcn'] = 0.5*(CONTOG+ALL)#+0.3 # 0, 0.5

p_init['gkca'] =(0.2+0.8*(CONTOG+ALL))#0.4+0.6*CONTOG#+0.3 # 0.2, 1
p_init['dca'] = 0.0  #reduced mobility allows for larger calcium swings



p_init['control'] = 0
p_init['all'] = 0


p_init['nspeed'] = 2

p_init['gkhh'] =2.5+2.5*CONTOG+ALL*1.5#1.5 4
p_init['nshift']=0#-5*CONTOG #
p_init['nslope'] = 16
p_init['glk'] = p_init['glna']+1#+(1-CONTOG) # 1 = 10 uS/cm2

p_init['size'] =500*(1+1*CONTOG) # conventional size lowered a bit so that failure remains at 100 pA ramp

p_init['slow'] =(1-CONTOG)*0.67+(2.5*CONTOG)# 1 = 40 1/s 3 (120/s) matches Ding data, 2 (80 /s) matches NMDA data.
# stimulus parameter

p_init['idel'] = 2000 # 
p_init['idur'] = 4000 # width of V-ramp
p_init['basal'] = (-25e-3) # initial hyperpolarizing holding step

p_init['iamp'] = (100.0e-3)  #translates to 50, 100 pA for 300, 600 um change this and in dep_fun so that the basal is the special case

p_init['catdist'] = 50
p_init['tmhalf'] = -52
p_init['thhalf'] = -81
p_init['tphi'] = 1.5
#p_init[26] = .0
