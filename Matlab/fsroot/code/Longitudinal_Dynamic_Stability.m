function Longitudinal_Dynamic_Stability
global AC AERO ATM WG HT

prop = 1;

%Inertia
m = AERO.WT/32.17;  %slugs
Iy = AERO.YI;

%Speed
M = AERO.MACH(1);   
U = M*ATM.a;        %ft/s
Q = ATM.Q;          %lb/ft^2

%Drag 
AC.CD = AC.CD0 + WG.K*AC.CL^2;  %cd = cd0 + K*CL^2
AC.CDa = 2*WG.K*AC.CL*AC.CLa;     %cda = 2*K*CL*a

%X-Force Coefficients
AC.CDu = 0;
if prop, CXu = -AC.CDu - 3*AC.CD; else CXu = -AC.CDu - 2*AC.CD; end
CXa = AC.CL - AC.CDa;  
CXadot = 0;
CXq = 0;
CXt = 0;
CXde = 0;

%X-Force Derivatives
Xu = CXu*Q*WG.S(end)/(m*U);      %1/s
Xa = CXa*Q*WG.S(end)/m;          %ft/s^2

%Z-Force Coefficients
AC.CLu = M^2/(1-M^2)*AC.CL;
CZu = -AC.CLu - 2*AC.CL;
CZa = -AC.CLa - AC.CD;
AC.CLadot = 2*HT.a*HT.eta*HT.V*HT.dwash*1.1; 
CZadot = -AC.CLadot;
AC.CLq = 2*HT.a*HT.eta*HT.V*1.1;
CZq = -AC.CLq;
CZde = -AC.CLde;
CZt = 0;

%Z-Force Derivatives
Zu = CZu*Q*WG.S(end)/(m*U);                  %1/s
Za = CZa*Q*WG.S(end)/m;                      %ft/s^2
Zadot = CZadot*Q*WG.S(end)*WG.cbar(end)/(2*m*U);  %ft/s
Zq = CZq*Q*WG.S(end)*WG.cbar(end)/(2*m*U);        %ft/s
Zde = CZde*Q*WG.S(end)/m;                    %ft/s^2

%M-Moment Coefficients
AC.Cmu = 0;                 %CMu = CMM*M
CMu = AC.Cmu;
CMa = AC.Cma;
AC.Cmadot = -2*HT.a*HT.eta*HT.V*HT.dwash*HT.l/WG.cbar(end)*1.1;
CMadot = AC.Cmadot;
AC.Cmq = -2*HT.a*HT.eta*HT.V*HT.l/WG.cbar(end)*1.1;
CMq = AC.Cmq;
CMde = AC.Cmde;

%M-Moment Derivatives
Mu = CMu*Q*WG.S(end)*WG.cbar(end)/(Iy*U);          %1/(ft*s)
Ma = CMa*Q*WG.S(end)*WG.cbar(end)/Iy;              %1/s^2
Madot = CMadot*Q*WG.S(end)*WG.cbar(end)^2/(2*Iy*U);%1/s
Mq = CMq*Q*WG.S(end)*WG.cbar(end)^2/(2*Iy*U);      %1/s
Mde = CMde*Q*WG.S(end)*WG.cbar(end)/Iy;            %1/s^2

%Body Axis Variables
c1 = WG.cbar(end)/(2*U);
m1 = 2*m/(Q/U*WG.S(end));
iy1 = Iy/(Q*WG.S(end)*WG.cbar(end));
zeta1 = (CXadot*c1)/(m1-CZadot*c1);
zeta2 = (CMadot*c1)/(m1-CZadot*c1);

%Construct A-Matrix
a = zeros(4);
a(1,1) = (CXu+zeta1*CZu)/m1;
a(1,2) = (CXa+zeta1*CZa)/m1;
a(1,3) = (CXq*AC.CL+zeta1*(m1+CZq*c1))/m1;
a(1,4) = (CXt+zeta1*CZt)/m1;
a(2,1) = CZu/(m1-CZadot*c1);
a(2,2) = CZa/(m1-CZadot*c1);
a(2,3) = (m1+CZq*c1)/(m1-CZadot*c1);
a(2,4) = CZt/(m1-c1*CZadot*c1);
a(3,1) = (CMu+zeta2*CZu)/iy1;
a(3,2) = (CMa+zeta2*CZa)/iy1;
a(3,3) = (CMq*AC.CL+zeta2*(m1+CZq*c1))/iy1;
a(3,4) = zeta2*CZt/iy1;
a(4,1) = 0; a(4,2) = 0; a(4,3) = 1; a(4,4) = 0;

%Construct B-Matrix
b = zeros(4,1);
b(1) = (CXde+zeta1*CZde)/m1;
b(2) = CZde/(m1-c1*CZadot);
b(3) = (CMde+zeta2*CZde)/iy1;
b(4) = 0;

%Construct C-Matrix
c = zeros(size(a));

%Construct D-Matrix
d = zeros(size(b));
% 
% figure
% roots = eig(a)
% damp(roots)
% plot(roots,'o')
% waitfor(gcf)


%Short Period
g = 32.17;

Ashort = [ Za/U                1            
         (Ma+(Madot*Za)/U)    (Mq+Madot)];
eAshort = eig(Ashort);

% PHUGOID MODE
Aphu = [ Xu      g            
        -Zu/U    0];
eAphu = eig(Aphu);

% hold on
% plot(eAshort,'or')
% plot(eAphu,'or')
% hold off
% damp(eig(Ashort))
% damp(eig(Aphu))
end