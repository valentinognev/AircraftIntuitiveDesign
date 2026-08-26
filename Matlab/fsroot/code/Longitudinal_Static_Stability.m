function Longitudinal_Static_Stability(trim,htail,body,angl)
global AC WG HT BD AERO F E

%Convert to Degrees if Necessary
if WG.a>1, WG.a=WG.a*pi/180; end
if HT.a>1, HT.a=HT.a*pi/180; end

%Project HT dimensions if using V-Tail
if angl && (HT.DHDADI || HT.DHDADO)
    if HT.SSPNOP
        HT.S(end)=HT.S(end)*(HT.SSPNOP*cosd(HT.DHDADI)+...
            (HT.SSPN-HT.SSPNOP)*cosd(HT.DHDADO))/HT.SSPN;
    else
        HT.S(end)=HT.S(end)*cosd(HT.DHDADI);
    end
end

%Lift Constants
TLT = HT.a*HT.eta*HT.S(end)/WG.S(end);                    %Tail Lift Coefficient Term
AC.CLa = WG.a+TLT*(1-HT.dwash);                   %Aircraft Lift Curve Slope

%Moment Constants
AC.Cma = WG.a*(AC.x_cg-WG.x_ac);                %A/C 
if htail, AC.Cma = AC.Cma-TLT*HT.l/WG.cbar(end)*(1-HT.dwash); end %HTail
if body, AC.Cma = AC.Cma+BD.Cma; end            %Fuselage

%Full Analysis for Trim Solution
if trim == 1 %adjust elevator only
        
    %Calculate Lift Terms
    WG.CL0=WG.a*(WG.i-WG.alpha0L);                  %Wing Lift
    if length(F.DELTA)==1
        WG.CL0 = WG.CL0+WG.a*F.DELTA*F.tau;         %Flap
        %WG.CL0 = WG.CL0+AC.CLdf*F.DELTA;
    end
    HT.CL0=TLT*(HT.i-HT.dwash*(WG.i-WG.alpha0L));   %Tail Lift (no elev)
    if length(E.DELTA)==1
        HT.CL0 = HT.CL0 + TLT*E.DELTA*E.tau;        %Elevator Lift
        %HT.CL0 = HT.CL0 + AC.CLde*E.DELTA;       
    end
    AC.CL0 = WG.CL0;                                %Total AC Lift
    if htail, AC.CL0 = AC.CL0 + HT.CL0; end
    AC.alpha = (AC.CL-AC.CL0)/AC.CLa;
    
    %Calculate Moment Terms
    WG.Cm0 = WG.Cm+WG.a*(WG.i-WG.alpha0L)*(AC.x_cg-WG.x_ac); %Wing Moment
    if length(F.DELTA)==1
        WG.Cm0=WG.Cm0 - WG.a*F.DELTA*F.tau*F.l/WG.cbar(end);    	 %Flap Moment
        %WG.Cm0 = WG.Cm0 + AC.Cmdf*F.DELTA;
    end
    HT.Cm0 = -HT.l/WG.cbar(end)*HT.CL0;                         	 %Tail Moment
    AC.Cm0 = WG.Cm0;                                         %AC Moment
    if htail, AC.Cm0 = AC.Cm0+HT.Cm0; end
    if body, AC.Cm0 = AC.Cm0+BD.Cm0; end
    
    %Calculate Required Elevator Deflection
    CM = AC.Cm0+AC.Cma*AC.alpha - AC.Cmde*E.DELTA;
    delta = -CM/AC.Cmde;
    E.DELTA = delta;
    
elseif trim == 2 %adjust wing incidence, htail incidence, and/or alpha
        
    %Variables to be Found
    syms i_wg i_ht aoa
 	
    %Determine Lift Terms
    CL0_wg = WG.a*(i_wg-WG.alpha0L);                    %Wing Lift
    if length(F.DELTA)==1
        CL0_wg = CL0_wg+WG.a*F.DELTA*F.tau;             %Flap Lift
    end
    CL0_ht=TLT*(i_ht-HT.dwash*(i_wg-WG.alpha0L));       %Tail Lift
    if length(E.DELTA)==1
        CL0_ht = CL0_ht+TLT*E.DELTA*E.tau;              %Elevator Lift 
    end
    CL0=CL0_wg+CL0_ht;                                  %Aircraft Lift
    
    %Determine Moment Terms
    Cm0_wg=WG.Cm+WG.a*(i_wg-WG.alpha0L)*(AC.x_cg-WG.x_ac);  %Wing Moment
    if length(F.DELTA)==1
        Cm0_wg=Cm0_wg - WG.a*F.DELTA*F.tau*F.l/WG.cbar(end);     %Flap Moment
    end
    Cm0_ht = -HT.l/WG.cbar(end)*CL0_ht;                          %Tail Moment
    Cm0 = Cm0_wg+Cm0_ht;                                    %AC Moment
    if body, Cm0 = Cm0+BD.Cm0; end       
    
    %Trim Solution
    if isempty(WG.i) && isempty(HT.i)
        tr=solve(AC.CL==CL0+AC.CLa*aoa, 0==Cm0+AC.Cma*aoa, aoa==AERO.ALSCHD);
    elseif isempty(WG.i)
        tr=solve(AC.CL==CL0+AC.CLa*aoa, 0==Cm0+AC.Cma*aoa, i_ht==HT.i);
    else %if isempty(HT.i)
        tr=solve(AC.CL==CL0+AC.CLa*aoa, 0==Cm0+AC.Cma*aoa, i_wg==WG.i);
    end
    er = 0;
    WG.i=double(tr.i_wg); if ~isreal(WG.i)||abs(WG.i)>60, WG.i=0; er=1; end
    HT.i=double(tr.i_ht); if ~isreal(HT.i)||abs(HT.i)>60, HT.i=0; er=2; end
    AC.alpha=double(tr.aoa);    if ~isreal(AC.alpha), AC.alpha=0; er=3; end

    %Trim Error
    if length(AERO.ALSCHD)==1, AERO.ALSCHD = AC.alpha; end
    if er, warndlg('Error calculating trim'), end
    
end

%Re-calculate Lift Terms
WG.CL0=WG.a*(WG.i-WG.alpha0L);                  %Wing Lift
if length(F.DELTA)==1
    WG.CL0 = WG.CL0+WG.a*F.DELTA*F.tau;         %Flap
    %WG.CL0 = WG.CL0+AC.CLdf*F.DELTA;
end
HT.CL0=TLT*(HT.i-HT.dwash*(WG.i-WG.alpha0L));   %Tail Lift
if length(E.DELTA)==1
    HT.CL0 = HT.CL0 + TLT*E.DELTA*E.tau;        %Elevator Lift
    %HT.CL0 = HT.CL0 + AC.CLde*E.DELTA;       
end
AC.CL0 = WG.CL0;                                %Total AC Lift
if htail, AC.CL0 = AC.CL0 + HT.CL0; end  

%Angle of Attack
if length(AERO.ALSCHD)==1
    AC.alpha = AERO.ALSCHD;
else
    AC.alpha = (AC.CL-AC.CL0)/AC.CLa;
end

%Account for Wing Drag Term
if ~isfield(WG,'e'), d=0.01; WG.e=1/(1+d);   end
if ~isfield(WG,'K'), WG.K=1/(pi*WG.e*WG.AR(end)); end

%Determine Neutral Point
Kt = TLT/WG.a*(1-HT.dwash);
CL_wg = WG.a*(WG.i-WG.alpha0L)+WG.a*AC.alpha;
z_wg = (AERO.ZCG-WG.Z)/WG.cbar(end);
l_ac = HT.l+WG.cbar(end)*(AC.x_cg-WG.x_ac);
num =(1+Kt)*WG.x_ac-CL_wg*(1/(180/pi*WG.a)-2*WG.K)*z_wg;
if htail, num = num+Kt*l_ac/WG.cbar(end); end        %Account for htail
if body, num = num-BD.Cma/AC.CLa; end             %Account for fuselage
AC.N0 = num/(1+Kt);

%Re-calculate Moment Terms
WG.Cm0 = WG.Cm+WG.a*(WG.i-WG.alpha0L)*(AC.x_cg-WG.x_ac); 	%Wing Moment
if length(F.DELTA)==1
    WG.Cm0=WG.Cm0 - WG.a*F.DELTA*F.tau*F.l/WG.cbar(end);    %Flap Moment
    %WG.Cm0 = WG.Cm0 + AC.Cmdf*F.DELTA;
end
HT.Cm0 = -HT.l/WG.cbar(end)*HT.CL0;                              %Tail Moment
AC.Cm0 = WG.Cm0;                                            %AC Moment
if htail, AC.Cm0 = AC.Cm0+HT.Cm0; end    
if body, AC.Cm0 = AC.Cm0+BD.Cm0; end
AC.Cm = AC.Cm0+AC.Cma*AC.alpha;

end