
%==========================================================================
% Written by Guosh Li (guoshi_li@med.unc.edu) 
% Generate spike rasterplots of the network
% Simulation time needs to be 3000 ms (3 sec) for the m-file to run properly
%==========================================================================

clc;
clear all;
close all;

load Odor;

nmitx = 5;
nmity = 5;
npgx  = 5;
npgy  = 5;
ngranx = 10;
ngrany = 10;
Nm   = nmitx*nmity;    % number of mitral cells
Ng   = ngranx*ngrany;  % number of granule cells
   
dm = 0.4;
dp = 0.4;
dg = 0.4;

T_Start = 1000;          % start time of calculation     
T_End   = 3000;          % end time of calculation  
T  = T_End - T_Start;    % Total duration in ms

min_T = T_Start;
max_T = T_End;

TP1 = 1000;     % Start of spontaneous activity
TP2 = 2000;     % End of spontaneous activity
TO1 = 2000;     % Start of odor stimulus
TO2 = 3000;     % End of odor stimulus
TP  = (TP2-TP1)/1000;
TO  = (TO2-TO1)/1000;


XT0 = -200; 
XT1 = 1000;
%============================================
%        Generate raster plot 
%============================================
% for mitral cells
figure;

for i = 0:1:(nmitx-1)
   for j = 0:1:(nmity-1) 
       
    n = i*nmity+j+1;
    s = ['load Ms' '_' int2str(i) '_' int2str(j) ';'];    
    eval(s);   
   
    ss = ['SpkT = Ms' '_' int2str(i) '_' int2str(j) ';'];    
    eval(ss);  
   
   % Spontanous rate 
    A = find (SpkT>=TP1 & SpkT<TP2); 
    FM_SP(n,1) = length(A)/TP;
    
   % Odor rate 
    A = find (SpkT>=TO1 & SpkT<TO2); 
    FM(n,1) = length(A)/TO;
   
   L = length(SpkT);
   if (L~=0)  
    for k = 1:L
     if (SpkT(k) > T_Start)
      
      x = [SpkT(k)-TO1   SpkT(k)-TO1];
      y = [n-dm          n+dm ];
   
       plot(x,y,'k','LineWidth',1);
       hold on;
     end
    end
   end
   
 end
end

xlabel('ms', 'FontSize',14);
ylabel('MC #', 'FontSize',14);
set(gca, 'FontSize',12);
axis([XT0,XT1,0,26]);
box('off');



% For granule cells
figure;
for i = 0:1:(ngranx-1)
   for j = 0:1:(ngrany-1) 
    
    n=i*ngrany+j+1;  
    
    s = ['load Gs' '_' int2str(i) '_' int2str(j) ';'];    
    eval(s);
    
    ss = ['SpkT = Gs' '_' int2str(i) '_' int2str(j) ';'];    
    eval(ss);  
   
   % Spontanous rate 
    A = find (SpkT>=TP1 & SpkT<TP2); 
    FG_SP(n,1) = length(A)/TP;
    
   % Odor rate 
    A = find (SpkT>=TO1 & SpkT<TO2); 
    FG(n,1) = length(A)/TO;
    
   L = length(SpkT);
   if (L~=0)
    for k = 1:L
     if (SpkT(k) > T_Start)
      
      x = [SpkT(k)-TO1   SpkT(k)-TO1];
      y = [n-dg          n+dg ];
   
       plot(x,y,'k','LineWidth',1);
       hold on;
     end  
    end
   end 
    
  end
end

axis([XT0,XT1, 0,101]);
box('off');
xlabel('ms', 'FontSize',14);
ylabel('GC #', 'FontSize',14);
set(gca, 'FontSize',12);


% For PG cells
figure;
for i = 0:1:(npgx-1)
   for j = 0:1:(npgy-1) 
    
    n=i*npgy+j+1;  
    
    s = ['load Ps' '_'  int2str(i) '_' int2str(j) ';'];    
    eval(s);
    
    ss = ['SpkT = Ps' '_' int2str(i) '_' int2str(j) ';'];    
    eval(ss);  
    
   % Spontanous rate 
    A = find (SpkT>=TP1 & SpkT<TP2); 
    FP_SP(n,1) = length(A)/TP;
    
   % Odor rate 
    A = find (SpkT>=TO1 & SpkT<TO2); 
    FP(n,1) = length(A)/TO;
    
   L = length(SpkT);
   if (L~=0)
    for k = 1:L
     if (SpkT(k) > T_Start)
      
      x = [SpkT(k)-TO1   SpkT(k)-TO1];
      y = [n-dp          n+dp ];
   
       plot(x,y,'k','LineWidth',1);
       hold on;
     end  
    end
   end 
    
  end
end

box('off');
xlabel('ms', 'FontSize',14);
ylabel('PG #', 'FontSize',14);
set(gca, 'FontSize',12);
axis([XT0,XT1,0,26]);


%=======================================

fM_SP = mean(FM_SP);
fP_SP = mean(FP_SP);
fG_SP = mean(FG_SP);
'_'
fM = mean(FM);
fP = mean(FP);
fG = mean(FG);

disp('The spontaneous MC firing rate is:');
fM_SP
fP_SP
fG_SP

disp('The MC firing rate during odor presentation is:');
fM
fP
fG



