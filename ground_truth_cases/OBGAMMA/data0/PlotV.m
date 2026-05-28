
%========================================================================
% Written by Guosh Li (guoshi_li@med.unc.edu) 
% Plot cell membrane potentials of MCs, PGCs and GCs
% Simulation time needs to be 3000 ms (3 sec) for the m-file to run properly
%========================================================================

clc;
clear all;
close all;

DT = 0.2;        % sampling time: ms
T1 = 1000;
T2 = 3000;
n1 = T1/DT+2;
n2 = T2/DT;

nmitx = 5;
nmity = 5;
npgx  = 5;
npgy  = 5;
ngranx = 10;
ngrany = 10;

    
load tt;
t  = tt(n1:n2);

for i = 0:1:4
    
   s = ['load Vmc22' '_' int2str(i) ';'];    
   eval(s);
        
end


for i = 0:1:(nmitx-1)
   for j = 0:1:(nmity-1) 
     s = ['load Vms' '_' int2str(i) '_' int2str(j) ';'];    
     eval(s);
     
     s = ['U=Vms' '_' int2str(i) '_' int2str(j) ';'];
     eval(s);
     
     U = U(n1:n2);
     s = ['ms' '_' int2str(i) '_' int2str(j) '=U'  ';'];
     eval(s);  
   
   end
end

for i = 0:1:(npgx-1)
   for j = 0:1:(npgy-1) 
    
    s = ['load Vpb' '_' int2str(i) '_' int2str(j) ';'];    
    eval(s);    
    s = ['U=Vpb' '_' int2str(i) '_' int2str(j) ';'];
    eval(s);
    U = U(n1:n2);
    s = ['pb' '_' int2str(i) '_' int2str(j) '=U'  ';'];
    eval(s);    
    
   end
end

for i = 0:1:(ngranx-1)
   for j = 0:1:(ngrany-1) 
    
    s = ['load Vgb' '_' int2str(i) '_' int2str(j) ';'];    
    eval(s);    
    s = ['U=Vgb' '_' int2str(i) '_' int2str(j) ';'];
    eval(s);
    U = U(n1:n2);
    s = ['gb' '_' int2str(i) '_' int2str(j) '=U'  ';'];
    eval(s); 

   end
end


L = length(ms_0_0);



%=====================================================
%           Plot Voltage for Each Cell Type
%=====================================================

XT1 = 2000;
XT2 = 3000;

% For MC
figure;
subplot(2,1,1);
plot(t,ms_0_1,'b', t, ms_4_1,'r','LineWidth',2);
axis([XT1,XT2,-80,40]);
title('MC', 'FontSize',14);
ylabel('mV', 'FontSize',14);
box('off');
legend('MC[0][1]','MC[4][1]');

subplot(2,1,2);
plot(t,ms_3_4,'b',t,ms_2_4,'r', 'LineWidth', 2);
axis([XT1,XT2,-80,40]);
xlabel('ms', 'FontSize',14);
ylabel('mV', 'FontSize',14);
box('off');
legend('MC[3][4]', 'MC[2][4]'); 


figure;
subplot(2,1,1);
plot(t,ms_3_2,'b', t, ms_4_3,'r','LineWidth',2);
axis([XT1,XT2,-80,40]);
ylabel('mV', 'FontSize',14);
title('MC', 'FontSize',14);
box('off');
legend('MC[3][2]','MC[4][3]');

subplot(2,1,2);
plot(t,ms_1_1,'b',t,ms_1_4,'r', 'LineWidth', 2);
axis([XT1,XT2,-80,40]);
xlabel('ms', 'FontSize',14);
ylabel('mV', 'FontSize',14);
box('off');
legend('MC[1][1]', 'MC[1][4]'); 


% % =============================================
% % For GC
figure;
subplot(2,1,1);
plot(t,gb_0_1,'b', t,gb_3_2,'r','LineWidth',2);
axis([XT1,XT2,-80,40]);
ylabel('mV', 'FontSize',14);
set(gca, 'FontSize',12);
title('GC', 'FontSize',14);
legend('GC[0][1]', 'GC[3][2]'); 
box('off');

subplot(2,1,2);
plot(t,gb_2_2,'b', t,gb_6_1,'r','LineWidth',2);
ylabel('mV', 'FontSize',14);
xlabel('ms', 'FontSize',14);
axis([XT1,XT2,-80,40]);
set(gca, 'FontSize',12);
legend('GC[2][2]', 'GC[6][1]'); 
box('off');



% % ===============================================
% For PG
figure;
subplot(2,1,1);
plot(t,pb_0_1,'b', t,pb_4_1,'r', 'LineWidth',2);
axis([XT1,XT2,-80,40]);
set(gca, 'FontSize',12);
ylabel('mV', 'FontSize',14);
title('PGC', 'FontSize',14);
legend('PG[0][1]', 'PG[4][1]'); 
box('off');

subplot(2,1,2);
plot(t,pb_3_4,'b', t,pb_2_4,'r', 'LineWidth',2);
axis([XT1,XT2,-80,40]);
set(gca, 'FontSize',12);
xlabel('ms', 'FontSize',14);
legend('PG[3][4]', 'PG[2][4]'); 
box('off');



%===========================================

for i = 0:1:(nmitx-1)
   for j = 0:1:(nmity-1) 
     s = ['clear Vms' '_' int2str(i) '_' int2str(j) ';'];    
     eval(s);       
    end
end

for i = 0:1:(npgx-1)
   for j = 0:1:(npgy-1) 
     s = ['clear Vpb' '_' int2str(i) '_' int2str(j) ';'];    
     eval(s);
    end
end


for i = 0:1:(ngranx-1)
   for j = 0:1:(ngrany-1) 
 
     s = ['clear Vgb' '_' int2str(i) '_' int2str(j) ';'];    
     eval(s);     
      
    end
end


clear U
