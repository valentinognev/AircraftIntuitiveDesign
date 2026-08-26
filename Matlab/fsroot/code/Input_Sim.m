%Write Geom/Aero Data to Simulink Input File
function Input_Sim(Results,AERO,ATM,AC,WG,A,E,R)
%global AERO AC WG A E R
%clc
%clear

%NEED: Clb and Clda and CNda

%Digital DATCOM Stability Derivatives
if isempty(Results), mode = 0; else mode = 1; end
assignin('base','mode',mode)
assignin('base','Results',Results)

%Trim Velocity components
initu = AERO.MACH(1)*ATM.a*cosd(AC.alpha);
initv = 0;
initw = AERO.MACH(1)*ATM.a*sind(AC.alpha);
assignin('base','initu',initu)
assignin('base','initv',initv)
assignin('base','initw',initw)

%Initial rates
initp=0;
initq=0;
initr=0;
assignin('base','initp',initp)
assignin('base','initq',initq)
assignin('base','initr',initr)

%Initial attitude
initbank = 0;
initpitch=atand(initw/initu); %equivalent to theta = alpha
inithead=0;
assignin('base','initbank',initbank)
assignin('base','initpitch',initpitch)
assignin('base','inithead',inithead)

%Initial Position
initnorth=0;
initeast=0;
initalt=AERO.ALT(1);
assignin('base','initnorth',initnorth)
assignin('base','initeast',initeast)
assignin('base','initalt',initalt)

%Initial Controls
elevator = E.DELTA(1); % Negative nose up 
aileron = (A.DELTAL(1)+A.DELTAR(1))/2;
rudder = R.DELTA(1);
throttle = 1;
control = [elevator, aileron, rudder, throttle];
assignin('base','control',control)

%Stability Derivatives

%CL - Lift
cla = AC.a*180/pi
cladot = AC.CLadot*180/pi
clq = AC.CLq*180/pi
clde=AC.CLde*180/pi
clo = AC.CL0
assignin('base','cla',cla)
assignin('base','cladot',cladot)
assignin('base','clq',clq)
assignin('base','clde',clde)
assignin('base','clo',clo)

%CD - Drag
cda2 = WG.K
cdo = AC.CD0
assignin('base','cda2',cda2)
assignin('base','cdo',cdo)

%CM - Pitch
cma = AC.CMa*180/pi
cmadot = AC.CMadot*180/pi
cmde = AC.CMde*180/pi
cmq = AC.CMq*180/pi
assignin('base','cma',cma)
assignin('base','cmadot',cmadot)
assignin('base','cmde',cmde)
assignin('base','cmq',cmq)

%CY - Side Force
cyb = AC.CYb*180/pi
cydr = AC.CYdr*180/pi
assignin('base','cyb',cyb)
assignin('base','cydr',cydr)

%Cl - Roll
clb = AC.ClB*180/pi
clp = AC.Clp*180/pi
clr = AC.Clr*180/pi
clda = AC.Clda*180/pi
cldr = AC.Cldr*180/pi
assignin('base','clb',clb)
assignin('base','clp',clp)
assignin('base','clr',clr)
assignin('base','clda',clda)
assignin('base','cldr',cldr)

%CN - Yaw
cnb = AC.CNB*180/pi 
cnp = AC.CNp*180/pi
cnr = AC.CNr*180/pi
cnda = AC.CNda*180/pi
cndr = AC.CNdr*180/pi
assignin('base','cnb',cnb)
assignin('base','cnp',cnp)
assignin('base','cnr',cnr)
assignin('base','cnda',cnda)
assignin('base','cndr',cndr)

%Aero Parameters
sw = WG.S
b = WG.b
cbar = WG.cbar
weight = AERO.WT
assignin('base','sw',sw)
assignin('base','b',b)
assignin('base','cbar',cbar)
assignin('base','weight',weight)

%Reference Positions
cg = [AERO.XCG, AERO.ZCG, 0]
ac = [WG.X+WG.xmac+WG.cbar*WG.x_ac, WG.Z, WG.ymac]
eng = [0 0 0]
assignin('base','cg',cg)
assignin('base','ac',ac)
assignin('base','eng',eng)

%Moment of Inertia
jx = AERO.XI
jy = AERO.YI
jz = AERO.ZI
jxz = 0
assignin('base','jx',jx)
assignin('base','jy',jy)
assignin('base','jz',jz)
assignin('base','jxz',jxz)

end

