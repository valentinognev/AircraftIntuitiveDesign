function Lat_Dir_Corrections(M)
global AERO ATM AC BD WG VT

%Vertical Tail
Av = VT.AR(end);
TRv = VT.TR(end);
bv_2r1 = BD.R(end-1)+BD.R(end);
St_Sv = VT.S(end)/WG.S(end);
Zh_bv = VT.Z-(sum(BD.ZU(end-1:end))/2+sum(BD.ZL(end-1:end))/2)/2;
Xact_cv = 0.25;

%Wing
W_A = WG.AR(end);
W_b = WG.b;     
W_TR  = WG.TR(end);
W_SweepC2 = WG.swp(3,end);
lf = WG.Xtip+WG.CHRDTP/2-BD.X(1);

%%%%%%%%%%%%%%%%%%%%%%%%% VT Effective AR %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%from Glenn Greiner (AE Professor at ERAU Daytona Beach)
%
%function [Aeff] = Lat_Aeff(Av,TRv,bv_2r1,St_Sv,Zh_bv,Xact_cv)
% Aeff - Vertical panel effective aspect ratio - FIGURE 5.3.1.1-22ABC
%[Aeff] = Lat_Aveff(Av,TRv,bv_2r1,St_Sv,Zh_bv,Xact_cv)
%Input(s):
%Av     = Vertical panel geometric aspect ratio
%TRv    = Vertical Panel taper ratio
%bv_2r1 = Vertical panel span/(2*avg fuselage radius) 
%         Digital Datcom avg fuselage radius = bv - bve
%St_Sv  = Horiz tail area / vertical panel area
%Zh_bv  = Horiz tail location above vertical panel chord
%         root / vertical panel span
%Xact_cv = Horiz tail aerodynamic center projected onto the 
%         vertical panel chord that the horiz tail is attached
%Output(s)
%Aeff is a structured array
%Aeff.Av      = Av;
%Aeff.TRv     = TRv;
%Aeff.bv_2r1  = bv_2r1;
%Aeff.St_Sv   = St_Sv;
%Aeff.Zh_bv   = Zh_bv;
%Aeff.Xact_cv = Xact_cv;
%Aeff.Avb_Av   Fig 5.3.1.1-22A
%Aeff.Avhb_Avb Fig 5.3.1.1-22B
%Aeff.KH       Fig 5.3.1.1-22C
%Aeff.Kv       Fig 5.3.1.1-22D
%Aeff.Aeff     Vertical panel effective aspect ratio
%              Aeff = Av*Aeff.Avb_Av*(1 + KH*(Avhb_Avb - 1))

% Calculate the Effective Aspect Ratio
Aeff.Av      = Av;
Aeff.TRv     = TRv;
Aeff.bv_2r1  = bv_2r1;
Aeff.St_Sv   = St_Sv;
Aeff.Zh_bv   = Zh_bv;
Aeff.Xact_cv = Xact_cv;

%AVB/AV FIGURE 5.3.1.1-22A
%bv/2r1
F22AX = [0 .125 .25 .5 .75 1. 1.25 1.5 1.75 2. 2.25 ...
         2.50 3.00 3.25 3.50 3.75 4.00 5.00 7.00];
%TRv
F22AX2 = [1.0 0.6];
%Taper ratio = 1.0
F22AY = {[0 .40 .720 .990 1.19 1.32 1.40 1.46 1.50 1.5 ... 
          1.4 1.42 1.27 1.21 1.17 1.13 1.10 1.04 1.02]
%Taper ratio <= 0.6
	     [0 .70 .940 1.18 1.35 1.46 1.54 1.60 1.63 1.64 ... 
          1.60 1.53 1.36 1.28 1.21 1.16 1.13 1.06 1.02]};
%Determine Avh/Av for bv/2r1 <=0.6 or interpolate 0.6< bv/2r1 <= 1
nm = numel(F22AY);
Avb_Av = zeros(size(nm));
if TRv <= 0.6
    Aeff.Avb_Av = interp1(F22AX,F22AY{2},bv_2r1,'spline');
end
if TRv > 0.6 && TRv <= 1.0
   for j=1:nm
      Avb_Av(j) = interp1(F22AX,F22AY{j},bv_2r1,'spline');
   end
      Aeff.Avb_Av = interp1(F22AX2,Avb_Av,TRv,'linear');
end


%AVHB/AVb FIGURE 5.3.1.1-22B
%Zh/bv (+ for ZHT above ZV, 0 if ZHT is below ZV
if Zh_bv < 0; Zh_bv = 0; end
F22BX = [0.0 0.2 0.3 0.4 0.5 0.6 0.65 0.7 0.75 0.8 0.85 0.9 1.];
%Xact/cv
F22BX2 = [.5 .6 .7 .8];
%AVHB/AVB
F22BY = {[1.05 0.94 0.90 0.87 0.86 0.87 0.90 0.93 0.98 1.06 1.16 1.29 1.70]
         [1.15 1.00 0.95 0.90 0.89 0.90 0.92 0.96 1.01 1.08 1.18 1.31 1.70]
         [1.22 1.05 0.99 0.94 0.92 0.92 0.95 0.98 1.03 1.10 1.20 1.33 1.70]
         [1.29 1.09 1.02 0.97 0.94 0.94 0.96 1.00 1.06 1.12 1.22 1.36 1.70]};

%Determine Avhb/Avb for x/cv <=0.5 or interpolate 0.5< x/cv <= 1
nm = numel(F22BY);
Avhb_Avb = zeros(size(nm));
if Xact_cv <=0.5
   Aeff.Avhb_Avb = interp1(F22BX,F22BY{1},Zh_bv,'spline');
end
if Xact_cv > 0.5 && Xact_cv <= 1.0
   for j=1:nm
      Avhb_Avb(j) = interp1(F22BX,F22BY{j},Zh_bv,'spline');
   end
      Aeff.Avhb_Avb = interp1(F22BX2,Avhb_Avb,Xact_cv,'linear');
end


%KH FIGURE 5.3.1.1-22C
F5322X = [0.,.2, .4, .6, .7, .8, .9,1.2, 1.4, 1.6, 2.0 ];
F5322Y = [0.,.29,.52,.70,.77,.83,.87,.98,1.04,1.07,1.13];
Aeff.KH =  interp1(F5322X,F5322Y,St_Sv,'pchip');

%Kv Figure 5.3.1.1-22D
if bv_2r1 <= 2; Aeff.Kv = 0.75; end
if bv_2r1 > 2 && bv_2r1 < 3.5; Aeff.Kv = 0.75 + 0.1667*(bv_2r1 - 2); end
if bv_2r1 >= 3.5; Aeff.Kv = 1.0; end

%Determine the effective Aspect ratio
if VT.TR(end)>1, Aeff.Avb_Av = 1; end
Aeff.Aeff = Av*Aeff.Avb_Av*(1 + Aeff.KH*(Aeff.Avhb_Avb - 1));
VT.AReff = Aeff.Aeff;

%% %%%%%%%%%%%%%%%%%%%%%%% ClB Sweep %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%%%% ClB_CL Sweep %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%from Glenn Greiner (AE Professor at ERAU Daytona Beach)
%
%function CLB_CL_W_Sweep = Lat_CLB_W_Sweep(W_A,W_tr,W_SweepC2)
%CLB_W_Sweep - Wing Sweep Contribution to CLB - FIGURE 5.1.2.1-27
%CLB_W_Sweep = Lat_CLB_W_Sweep(W_A,W_Taper,W_SweepC2)
%Input(s)
%W_A         = Wing aspect ratio
%W_TR        = Wing taper ratio
%W_SweepC2   = wing sweep @ 50%c

%taper ratio
F5121X3 = [1 0.5 0];
%aspect ratio
F5121X2 = [1.0 2.0 4.0 6.0 8.0];
%Half chord sweep
F5121X = [-20 0 20 30 40 50 55 60];
%CLB/CLsweep C2 per taper ratio starting at 0
F5121Y= {{[.0014 0.0 -.00125 -.002  -.0027 -.0036 -.004  -.0044]
          [.0015 0.0 -.00145 -.0022 -.003  -.0041 -.005  -.00595]  
          [.0016 0.0 -.0016  -.0024 -.0033 -.0047 -.0057 -.0071]  
          [.0016 0.0 -.0016  -.0024 -.0035 -.0049 -.006  -.0074]
          [.0016 0.0 -.0016  -.0027 -.0035 -.0049 -.006  -.0074]}

         {[.0012  0.0 -.0012  -.0019 -.0026 -.0034 -.0039  -.0044]
          [.0013  0.0 -.0013  -.0021 -.003  -.0043 -.00515 -.0064]  
          [.0015  0.0 -.0014  -.0024 -.0036 -.005  -.00605 -.0075]
          [.00165 0.0 -.0016  -.0025 -.0038 -.0054 -.0066  -.0082]  
          [.0018  0.0 -.00175 -.0027 -.004  -.0058 -.007   -.0089]}

         {[.00105 0.0 -.001   -.0016  -.0023 -.003   -.0035  -.0038]
          [.0012  0.0 -.0013  -.0021  -.0031 -.00435 -.00505 -.0062]  
          [.0014  0.0 -.00165 -.00245 -.0036 -.0052  -.0061  -.0078]   
          [.00167 0.0 -.0017  -.0028  -.004  -.00595 -.00715 -.009] 
          [.0018  0.0 -.0018  -.00295 -.0042 -.0062  -.0078  -.010]}};

%interpolate/extrapolate
nmY = length(F5121X3);
nmX2 = length(F5121X2);
CLBCL1 = cell(size(nmY));
CLBCL2 = zeros(size(nmX2));
   
for i=1:nmY
    for j=1:nmX2
        %interpolate by sweep for each graph under each aspect ratio
        %and taper ratio
        CLBCL1{i}(j) = interp1(F5121X,F5121Y{i}{j},W_SweepC2,...
                       'spline','extrap');
    end
    %interpolate by aspect ratio for each graph under taper ratio
    CLBCL2(i) = interp1(F5121X2,CLBCL1{i},W_A,'linear','extrap');
end

%interpolate by taper ratio
ClB_CL_W_Sweep = interp1(F5121X3,CLBCL2,W_TR,'spline');
clear i j

%%%%%%%%%%%%%%%%%%%%%%%% ClB Mach Sweep %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%from Glenn Greiner (AE Professor at ERAU Daytona Beach)
%
%function ClB_KM_Sweep = Lat_ClB_W_KM_Sweep(W_A,W_SweepC2,M)
%Lat_KM_SWEEP  FIGURE 5.1.2.1-28-A  
%KM_Sweep = Lat_KM_Sweep(W_A,W_SweepC2,M)
%Input
%W_A       = Wing aspect ratio
%W_SweepC2 = wing sweep @ 50%c
%M         = Mach Number

%Output
%CLB_W_SWEEP = Ratio of CLB/CL accounting for wing sweep effects

%A/Cos(SweepC2)
F128AX2 = [ 2. 3. 4. 5. 6. 8. 10.];
%MCOS(SweepC2)
F228AX =[ 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 0.95];
%KMSweep
F28AY = {[ones(1,8) 0.995 0.990]
         [ones(1,6) 1.01 1.03 1.03 1.02]
         [1   1    1.01  1.015 1.025 1.05 1.08  1.09 1.10 1.10]
         [1.0 1.01 1.015 1.02  1.05  1.09 1.115 1.16 1.20 1.21]
         [1.0 1.01 1.02  1.04  1.07  1.12 1.17  1.24 1.32 1.36]
         [1.0 1.01 1.05  1.07  1.12  1.18 1.27  1.40 1.58 1.70]
         [1.0 1.02 1.05  1.10  1.15  1.23 1.37  1.54 1.84 2.08]};

%interpolate/extrapolate
MCOS = M*cosd(W_SweepC2);
A_COS = W_A/cosd(W_SweepC2);
nmY = length(F128AX2);
KML1 = zeros(size(nmY));
    
for i = 1:nmY
    KML1(i) = interp1(F228AX,F28AY{i},MCOS,'spline','extrap');
end

ClB_KM_Sweep = interp1(F128AX2,KML1,A_COS,'linear','extrap');

%end

%%%%%%%%%%%%%%%%%%%%%%%% ClB Fuselage Sweep %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%from Glenn Greiner (AE Professor at ERAU Daytona Beach)
%
%function ClB_Kf = Lat_ClB_B_Kf_Sweep(W_A,W_SweepC2,lf,W_b)
%Kf - Fuselage correction factor - FIGURE 5.2.2.1-26
%Kf = Lat_CLB_Kf(W_A,W_b,W_SweepC2,W_Xc2tip)
%Input(s)
%W_A       = Wing aspect ratio
%W_b       = Wing span
%W_SweepC2 = wing sweep @ 50%c
%lf        = Distance from nose to wing tip 50% chord

%Aspect Ratio
F5221X2 =[4.0 4.5 5.0 5.5 6.0 7.0 8.0];
%lf/bw   
F5221X = [0.0 .2 .4 .6 .8 1.0 1.2 1.4 1.6];
%Kf   
F5221Y = {[1.0 1.00 1.00 1.00 1.00 1.00 1.00 .990 .970]
          [1.0 1.00 1.00 1.00 1.00 1.00 .980 .948 .911]
          [1.0 1.00 1.00 1.00 .997 .971 .933 .883 .827]
          [1.0 1.00 1.00 .991 .963 .922 .870 .811 .746]
          [1.0 1.00 .995 .970 .932 .884 .829 .764 .695]
          [1.0 1.00 .977 .944 .899 .845 .780 .715 .641]
          [1.0 .985 .960 .921 .870 .812 .745 .670 .592]}; 

%interpolate/extrapolate
lf_bw = lf/W_b;
ACOS = W_A/cosd(W_SweepC2);

nm = numel(F5221Y);
Kf1 = zeros(size(nm));
for j = 1:nm
    Kf1(j) = interp1(F5221X,F5221Y{j},lf_bw,'spline','extrap');
end
ClB_Kf = interp1(F5221X2,Kf1,ACOS,'spline','extrap');

%%%%%%%%%%%%%%%%%%%%%%%% ClB Sweep Combined %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

ClB_sweep = AC.CL*ClB_CL_W_Sweep*ClB_KM_Sweep*ClB_Kf;

%% %%%%%%%%%%%%%%%%%%%%%% ClB Aspect Ratio %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%from Glenn Greiner (AE Professor at ERAU Daytona Beach)
%
%function ClB_CL_W_A = Lat_ClB_W_A(W_A,W_tr)
%CLB_CL_A - Aspect ratio contribution to wing CLB - FIGURE 5.1.2.1-28-B  
%CLB_CL_A = Lat_CLB_CL_A(W_A,W_tr)
%Input(s)
%W_A      = Wing aspect ratio
%W_tr     = wing taper ratio

%Wing taper ratio
F5151X2 = [0 0.5 1];
%Wing aspect ratio
F5151X = [1.0 1.5 2.0 2.5 3.0 4.0 5.0 6.0 8.0]; 
%CLB_CL_A
F5151Y ={[-.00580 -.00345 -.00235 -.00145 -.00100 ...
          -.00045 -.00025  .00005  .00040];
         [-.00800 -.00555 -.00400 -.00300 -.00235 ...
          -.00140 -.00100 -.00065 -.00020];
         [-.01130 -.00800 -.00595 -.00465 -.00370 ...
          -.00255 -.00182 -.00147 -.00097]};

%interpolate/extrapolate
nmX2 = length(F5151X2);
CLBCLA1 = zeros(size(nmX2));

if W_A > 8
    for i = 1:nmX2
        CLBCLA1(i) = interp1(F5151X,F5151Y{i},W_A,'linear','extrap');
    end
    ClB_CL_W_A = interp1(F5151X2,CLBCLA1,W_TR,'linear')/6;
else
    for i = 1:nmX2
        CLBCLA1(i) = interp1(F5151X,F5151Y{i},W_A,'spline');
    end
    ClB_CL_W_A = interp1(F5151X2,CLBCLA1,W_TR,'linear');
end

ClB_AR = AC.CL*ClB_CL_W_A;

%% %%%%%%%%%%%%%%%%%%%%%%% ClB Twist %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%from Glenn Greiner (AE Professor at ERAU Daytona Beach)
%
%function ClB_TS = Lat_ClB_W_TS(W_A,W_TR)
%Lat_ClB_W_TS - Wing Twist Correction Factor - FIGURE 5.1.2.1-30b  
%ClB_TS = Lat_ClB_T(W_A,W_TR)
%Input
%W_A  = Wing Aspect ratio
%W_TR = Wing Taper ratio
%Output
%ClB_TS = Ratio of dClB/(Twist*tan(Sweep_25%C))


X2 = [0.0,0.4,0.6,1.0];
X1 = [3.,4.,5.,6.,7.,8.,9.,10.,11.];
Y  = {[-.0000192,-.0000222,-.0000238,-.0000231,-.0000230, ...
       -.0000241,-.0000260,-.0000284,-.0000328]
      [-.0000220,-.0000287,-.0000323,-.0000335,-.0000339, ...
       -.0000342,-.0000350,-.0000370,-.0000420]
      [-.0000233,-.0000300,-.0000335,-.0000350,-.0000366, ...
       -.0000370,-.0000375,-.0000400,-.0000470] 
      [-.0000233,-.0000300,-.0000335,-.0000350,-.0000366, ...
       -.0000370,-.0000375,-.0000400,-.0000470]};

nm = length(X2);
Y1 = zeros(size(nm));
    
for i = 1:nm
    Y1(i) = interp1(X1,Y{i},W_A,'spline','extrap');
end
ClB_TS = interp1(X2,Y1,W_TR,'linear','extrap');

ClB_twist = -WG.TWISTA*tand(WG.swp(2,end))*ClB_TS;

%% %%%%%%%%%%%%%%%%%%%%%%% ClB Dihedral %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%%%%% ClB Dihedral %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%from Glenn Greiner (AE Professor at ERAU Daytona Beach)
%
%function ClB_W_GU = Lat_ClB_W_GU(W_A,W_tr,W_SweepC2)
%ClB_G - Uniform Geometric Dihedral on wing CLB - FIGURE 5.1.2.1-29
%ClB_G = Lat_CLB_G(W_A,W_tr,W_SweepC2)
%Input(s)
%W_A         = Wing aspect ratio
%W_tr        = Wing taper ratio
%W_SweepC2   = wing sweep @ 50%c

%taper ratio
F5129X3 = [0.0 0.5 1.0];
%half chord sweep
F5129X2 = [0.0 40.0 60.0];
%aspect Ratio
F5129X  = [0.0 1.0 2.0 3.0 4.0 5.0 6.0 8.0 10.];
%CLB/Dihedral per Sweep C2 per taper ratio starting at 0
F5129Y = {{[0.0 -.000052 -.000088 -.000110 -.000134 -.000153...
                -.000168 -.000190 -.000200]
           [0.0 -.000048 -.000085 -.000108 -.000128 -.000141 ...
                -.000153 -.000173 -.000178]  
           [0.0 -.000040 -.000073 -.000095 -.000108 -.000119 ...
                -.000127 -.000135 -.000138]}

          {[0.0 -.000052 -.000098 -.000132 -.000162 -.000186...
                -.000208 -.000240 -.000260]  
           [0.0 -.000050 -.000096 -.000124 -.000105 -.000107...
                -.000188 -.000217 -.000230]
           [0.0 -.000050 -.000087 -.000111 -.000129 -.000142...
                -.000153 -.000166 -.000170]}

          {[0.0 -.000050 -.000096 -.000133 -.000167 -.000193...
                -.000216 -.000252 -.000280] 
           [0.0 -.000050 -.000095 -.000129 -.000155 -.000178...
                -.000197 -.000225 -.000245]
           [0.0 -.000050 -.000088 -.000113 -.000132 -.000147...
                -.000159 -.000172 -.000180]}};

 %interpolate/extrapolate
 nmY = numel(F5129Y);
 nmX2 = length(F5129X2);
 CLBG2 = cell(size(nmY));
 CLBG1 = zeros(size(nmX2));
 
 for i=1:nmY
    for j = 1:nmX2
       %interpolate on all graphs based on Aspect Ratio
       CLBG2{i}(j) = interp1(F5129X, F5129Y{i}{j},W_A,'spline','extrap');
    end
    %interpolate based on half chord sweep
    CLBG1(i) = interp1(F5129X2, CLBG2{i},W_SweepC2,'spline','extrap');
 end
 
%inerpolate based on taper ratio
ClB_W_GU = interp1(F5129X3,CLBG1,W_TR,'spline');

%%%%%%%%%%%%%%%%%%%%%%% ClB Mach Dihedral %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%from Glenn Greiner (AE Professor at ERAU Daytona Beach)
%
%function KMG = Lat_ClB_W_KM_G(W_A,W_SweepC2,M)
%KMG Compressibility Correction to dihedral effet on wing
%KMG FIGURE 5.2.2.1-30A
%KMG = Lat_KMG(W_A,W_SweepC2,M))
%Input(s)
%W_A       = Wing aspect ratio
%W_SweepC2 = wing sweep @ 50%c
%M         = Mach Number

%A/Cos(SweepC2)
F5130X2 = [2. 4. 6. 8. 10.];
%M*cos(SweepC2)
F5130X = [0.0 .2 .4 .5 .6 .7 .8 .9 .95];
%KMG
F5130Y = {[1.0 1.01 1.018 1.02 1.023 1.03 1.04 1.05 1.057]
          [1.0 1.012 1.03 1.045 1.06 1.085 1.118 1.16 1.19]
          [1.0 1.015 1.045 1.07 1.1 1.14 1.197 1.27 1.33]
          [1.0 1.018 1.05 1.085 1.125 1.19 1.26 1.39 1.485]
          [1.0 1.02 1.058 1.097 1.148 1.215 1.325 1.495 1.635]};
        
%interpolate/extrapolate
MCOS = M*cosd(W_SweepC2);
A_COS = W_A/cosd(W_SweepC2);

nmY = length((F5130X2));
KMG1 = zeros(size(nmY));

for i = 1:nmY
    KMG1(i) = interp1(F5130X,F5130Y{i},MCOS,'spline','extrap');
end
KMG = interp1(F5130X2,KMG1,A_COS,'linear','extrap');

%%%%%%%%%%%%%%%%%%%%%%% ClB Dihedral Combined %%%%%%%%%%%%%%%%%%%%%%%%%%%%%

ClB_dihedral = WG.gamma*ClB_W_GU*KMG;
ClB_dihedral = ClB_dihedral-0.0005*sqrt(WG.AR(end))*(BD.d_eq/WG.b)^2;

%% %%%%%%%%%%%%%%%%%%%%%%% Calculate ClB %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

AC.Clb = ClB_sweep+ClB_AR+ClB_twist+ClB_dihedral;

%% %%%%%%%%%%%%%%%%%%%%%%%%% CNB Kn %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%from Glenn Greiner (AE Professor at ERAU Daytona Beach)
%
%function KN = Lat_CNB_Kn
%KN - Wing-Body interference factor (per degree) - FIGURE 5.2.3.1-8
%KN = Lat_CNB_Kn(XCG, Lf, SBS, h1, h2, hf_max, wf_max)
%XCG    = CG location with respect to nose
XCG     = AERO.XCG;
%Lf     = Fuselage(Body) length
Lf      = BD.X(end)-BD.X(1);
%SBS    = Fuselage(Body) side area
SBS     = trapz(BD.X,BD.ZU-BD.ZL);
%h1     = Fuselage(Body) height @ 0.25Lf
h1      = interp1(BD.X,BD.ZU-BD.ZL,0.25*Lf);
%h2     = Fuselage(Body) height @ 0.75Lf
h2      = interp1(BD.X,BD.ZU-BD.ZL,0.75*Lf);
%hf_max = Fuselage(Body) maximum height
hf_max  = max(BD.ZU-BD.ZL);
%wf_max = Fuselage(Body) maximum width
wf_max  = 2*max(BD.R);

%5.2.3.1-8A
%Lf^2/SBS
F5231X2A = [20. 14. 10. 8. 7. 6. 5. 4. 3. 2.5];
%XCG/Lf
F5231XA =  [ .20  .8];
F5231YA = {[ .10 1.88] 
           [ .40 2.21]
           [ .74 2.60]
           [ .98 2.80]
           [1.30 3.13]
           [1.61 3.50]
           [2.00 3.88]
           [2.50 4.40] 
           [2.99 5.00]
           [3.45 5.40]};

%5.2.3.1-8B
%sqrt(h1/h2)
F5231X2B = [0.8 1.0 1.2 1.4 1.6 ];
F5231XB = [0.0 3.0 6.0];
%used to find Y value
F5231YB = {[0.0 2.35 4.68]
           [0.0 3.00 6.00]
           [0.0 3.60 7.25]
           [0.0 4.18 8.50]
           [0.0 4.79 9.50]};

%5.2.3.1-8C
%h/wfmax 
F5231X2C = [0.5 0.6 0.8 1.0 2.0];
%for finding X value
F5231XC = [ 0.0 6.0 ];
%KN
F5231YC = {[-.00048 .00251] 
           [-.00048 .00350]
           [-.00048 .00477]
           [-.00048 .00559]
           [-.00048 .00641]};
                          
xm_lf = XCG/Lf;
Lf_SB = Lf^2/SBS;
h1_h2 = sqrt(h1/h2);
hf_wf = hf_max/wf_max;

%interpolate graph A (Lf^2/SBS) first
nmA = numel(F5231YA);
nmB = length(F5231X2B);
nmC = numel(F5231YC);
FIGBY1 = zeros(size(nmA));
FIGCX1 = zeros(size(nmB));
KN1 = zeros(size(nmC));
    
for j = 1:nmA
    %figure B's Y value
    FIGBY1(j) = interp1(F5231XA,F5231YA{j},xm_lf,'linear','extrap');
end 
FIGBY = interp1(F5231X2A,FIGBY1,Lf_SB,'spline','extrap');

%interpolate graph B sqrt(h1/h2) second using Y values as X
for k = 1:nmB
    %Figure C's X value
    FIGCX1(k) = interp1(F5231XB,F5231YB{k},FIGBY,'linear','extrap');
end
FIGCX = interp1(F5231X2B,FIGCX1,h1_h2,'spline','extrap');

%interpolate graph C (hf/wf) for KN last
for n = 1:nmC
    %Interpolate each line on graph C
    KN1(n) = interp1(F5231XC,F5231YC{n},FIGCX,'linear','extrap');
end

%Final value 
KN1(isnan(KN1)) = 0;
KN = interp1(F5231X2C,KN1,hf_wf,'spline','extrap');

%Additional Geometric and Empirical Constants
KRL = 0.205*log(ATM.Re*Lf)-1.833;

%Body Contribution to CNB
BD.Cnb = -KN*KRL*SBS*Lf/(WG.S(end)*WG.b);

end