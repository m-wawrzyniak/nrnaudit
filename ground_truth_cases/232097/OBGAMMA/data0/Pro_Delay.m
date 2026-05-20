
%==========================================================================
% Written by Guosh Li (guoshi_li@med.unc.edu) 
% Plot spike propogation delay of a representative MC (MC[2][2])
% Simulation time needs to be 3000 ms (3 sec) for the m-file to run properly
%==========================================================================

clc;
clear all;
close all;

T1 = 1000;
T2 = 3000;

DT = 0.02;        % sampling time: ms

load Tt;

for i = 0:1:4
    
    s = ['load Vmc22' '_' int2str(i) ';'];    
    eval(s);
        
end
  

n1 = T1/DT;
n2 = T2/DT;

t  = Tt(n1:n2);

V0 = Vmc22_0(n1:n2);
V1 = Vmc22_1(n1:n2);
V2 = Vmc22_2(n1:n2);
V3 = Vmc22_3(n1:n2);
V4 = Vmc22_4(n1:n2);
  


figure;
plot(t, V0, 'k', t,V1, 'b', t,V3, 'g', t,V4, 'r');
axis([1000,3000,-80,40]);
legend('Soma', 'Dend(0.16)', 'Dend(0.47)', 'Dend(1.0)');


figure;
plot(t, V0, 'k', t,V1, 'b', t,V3, 'g', t,V4, 'r');
axis([2500,3000,-80,40]);
legend('Soma', 'Dend(0.16)', 'Dend(0.47)', 'Dend(1.0)');


figure;
plot(t, V0, 'k', t,V1, 'b', t,V3, 'g', t,V4, 'r');
axis([2525,2535,-80,40]);
legend('Soma', 'Dend(0.16)', 'Dend(0.47)', 'Dend(1.0)');

figure;
plot(t, V0, 'k', t,V1, 'b', t,V3, 'g', t,V4, 'r','LineWidth', 2);
axis([2660,2670,-80,40]);
legend('Soma', 'Dend(0.16)', 'Dend(0.47)', 'Dend(1.0)');

