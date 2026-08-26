function [geo,state] = Tornado_IO(mesh)
global WG HT VT F A E R NP AERO ATM AC cmp

%Discretization
nj = str2double(mesh{1});
ni = str2double(mesh{2});
m = [1,1];
if length(mesh)==3
    if WG.TWISTA 
        m(1) = str2double(mesh{3});
    else
        m(2) = str2double(mesh{3});
    end
elseif length(mesh)==4
    m(1) = str2double(mesh{3});
    m(2) = str2double(mesh{4});
end

%Write Geometry Data
if get(cmp(1),'Value')
    CS = {}; %cell array of relevant control surfaces
    if length(F.DELTA)>1 || F.DELTA, CS{1} = F; end
    if length(A.DELTAL)>1 || A.DELTAL || length(A.DELTAR)>1 || A.DELTAR
        CS{end+1} = A; end
    geo = Write_Geometry(WG,CS,ni,nj,m);
end
if get(cmp(2),'Value')
    CS = {}; if length(E.DELTA)>1 || E.DELTA, CS{1} = E; end
    geo = Write_Geometry(HT,CS,round(ni/2),round(nj/2),[1,1],geo);
end
if get(cmp(3),'Value')
    CS = {}; if length(R.DELTA)>1 || R.DELTA, CS{1} = R; end
    geo = Write_Geometry(VT,CS,round(ni/2),round(nj/2),[1,1],geo,'v');
end

for i=1:3
    if ~isempty(NP{i}) && get(cmp(4+i),'Value')
        type = {'h','h','v','v'};
        geo = Write_Geometry(NP{i},{},round(ni/2),round(nj/2),[1,1],geo,type{i});
    end
end

%Write Flight Conditions
AS_alpha_beta = 0;
if AS_alpha_beta
    prompt = {'Airspeed (m/s)','Angle of Attack, (deg)','Sideslip Angle, (deg)'};
    def{1} = num2str(AERO.MACH*ATM.a/3.28084);	%airspeed (m/s)
    def{2} = num2str(AC.alpha);                 %angle of attack
    def{3} = num2str(0);                        %angle of sideslip
    out = inputdlg(prompt,'Simulation Parameters',1,def);
    state.AS = eval(out{1});
    state.alpha = eval(out{2})*pi/180;
    state.betha = eval(out{3})*pi/180;
else
    state.AS = AERO.MACH*ATM.a/3.28084;	%airspeed (m/s)
    state.alpha = AC.alpha*pi/180;     	%angle of attack
    state.betha = 0;                  	%angle of sideslip
end
state.P = 0;                        %roll angluar rate
state.Q = 0;                        %pitch angular rate
state.R = 0;                        %yaw angular rate
state.alphadot = 0;                 %angle of attack time derivative
state.bethadot = 0;                 %angle of sidesliptime derivative
state.ALT = AERO.ALT/3.28084;       %altitude, meters.
state.rho = ATM.D*515.379;       	%air density, kg/m^3.
state.pgcorr = 0;                   %Prandtl-Glauert correction.

end

function [geo] = Write_Geometry(PT,CS,ni,nj,m,geo,type)
global AERO

%Initialize Geometry "geo" Structure
if nargin<7, type = 'h'; end
if nargin<6 || isempty(geo)
    geo.nwing = 0;				%number of wings (scalar)
    geo.ref_point = [0,0,0];  	%system reference point (vector)
    geo.CG = [AERO.XCG,0,0];  	%system center of gravity (vector)
    
    %Planform
    geo.nelem = [];         %number of partitions on each wing (1d array)
    geo.c = [];           	%root chord (2d array)
    geo.T = [];            	%taper ratio (2d array)
    geo.SW = [];           	%sweep (2d array)
    geo.dihed = [];        	%dihedral (2d array)
    geo.b = [];            	%span (2d array)
    geo.symetric = [];   	%wing symmetry (2d boolean)
    geo.startx = [];     	%partition starting coordinate (2d array)
    geo.starty = [];       	% ---"----
    geo.startz = [];      	% ---"----
    
    %Airfoil and Twist
    geo.TW = [];            %partition twist (3d array)
    geo.foil = {};          %partition airfoils (3d cell array)
    
    %Flaps
    geo.fnx = [];           %number of panels on flap chords (2d array)
    geo.fsym = [];          %flap deflection symmetry (2d boolean)
    geo.fc = [];            %flap chord in percent of wingchord (2d array)
    geo.flapped = [];       %flapped partition (2d boolean)
    geo.flap_vector = [];	%flap deflection (vector)
    geo.flap_id = [];       %identify flap type (my addition for AVL input)
    
    %Discretization
    geo.meshtype = [];      %mesh type (2d array)
    geo.ny = [];            %number of panels in span (2d array)
    geo.nx = [];			%number of panels on chord (2d array)
end

%Add Planform Geometry
geo.nwing = geo.nwing+1;				%number of wings (scalar)
geo.symetric(end+1) = 1;                %symmetry (vector)

%Break into Several Sections if Varying Linearity
eta = [0,1];
if m(1)>1 || m(2)>1, eta = cos(linspace(pi/2,0,nj)); nj = 1; end
flap_id = zeros(size(eta));

%Break for Control Surfaces
for i=1:length(CS)
    eta = [[CS{i}.SPANFI,CS{i}.SPANFO]./PT.SSPN,eta];
    flap_id = [i,i,flap_id];
end
if PT.SSPNOP %one more section for break span
    eta(end+1) = PT.SSPNOP/PT.SSPN; jbrk = length(eta); flap_id(end+1) = 0; 
end
[eta,index]=unique(eta); flap_id=flap_id(index); flap_pos=find(flap_id);
if length(flap_pos) == 2
    flap_index{1} = flap_pos(1):flap_pos(2)-1;
elseif length(flap_pos) == 3
    flap_index{1} = flap_pos(1):flap_pos(2)-1;
    flap_index{2} = flap_pos(2):flap_pos(3)-1;
elseif length(flap_pos) == 4
    flap_index{1} = flap_pos(1):flap_pos(2)-1;
    flap_index{2} = flap_pos(3):flap_pos(4)-1;
end

%Prepare Linear Interpolation
if PT.SSPNOP
    eta0 = [0,PT.SSPNOP/PT.SSPN,1];
    c0 = [PT.CHRDR,PT.CHRDBP,PT.CHRDTP];
    x0 = [PT.X,PT.Xbrk,PT.Xtip];
    y0 = [PT.Y,PT.Y+PT.SSPNOP,PT.Y+PT.SSPN];
    z0 = [PT.Z,PT.Zbrk,PT.Ztip];
    jspan = find(index==jbrk):length(index)-1;
else
    eta0 = [0,1];
    c0 = [PT.CHRDR,PT.CHRDTP];
    x0 = [PT.X,PT.Xtip];
    y0 = [PT.Y,PT.Y+PT.SSPN];
    z0 = [PT.Z,PT.Ztip];
    jspan = [];
end

%Planform
n = length(eta)-1;
geo.nelem(end+1) = n;
c = interp1(eta0,c0,eta);
geo.c(end+1,1:n) = c(1:end-1);
geo.T(end+1,1:n) = c(2:end)./c(1:end-1);
geo.SW(end+1,1:n) = PT.swp(2,1)*pi/180;
if PT.SSPNOP, geo.SW(end,jspan) = PT.swp(2,2)*pi/180; end
geo.dihed(end+1,1:n) = PT.DHDADI*pi/180;
if PT.SSPNOP, geo.dihed(end,jspan) = PT.DHDADO*pi/180; end
geo.b(end+1,1:n) = (eta(2:end)-eta(1:end-1))*PT.SSPN;
geo.startx(end+1,1:n) = interp1(eta0,x0,eta(1:end-1));
geo.starty(end+1,1:n) = interp1(eta0,y0,eta(1:end-1));
geo.startz(end+1,1:n) = interp1(eta0,z0,eta(1:end-1));

%Airfoil and Twist
theta = (PT.i-PT.TWISTA*eta.^m(1))*pi/180;
geo.TW(end+1,1:n,1) = theta(1:end-1);
geo.TW(end,1:n,2) = theta(2:end);

if length(PT.DATA)==2 %varying airfoil geometry
    data1 = PT.DATA{1};
    data2 = PT.DATA{2};
    N = length(data1);
    if length(data1)>length(data2)
        N = length(data2);
        pts1 = unique(round(linspace(1,length(data1),N)))';
        data1 = interp2(data1,1:2,pts1,'nearest');
    elseif length(data2)>length(data1)
        N = length(data1);
        pts2 = unique(round(linspace(1,length(data2),N)))';
        data2 = interp2(data2,1:2,pts2,'nearest');
    end
    LE = ceil(N/2);
    if mod(N,2) %make even
        data1(LE+1:end+1,:) = data1(LE:end,:);
        data2(LE+1:end+1,:) = data2(LE:end,:);
    end
    x1 = data1(:,1);	z1 = data1(:,2);
    x2 = data2(:,1);	z2 = data2(:,2);
    x = x1(:)+(x2(:)-x1(:)).*eta.^m(2);
    z = z1(:)+(z2(:)-z1(:)).*eta.^m(2);
    geo.foil(end+1,1,1)={[x(:,1),z(:,1)]};
    geo.foil(end,1,2)={[x(:,2),z(:,2)]};
    for i=2:n
        geo.foil(end,i,1)={[x(:,i),z(:,i)]};
        geo.foil(end,i,2)={[x(:,i+1),z(:,i+1)]};
    end
else
    geo.foil(end+1,1:n,1:2)=PT.DATA(1);
end

%Flaps
geo.fnx(end+1,1:n) = 0;
geo.fsym(end+1,1:n) = 0;
geo.fc(end+1,1:n) = 0;
geo.flapped(end+1,1:n) = 0;
geo.flap_vector(end+1,1:n) = 0;
geo.flap_id(end+1,1:n,2) = 0;
for i=1:length(CS)
    geo.flap_id(end,flap_index{i},i) = i;
    geo.fsym(end,flap_index{i}) = 1;
    geo.fc(end,flap_index{i}) = CS{i}.CHRDFI/geo.c(find(flap_id==i,1));
    ni_flap = ceil(geo.fc(end,flap_index{i})*ni);
    geo.fnx(end,flap_index{i}) = ni_flap;
    geo.flapped(end,flap_index{i}) = 1;
    if ~isfield(CS{i},'DELTA')
        if CS{i}.DELTAR~=-CS{i}.DELTAR
            geo.fsym(end,flap_index{i}) = 0; 
        elseif CS{i}.DELTAR~=CS{i}.DELTAR
            warndlg('Assuming left aileron deflection for both')
        end
        CS{i}.DELTA = -CS{i}.DELTAL;
    end
    geo.flap_vector(end,flap_index{i}) = CS{i}.DELTA(1)*pi/180;
end

%Discretization
geo.meshtype(end+1,1:n-1) = 6; geo.meshtype(end,n) = 3; %cos at tip
geo.nx(end+1,1:n) = ni-geo.fnx(end,1:n);
geo.ny(end+1,1:n) = ceil(nj*geo.b(end,1:n)/PT.SSPN);

%vertical symmetry fix
if strcmp(type,'v')
    geo.dihed(end,:) = pi/2 - abs(geo.dihed(end,:));
%     starty = geo.starty(end,:);
%     geo.starty(end,:) = geo.startz(end,:);
%     geo.startz(end,:) = starty;
    if ~PT.gamma && ~PT.Y
        geo.symetric(end) = 0;
    else
        geo.symetric(end) = 1;
    end
end

end