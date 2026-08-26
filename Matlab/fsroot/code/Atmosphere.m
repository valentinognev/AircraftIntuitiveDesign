function [Results]=Atmosphere(h)
%Standard Atmosphere Property Calculator by Zachary Lietzau
%Input (h): Altitude in feet
%Output (Results): 
%   -Temperature (T)
%   -Pressure (P)
%   -Density (D)
%   -Viscocity (V)
%   -Speed of Sound (a)

h=h(1);
if h<=36089
    theta=1-h/145442;
    delta=(1-h/145442)^5.255876;
    sigma=(1-h/145442)^4.255876;
elseif h<=65617
    theta=0.751865;
    delta=0.223361*exp(-(h-36089)/20806);
    sigma=0.297076*exp(-(h-36089)/20806);
elseif h<=104987 %Inversion
    theta=0.682457+h/945374;
    delta=(0.988626+h/652600)^-34.16320;
    sigma=(0.978261+h/659515)^-35.16320;
elseif h<=154199 %Inversion
    theta=0.482561+h/337634;
    delta=(0.898309+h/181373)^-12.20114;
    sigma=(0.857003+h/190115)^-13.20114;
elseif h<=167323 %Isothermal
    theta=0.939268;
    delta=0.00109456*exp(-(h-154199)/25992);
    sigma=0.00116533*exp(-(h-154199)/25992);
elseif h<=232940 
    theta=1.434843-h/337634;
    delta=(0.838263-h/577922)^12.20114;
    sigma=(0.798990-h/606330)^11.20114;
elseif h<=278386
    theta=1.237723-h/472687;
    delta=(0.917131-h/637919)^17.08160;
    sigma=(0.900194-h/649922)^16.08160;
else
    fprintf('Properties can only be calculated from 0 to 278,386 ft')
    theta=0; delta=0; sigma=0;
end

%Define Standard Sea Level Properties
T_0=518.69;     %R
P_0=2116.22;    %psf
D_0=0.002377;   %slug/ft^3
V_0=3.62E-7;    %lb*s/ft^2

%Calculate Properties at Given Altitude
Results.T=T_0*theta;
Results.P=P_0*delta;
Results.D=D_0*sigma;
Results.V=V_0*theta^1.5*717.42/(Results.T+198.72);  %Sutherland's Eqn
Results.a=sqrt(1.4*1716*Results.T); %Speed of Sound, ft/s
end

