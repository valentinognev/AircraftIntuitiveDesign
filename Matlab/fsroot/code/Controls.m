function PT = Controls(PT)
global AC WG HT VT F A E R

%Perkins and Hage Figure 5-33
tau = [0,0.25,0.4,0.5,0.58,0.65,0.71,0.76];
S_ratio = 0:0.1:0.7;

%Flaps
F.S = 1/2*(F.CHRDFI+F.CHRDFO)*(F.SPANFO-F.SPANFI);
F.tau = interp1(S_ratio,tau,F.S/WG.S(end),'spline');
AC.CLdf = WG.a*F.tau;
F.x_ac = WG.cbar(end)-1/2*(F.CHRDFI+F.CHRDFO);        %made this up for flap ac
%F.l = WG.X+WG.xmac+F.x_ac-AERO.XCG;              %for effect of flap on Cm
F.l = F.x_ac-AC.x_cg;
AC.Cmdf = -WG.a*F.tau*F.l/WG.cbar(end);

%Elevator
E.S = 1/2*(E.CHRDFI+E.CHRDFO)*(E.SPANFO-E.SPANFI);
E.tau = interp1(S_ratio,tau,E.S/HT.S(end),'spline');
AC.CLde = HT.a*HT.eta*HT.S(end)/WG.S(end)*E.tau;
AC.Cmde = -HT.l/WG.cbar(end)*AC.CLde;

%Rudder
R.S = 1/2*(R.CHRDFI+R.CHRDFO)*(R.SPANFO-R.SPANFI);
R.tau = interp1(S_ratio,tau,E.S/VT.S(end),'spline');
AC.CYdr = VT.k*VT.a*VT.swash*VT.S(end)/WG.S(end)*R.tau;
AC.Cldr = VT.k*VT.a*VT.swash*VT.S(end)/WG.S(end)*VT.h/WG.b*R.tau;
AC.Cndr = -AC.CYdr*VT.l/WG.b;

%DATCOM Figure 6.1.4.1-15
Kb0 = [0,0.155,0.305,0.44,0.56,0.675,0.775,0.86,0.93,0.98,1];
Kb1 = [0,0.125,0.25,0.375,0.495,0.6,0.705,0.8,0.89,0.95,1];
eta = 0:0.1:1;

%Ailerons
Kb0_in = interp1(eta,Kb0,A.SPANFI/WG.SSPN,'spline');
Kb1_in = interp1(eta,Kb1,A.SPANFI/WG.SSPN,'spline');
Kb0_out = interp1(eta,Kb0,A.SPANFO/WG.SSPN,'spline');
Kb1_out = interp1(eta,Kb1,A.SPANFO/WG.SSPN,'spline');
Kb_in = Kb0_in+WG.TR*(Kb1_in-Kb0_in);
Kb_out = Kb0_out+WG.TR*(Kb1_out-Kb0_out);
A.Kb = Kb_out-Kb_in;
%AC.Clda = WG.a*A.tau/(WG.S*WG.b)*integral...
%AC.Cnda = 2*WG.K*AC.CL*AC.Clda;

end
