%Plot Fuselage
function [h,g] = Plot_Body(PT,a,n,choice,type,h)

%Initialize Coordinate Variables
g=[]; %handle for line objects (for highlighting selection)
if nargin<6, h=[];      end
if nargin<5, type=0;    end
if nargin<4 || isempty(choice) || strcmp(choice,'init'), choice='00'; end

%Correct n
if mod(n,4), n=n-mod(n,4); end

%If Adjusting Secondary Body
if type
    
    %Position
    if ~isfield(PT,'X0'), PT.X0 = 0; end
    if ~isfield(PT,'Y0'), PT.Y0 = 0; end
    if ~isfield(PT,'Z0'), PT.Z0 = 0; end
    
    %Update X Values
    PT.X = PT.X + PT.X0;
    
    %Update Z Values
    PT.ZU = PT.ZU + PT.Z0;
    PT.ZL = PT.ZL + PT.Z0;
    
    %Y-Offset
    offset = PT.Y0;
else
    offset = 0;
end

%Initialize Arrays
X = zeros(PT.NX,n); Y = X; Z = X;

%Define Center of Each Station
ZC = (PT.ZU+PT.ZL)/2;   H = PT.ZU-ZC;

%Parametrically Map Super-Ellipses or Fermat Curves
if isfield(PT,'P') && any(PT.P~=1)
    
    %P<0: SR-71; P=0: Ellipse; P>0: Rectangular
    PU = 2.^PT.P;
    PL = 2.^PT.P; %Potentially could vary upper and lower curvature
    theta = linspace(0,pi/2,n/4);
    for i=1:PT.NX
        X(i,:) = PT.X(i);
        
        %Y
        Y(i,1:n/4) = -PT.R(i)*cos(theta).^(2/PU(i));
        Y(i,n/4+1:n/2) = fliplr(PT.R(i)*cos(theta).^(2/PU(i)));
        Y(i,n/2+1:3*n/4) = PT.R(i)*cos(theta).^(2/PL(i));
        Y(i,3*n/4+1:n) = -fliplr(PT.R(i)*cos(theta).^(2/PL(i)));
        
        %Z
        Z(i,1:n/4) = ZC(i)+H(i)*sin(theta).^(2/PU(i));
        Z(i,n/4+1:n/2) = fliplr(ZC(i)+H(i)*sin(theta).^(2/PU(i)));
        Z(i,n/2+1:3*n/4) = ZC(i)-H(i)*sin(theta).^(2/PL(i));
        Z(i,3*n/4+1:n) = fliplr(ZC(i)-H(i)*sin(theta).^(2/PL(i)));
        
        %Smooth Top and Bottom
        if PT.P(i)<1
            
            r_top=[ceil(1*n/16):ceil(3*n/16),ceil(5*n/16):ceil(7*n/16)];
            pfit = polyfit(Y(i,r_top),Z(i,r_top),5);
            r2_top = ceil(n/8):ceil(3*n/8);
            Z(i,r2_top)=polyval(pfit,Y(i,r2_top));
            r_bot=[ceil(9*n/16):ceil(11*n/16),ceil(13*n/16):ceil(15*n/16)];
            pfit = polyfit(Y(i,r_bot),Z(i,r_bot),5);
            r2_bot = ceil(5*n/8):ceil(7*n/8);
            Z(i,r2_bot)=polyval(pfit,Y(i,r2_bot));

        end
    end
    
else %Parametrically Map Ellipses
    
    theta = linspace(0,2*pi,n);
    for i=1:PT.NX
        X(i,:) = PT.X(i);
        Y(i,:) = PT.R(i)*cos(theta);
        Z(i,:) = ZC(i)+H(i)*sin(theta);
    end
    
end

%Plot
if type==1, tag='NB{1}'; elseif type==2, tag='NB{2}'; else, tag='BD'; end
if isempty(h) || h(1)==0
    h(1) = surf(a,X,Y+offset,Z,'Tag',tag);
else
    set(h(1),'XData',X,'YData',Y+offset,'ZData',Z);
end
if offset
   	if length(h)<2 || h(2)==0
        h(2) = surf(a,X,Y-offset,Z,'Tag',tag);
    else
        set(h(2),'XData',X,'YData',Y-offset,'ZData',Z);
    end
elseif length(h)>1 && h(2)
    delete(h(2)), h(2) = [];
end

%Highlight Section
if str2double(choice(1))==type
    xi=str2double(choice(2:end));
    if ~isnan(xi) && xi
        if offset
            g(1) = plot3(a,X(xi,:),Y(xi,:)+offset,Z(xi,:),'-k');
            g(2) = plot3(a,X(xi,:),Y(xi,:)-offset,Z(xi,:),'-k');
        else
            g(1) = plot3(X(xi,:),Y(xi,:),Z(xi,:),'-k');
        end
        set(g,'LineWidth',1)
    end
end
