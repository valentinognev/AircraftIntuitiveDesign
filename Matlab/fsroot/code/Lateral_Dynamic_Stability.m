function Lateral_Dynamic_Stability
global AC WG VT

%Y-Force Coefficients
AC.CYp = AC.CL*(WG.AR(end)+cosd(WG.swp(2,end)))/(WG.AR(end)+4*cosd(WG.swp(2,end)))*...
    tand(WG.swp(2,end)) + 2*AC.CYb/WG.b*(VT.h-VT.hp);
AC.CYr = -2*AC.CYb*VT.l/WG.b;

%L-Moment Coefficients
AC.Clp = -WG.a/12*(1+3*WG.TR(end))/(1+WG.TR(end));
AC.Clr = AC.CL/4-2*AC.CYb*VT.l*VT.h/WG.b^2;

%N-Moment Coefficients
AC.Cnp = -AC.CL/8 - 2*AC.CYb*VT.l*(VT.h-VT.hp)/WG.b^2;
AC.Cnr = -2*VT.a*VT.swash*VT.S(end)/WG.S(end)*(VT.l/WG.b)^2;

end