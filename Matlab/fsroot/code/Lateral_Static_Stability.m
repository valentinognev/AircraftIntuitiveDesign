function Lateral_Static_Stability(angl,plt)
global AERO AC BD WG HT VT

%Project VT dimensions if using V-Tail
if ~plt(4) && (HT.DHDADI || HT.DHDADO)
    VT = HT;
    if angl
        if HT.SSPNOP
            proj = (HT.SSPNOP*sind(HT.DHDADI)+...
                (HT.SSPN-HT.SSPNOP)*sind(HT.DHDADI))/HT.SSPN;
        else
            proj = sind(HT.DHDADI);
        end

    else
        if HT.SSPNOP
            proj = (HT.SSPNOP*tand(HT.DHDADI)+...
                (HT.SSPN-HT.SSPNOP)*tand(HT.DHDADI))/HT.SSPN;
        else
            proj = tand(HT.DHDADI);
        end
    end
    VT.S = HT.S*proj;
    VT.b = HT.b*proj;
end

%Vertical Tail Geometry
VT.hp = VT.Z+VT.ymac-AERO.ZCG;
VT.lp = VT.X+VT.xmac+VT.cbar(end)/4-AERO.XCG;
VT.h = VT.hp*cosd(AC.alpha)-VT.lp*sind(AC.alpha);
VT.l = VT.lp*cosd(AC.alpha)+VT.hp*sind(AC.alpha);

%Estimate Tail-Body Interference Term
d1 = interp1(BD.X,BD.ZU-BD.ZL,VT.X,'linear');
d2 = interp1(BD.X,BD.ZU-BD.ZL,VT.X,'linear','extrap');
d = (d1+d2)/2;  %mean fuselage diameter under VT
if VT.b/d < 2
    VT.k = 0.75;
elseif VT.b/d < 3.5
    VT.k = 0.75 + (VT.b/2-2)/6;
else
    VT.k = 1;
end

%Vertical Tail-Body Interference (Figure 5.3.1.1-22)
Avb=[0,1.18,1.45,1.6,1.62,1.5,1.36,1.2,1.15,1.1,1.08,1.06,1.05,1.05,1.05];
bv_h=0:0.5:7;
Avb_Av=interp1(bv_h,Avb,VT.b/d,'spline','extrap');

%Estimate Wing-Body Contribution to CYb
if ~isfield(BD,'dk'), BD.dk=1; end
Z_BD = mean((BD.ZU+BD.ZL)/2); %fuselage ref line
Z_WG = WG.Z-Z_BD;
if Z_WG>0   %high wing
    Kwb = 1.85*Z_WG/max(BD.ZU-Z_BD);
else        %low wing
    Kwb = -1.5*Z_WG/max(Z_BD-BD.ZL);
end
x1 = BD.X(find(BD.R==max(BD.R),1,'last'));  %where flow becomes viscous
x0_pos = interp1(BD.X,1:BD.NX,0.378*BD.X(end)+0.527*x1,'nearest');
S0 = BD.S(x0_pos);
CYB_wb = 2*pi/180*Kwb*BD.dk*S0/WG.S(end)-0.0001*WG.gamma;

%Horizontal-Vertical Tail Interference (Figure 5.3.1.1-22)
Avhb = [1.2,1.1,1,0.95,0.91,0.9,0.92,0.98,1.09,1.35,1.7];
zh_bv = 0:0.1:1;
Avhb_Av = interp1(zh_bv,Avhb,HT.Z/VT.b,'spline','extrap');
Kh = [0,0.28,0.5,0.7,0.82,0.92,0.98,1.03,1.07,1.1,1.12];
S_ratio = 0:0.2:2;
K_h = interp1(S_ratio,Kh,HT.S(end)/VT.S(end),'spline','extrap');
    
%Calculate Lift Curve Slope
B=sqrt(1-AERO.MACH(1)^2*cosd(WG.swp(2,end))^2);     %Prandtl-Gluaert Correction
k=HT.a0(end)/(2*pi);                                %2-D Lift Curve Slope 
AR_eff = VT.AR(end)*Avb_Av*(1+K_h*(Avhb_Av-1));
VT.a = 2*pi*AR_eff/(2+sqrt((AR_eff*B/k)^2*(1+tand(WG.swp(3,end))^2/B^2)+4));
VT.a = VT.a*pi/180;

%Calculate Sidewash Gradient/Dynamic Pressure Ratio
VT.swash = 0.724+3.06*VT.S(end)/WG.S(end)/(1+cosd(WG.swp(2,end)))+...
    0.4*Z_WG/max(BD.ZU-BD.ZL)+0.009*WG.AR(end);

%Estimate Vertical Tail Contribution to CYb
CYB_v = -VT.k*VT.a*VT.swash*VT.S(end)/WG.S(end);

%Calculate CYb
AC.CYb = CYB_wb+CYB_v;

%Estimate Dihedral Effect on CNb
CNB_gamma = -0.075*WG.gamma*AC.CL*pi^2/180^2;

%Estimate Sweep Effect on CNb
A = WG.AR(end); cswp=cosd(WG.swp(2,end)); sswp=sind(WG.swp(2,end)); tswp=sswp/cswp;
CNB_sweep = AC.CL^2*pi/180*(1/(4*pi*A)-tswp/(pi*A*(A+4*cswp))*(cswp-...
    A/2-A^2/(8*cswp)-6*(AC.x_cg-WG.x_ac)*sswp/A));
CNB_sweep = (A+4*cswp)/(A*B+4*cswp)*(A^2*B^2+4*A*B*cswp-8*cswp^2)/...
    (A^2+4*A*cswp-8*cswp^2)*CNB_sweep;  %account for Mach effects

%Calculate CNb
AC.Cnb = CNB_gamma+CNB_sweep+BD.Cnb-CYB_v*VT.l/WG.b;

%Estimate Roll Derivatives (ClB in Lat_Dir Corrections)
FCL = (BD.ZU+BD.ZL)/2;
z_bd = interp1(BD.X,FCL,WG.X+WG.CHRDR/4);
z_wg = z_bd-WG.Z;
AC.Clb = AC.Clb+1.2*sqrt(WG.AR(end))*pi/180*2*z_wg*BD.d_eq/WG.b^2;
AC.Clb = AC.Clb+CYB_v*VT.h/WG.b;

%Aileron Effectiveness
AC.Clda = 0.1;
AC.Cnda = 0.1;

end