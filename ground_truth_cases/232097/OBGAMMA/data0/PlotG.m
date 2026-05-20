
%==========================================================================
% Written by Guosh Li (guoshi_li@med.unc.edu) 
% Plot PG-->MC and GC-->MC GABAA conductance in the OB network
% Simulation time needs to be 3000 ms (3 sec) for the m-file to run properly
%==========================================================================

clc;
clear all;
close all;

DT = 0.2;    % sampling time: ms
T1 = 1000;
T2 = 3000;
n1 = T1/DT+2;
n2 = T2/DT;


nmitx = 5;
nmity = 5;

nMit = 25;
nPG  = 25;
nGC  = 100;

load tt;
t  = tt(n1:n2);
t = (t-2000);

% Load PG-->MC conductances
for i = 0:1:nmitx-1
    for j = 0:1:nmity-1
     s = ['load Gpm' int2str(i) int2str(j) ';'];    
     eval(s);
     s = ['U=Gpm' int2str(i) int2str(j) ';'];
     eval(s);
     U = U(n1:n2);
     s = ['Gpm' int2str(i) int2str(j) '=U*1e3'  ';'];
     eval(s);

    end
end


% Load GC-->MC conductances

  for i = 0:1:(nMit-1) 
     s = ['load Ggm' int2str(i) ';'];    
     eval(s);
     s = ['U=Ggm' int2str(i) ';'];
     eval(s);
     U = U(n1:n2);
     s = ['Ggm' int2str(i) '=U*1e3'  ';'];
     eval(s);
  end


%================================================
%               For PG-->MC 
%================================================

    figure;
    subplot(3,1,1);
    plot(t,Gpm00,'b-');
    title('G_P_G_-_-_>_M_C', 'FontSize',14);
    set(gca, 'XTickLabel',[ ]);
    set(gca, 'FontSize',12);
    box('off');

    subplot(3,1,2);
    plot(t,Gpm23,'b');
    set(gca, 'XTickLabel',[ ]);
    set(gca, 'FontSize',12);
    ylabel('nS', 'FontSize',14);
    box('off');

    subplot(3,1,3);
    plot(t,Gpm34,'b');
    set(gca, 'FontSize',12);
    xlabel('ms', 'FontSize',14);
    box('off');


%=====================================
%           For GC-->MC 
%=====================================

    xmax = 1001;
    ymax = 80;
%     
%     figure;
%     subplot(3,1,1);
%     plot(t,Ggm0,'b','LineWidth',2);
%     set(gca, 'XTickLabel',[ ]);
%     set(gca, 'FontSize',12);
%     axis([-0.2,xmax,0,ymax]);
%     % set(gca, 'YTick',[0:15:30]);
%     title('G_G_C_-_>_M_C', 'FontSize',14);
% %     legend('MC1');
%     box('off');
% 
%     subplot(3,1,2);
%     plot(t,Ggm14,'b','LineWidth',2);
%     set(gca, 'XTickLabel',[ ]);
%     set(gca, 'FontSize',12);
%     axis([-0.2,xmax,0,ymax]);
%     % set(gca, 'YTick',[0:15:30]);
%     ylabel('nS', 'FontSize',14);
% %     legend('MC13');
%     box('off');
% 
%     subplot(3,1,3);
%     plot(t,Ggm20,'b','LineWidth',2);
%     set(gca, 'FontSize',12);
%     xlabel('Sec', 'FontSize',14);
%     axis([-0.2, xmax, 0, ymax]);
%     % set(gca, 'YTick',[0:15:30]);
% %        legend('MC24');
%     box('off');
    
    
    
    figure;
    plot(t,Ggm0,'b', t,Ggm14, 'r', t,Ggm20,'k','LineWidth',2);
    set(gca, 'FontSize',12);
    axis([-200,800,0,ymax]);
    xlabel('ms', 'FontSize',14);
    ylabel('nS', 'FontSize',14);
    title('G_G_C_-_-_>_M_C', 'FontSize',14);
    box('off');

    
    
    
    
    
    
    







