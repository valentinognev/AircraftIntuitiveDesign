%Note: wetted areas can be calculated more accurately by incorporating this
%function through Plot_Planform/Plot_Fuselage and taking the cross product
%of two vectors from each cell to find actual surface area.

%Estimate Component Drag
function PT = Drag(PT,unit)
global ATM WG

%Check Component Type
if isfield(PT,'NACA') %planform
    
    %Calculate S_wet
    S_wet=(1.977+0.52*PT.TC)*PT.S(end);
    
    %Calculate L
    %x_tmax=str2double(WG.NACA(2))/10;
    x_tmax=0.2; %guess
    if x_tmax<0.3, L=2; else L=1.2; end
    
    %Calculate Cf
    Re_cbar=ATM.Re*PT.cbar(end);
    if strcmp(unit,'in'), Re_cbar=Re_cbar/12; end
    Cf=0.455/log10(Re_cbar)^2.58;  %Estimated at M=0;
    
    %Determine Correction Factor (RLS)
    RLS=1.3;
    
    %Calculate CD0
    PT.CD0=Cf*(1+L*PT.TC+PT.TC^4)*RLS*S_wet/WG.S(end);
    
else %fuselage
    
    %Calculate S_wet
    h=(PT.ZU-PT.ZL)/2;
    p=2*pi*sqrt((h.^2+PT.R.^2)/2);  %rough perimeter of an ellipse
    dx=PT.X(2:end)-PT.X(1:end-1);
    S_wet=sum((p(1:end-1)+p(2:end))/2.*dx);
    
    %Calculate Cf
    Re_L=ATM.Re*PT.X(end);
    if strcmp(unit,'in'), Re_L=Re_L/12; end
    Cf=0.455/log10(Re_L)^2.58;  
    
    %Calculate Fineness Ratio
    l_d=PT.X(end)/max([2*PT.R,PT.ZU-PT.ZL]);
    
    %Calculate CD0
    PT.CD0=Cf*(1+60/l_d^3+0.0025*l_d)*S_wet/WG.S(end);
    
end
