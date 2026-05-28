
%=====================================================================
% Written by Guosh Li (guoshi_li@med.unc.edu) 
% This m-file can be used to load all the spiking and voltage data
% to the workspace to save into a mat file for later analysis
%=====================================================================


clc;
clear all;
close all;

nmitx = 5;
nmity = 5;
npgx  = 5;
npgy  = 5;
ngranx = 10;
ngrany = 10;

nMit = 25;
nPG  = 25;
nGC  = 100;

DT = 0.2;        % sampling time: ms
T1 = 1000;
T2 = 3000;
n1 = T1/DT+1;
n2 = T2/DT;


% Load time

load tt;
load Tt;

t  = tt(n1:n2);

% Load LFP
load Vam;        
load Vag;

% load Spike timing

for i = 0:1:(nmitx-1)
   for j = 0:1:(nmity-1)   
     s = ['load Ms' '_' int2str(i) '_' int2str(j) ';'];    
     eval(s); 
   end
end

for i = 0:1:(npgx-1)
   for j = 0:1:(npgy-1) 
     s = ['load Ps' '_' int2str(i) '_' int2str(j) ';'];    
     eval(s);
   end
end

for i = 0:1:(ngranx-1)
   for j = 0:1:(ngrany-1)
    s = ['load Gs' '_' int2str(i) '_' int2str(j) ';'];    
    eval(s); 
   end
end


for i = 0:1:(nmitx-1)
   for j = 0:1:(nmity-1)   
     s = ['load Md' '_' int2str(i) '_' int2str(j) ';'];    
     eval(s); 
   end
end

for i = 0:1:(npgx-1)
   for j = 0:1:(npgy-1) 
     s = ['load Pd' '_' int2str(i)  '_' int2str(j) ';'];    
     eval(s);
   end
end

for i = 0:1:(ngranx-1)
   for j = 0:1:(ngrany-1)
    s = ['load Gd' '_' int2str(i) '_' int2str(j) ';'];    
    eval(s); 
   end
end


% Load Voltage



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




% Load conductance
% Load PG-->MC conductances
for i = 0:1:nmitx-1
    for j = 0:1:nmity-1
     s = ['load Gpm' int2str(i) int2str(j) ';'];    
     eval(s);

    end
end

% Load GC-->MC conductances

  for i = 0:1:(nMit-1) 
     s = ['load Ggm' int2str(i) ';'];    
     eval(s);

  end




% Clean up data

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






