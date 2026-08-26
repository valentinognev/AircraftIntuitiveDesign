function [Z_eta,Z_w]=Downwash
global ATM HT WG AERO AC

%Assume Tail Incidence
if ~isfield(HT,'i'), HT.i=-1; end

%Find x and z of tail ac relative to wing root TE
HT.x=HT.X+(HT.xmac+HT.x_ac*HT.cbar(end))*cosd(HT.i)-(WG.X+WG.CHRDR*cosd(WG.i));
HT.z=HT.Z-(HT.xmac+HT.x_ac*HT.cbar(end))*sin(HT.i)-(WG.Z-WG.CHRDR*sin(WG.i));

%Determine h_epsilon and l_epsilon
h=(HT.x-HT.z*tand(WG.i))*sind(WG.i)+HT.z/cosd(WG.i);
l=(HT.x-HT.z*tand(WG.i))*cosd(WG.i)+(WG.CHRDR-(WG.Cm+WG.cbar(end)/4));

%Calculate K Coefficients
K1=1/WG.AR(end)-1/(1+WG.AR(end)^1.7);
K2=(10-3*WG.TR(end))/7;
K3=(1-h/WG.b)/(2*l/WG.b)^(1/3);

%Solve for Downwash Gradient
HT.dwash=4.44*(K1*K2*K3*sqrt(cosd(WG.swp(2,end))))^1.19;

%Estimate Cl and Alpha
if ~isfield(AC,'CL'), AC.CL=AERO.WT/(ATM.Q*WG.S(end)); end
if ~isfield(AC,'alpha'), AC.alpha=0; end

%Downwash Angle
if ~isfield(WG,'e'), WG.e=0.9; end %Span Efficiency Factor
epsilon=57.3*1.62*AC.CL/(pi*WG.e*WG.AR(end));

%Additional HT Location Reference Values wrt Wake Center Line
Gamma=atan(HT.z/HT.x);      Ro=WG.i-Gamma;
Tau=AC.alpha+WG.i-epsilon;  Z2=HT.z-HT.x*tand(Tau);
L_eta=HT.x/cosd(Tau)+(Z2)*sind(Tau);
Z_eta=Z2*cosd(Tau);

%Wing Wake Half-Width
Z_w=0.68*WG.cbar(end)*sqrt(WG.CD0*(0.15+L_eta/WG.cbar(end)));

if Z_eta<Z_w
    dq0=2.42*sqrt(WG.CD0)/(0.3+L_eta/WG.cbar(end));
    dq=dq0*cos(pi/2*Z_eta/Z_w)^2;
    HT.eta=1-dq;
else
    HT.eta=1;
    Pr1=sprintf('The wing''s wake half-width of %.2fft\n',Z_w);
    Pr2='does not interact with the tail.';
    %msgbox([Pr1,Pr2]);
end

end