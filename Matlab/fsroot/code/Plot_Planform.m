%Plot Wing, Horizontal Tail, or Vertical Tail
function [h,g,PT] = Plot_Planform(PT,type,a,ni,nj,option,choice,h)
global F A E R BD HT VT

%Check Plot Option
g=[]; %handle for line objects (for highlighting selection)
if nargin<8, h=[]; end
if nargin<7, choice=''; dot = []; else, dot = strfind(choice,'.'); end
if nargin>5 && length(option)==1 && option, angle = 1; else, angle = 0; end

%Correct VT Position and Break Definition
if ~isempty(strfind(type,'vt'))||strcmp(type,'prop')
    offset = PT.Y; PT.Y = PT.Z; PT.Z = offset;
end

%Extract Parameters
if isfield(PT,'CHRDBP') && PT.CHRDBP && PT.SSPNOP %break geometry
    
    %Inboard Section
    %SSPN1 = PT.SSPN - PT.SSPNOP;
    if angle
        y_break = PT.SSPNOP*cosd(PT.DHDADI);
        if strcmp(type,'prop'), y_break = y_break*cosd(PT.SAVSI); end
    else
        y_break = PT.SSPNOP;
    end
    y1 = PT.Y+linspace(0,y_break,round(nj*abs(y_break)/PT.SSPN));
    c1 = PT.CHRDR + (y1-PT.Y)/(y1(end)-PT.Y)*(PT.CHRDBP-PT.CHRDR);
    dx1 = PT.X + (y1-PT.Y)*tand(PT.SAVSI) + ...
        PT.CHSTAT*(PT.CHRDR-PT.CHRDBP)*(y1-PT.Y)/(y1(end)-PT.Y);
    dz1 = PT.Z + (y1-PT.Y)*tand(PT.DHDADI);
    jbreak = length(y1);
    
    %Ouboard Section
    if angle
        %full eqn... (PT.SSPN-(PT.SSPNOP-y_break)-y_break)*cosd(PT.DHDADO)
        y_out = y_break+(PT.SSPN-PT.SSPNOP)*cosd(PT.DHDADO);
        if strcmp(type,'prop')
            y_out = y_break+(y_out-y_break)*cosd(PT.SAVSO);
        end
    else
        y_out = PT.SSPN;
    end
    y2 = PT.Y+linspace(y_break,y_out,nj-round(nj*abs(y_break)/PT.SSPN));
    if isempty(y2), y2 = y1(end); end %if plot resolution too coarse
    c2 = PT.CHRDBP + (y2-y2(1))/(y2(end)-y2(1))*(PT.CHRDTP-PT.CHRDBP);
    dx2 = dx1(end) + (y2-y2(1))*tand(PT.SAVSO) + ...
        PT.CHSTAT*(PT.CHRDBP-PT.CHRDTP)*(y2-y2(1))/(y2(end)-y2(1));
    dz2 = dz1(end) + (y2-y2(1))*tand(PT.DHDADO);
    
    %Concatenate
    y = [y1,y2]; c = [c1,c2]; dx = [dx1,dx2]; dz = [dz1,dz2];
    theta = PT.i - (y-PT.Y)/(y(end)-PT.Y)*PT.TWISTA;
    
else %single planform
    
    %Full Section
    if angle
        y_out = PT.SSPN*cosd(PT.DHDADI);
        if strcmp(type,'prop'), y_out = y_out*cosd(PT.SAVSI); end
    else
        y_out = PT.SSPN;
    end
    y = PT.Y + linspace(0,y_out,nj);
    c = PT.CHRDR + (y-PT.Y)/(y(end)-PT.Y)*(PT.CHRDTP-PT.CHRDR);
    dx = PT.X + (y-PT.Y)*tand(PT.SAVSI)+...
        PT.CHSTAT*(PT.CHRDR-PT.CHRDTP)*(y-PT.Y)/(y(end)-PT.Y);
    dz = PT.Z + (y-PT.Y)*tand(PT.DHDADI);
    theta = PT.i - (y-PT.Y)/(y(end)-PT.Y)*PT.TWISTA;
    jbreak=length(y);
    
end

%Variable Chord Test
%c = PT.CHRDR*(sqrt(1-((y-PT.Y)/(y(end)-PT.Y)).^2)) 
%the point is... variable geometries would be easy to plot

%Choose Axis of Rotation
xt = 0.25; %0 for LE
dx = dx+xt*c;
if angle, c = c.*cosd(theta); end 

%Control Surface Interpolation
y0 = linspace(0,PT.SSPN,nj);

%Plot Airfoil
if length(PT.DATA)==1 %uniform airfoil geometry
    
    data=PT.DATA{1};
    if ni<length(data) 
        pts = unique(round(linspace(1,length(data),ni)))';
        data = interp2(data,1:2,pts,'nearest');
    elseif ni>length(data)
        ni = length(data); %not going to perform splinewise interpolation
    end
    LE = ceil(ni/2);
    if mod(ni,2), data(LE+1:end+1,:) = data(LE:end,:); ni = ni+1; end %even
    x = data(:,1);	z = data(:,2);
    X = zeros(ni,nj); Y = X; Z = X;
    
 	%Map Planform Geometry
    for j=1:nj
        X(:,j) = (x-xt)*c(j)+dx(j);
        Y(:,j) = y(j);
        Z(:,j) = z*c(j)+dz(j)+(xt-x)*tand(theta(j))*c(j);
    end
    
elseif length(PT.DATA)==2 %varying airfoil geometry
    
    data1 = PT.DATA{1};
    data2 = PT.DATA{2};
    if ni<min([length(data1),length(data2)])
        pts1 = unique(round(linspace(1,length(data1),ni)))';
        data1 = interp2(data1,1:2,pts1,'nearest');
        pts2 = unique(round(linspace(1,length(data2),ni)))';
        data2 = interp2(data2,1:2,pts2,'nearest');
    else 
        if length(data1)>length(data2)
            ni = length(data2); 
            pts1 = unique(round(linspace(1,length(data1),ni)))';
            data1 = interp2(data1,1:2,pts1,'nearest');
        elseif length(data2)>length(data1)
           	ni = length(data1); 
            pts2 = unique(round(linspace(1,length(data2),ni)))';
            data2 = interp2(data2,1:2,pts2,'nearest');
        end
    end
    LE = ceil(ni/2);
    if mod(ni,2) %make even
        data1(LE+1:end+1,:) = data1(LE:end,:); 
        data2(LE+1:end+1,:) = data2(LE:end,:); 
        ni = ni+1;
    end 
    x1 = data1(:,1);	z1 = data1(:,2);
    x2 = data2(:,1);	z2 = data2(:,2);
    x = interp1([y(1),y(end)],[x1,x2]',y,'linear')';
    z = interp1([y(1),y(end)],[z1,z2]',y,'linear')';
    X = zeros(ni,nj); Y = X; Z = X;
    
    %Map Planform Geometry
    for j=1:nj
        X(:,j) = (x(:,j)-xt)*c(j)+dx(j);
        Y(:,j) = y(j);
        Z(:,j) = z(:,j)*c(j)+dz(j)+(xt-x(:,j))*tand(theta(j))*c(j);
    end
end

%Tip Cap Geometry (for even number of data points)
XL = X(1:LE,nj); XU = X(LE+1:end,nj); Xtip = [XL,flipud(XU)];
ZL = Z(1:LE,nj); ZU = Z(LE+1:end,nj); Ztip = [ZL,flipud(ZU)];
Ytip = [Y(1:LE,nj),Y(LE+1:end,nj)];

%Tip Cap Geometry (for odd number of data points)
% XL = X(1:LE,nj); XU = X(LE:end,nj); Xtip = [XL,flipud(XU)];
% ZL = Z(1:LE,nj); ZU = Z(LE:end,nj); Ztip = [ZL,flipud(ZU)];
% Ytip = [Y(1:LE,nj),Y(LE:end,nj)];

%Unique Aileron Tips
Xtl = Xtip; Xtr = Xtip;
Ztl = Ztip; Ztr = Ztip;

%Plot Wing
switch type
    
    case 'wing' %%%%%%%%%%%%%%%%%%%%%%%% WING %%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        
        %Flaps
        if max(abs(F.DELTA))
            i=(x(:,1)>(PT.CHRDR-F.CHRDFI)/PT.CHRDR);
            j=(F.SPANFI<y0&y0<=F.SPANFO); j(find(j,1,'first')-1)=1;
            Xf = X(i,j);                Zf = Z(i,j);
            for nj = 1:length(find(j))
                %f defines the chordwise position relative to the hingeline
                f=c(nj)*(X(i,nj)-min(X(i,nj)))/(max(X(:,nj)-min(X(:,nj))));
                dX=f-f*cosd(mean(F.DELTA));     Xf(:,nj) = Xf(:,nj)-dX;
                dZ=f*sind(mean(F.DELTA));       Zf(:,nj) = Zf(:,nj)-dZ;
            end
            if length(h)<5 || ~isgraphics(h(5))
                h(5) = surf(a,Xf,Y(i,j),Zf,'Tag','F');
                h(6) = surf(a,Xf,-Y(i,j),Zf,'Tag','F');
            else
                delete(h), h = [];
                h(5) = surf(a,Xf,Y(i,j),Zf,'Tag','F');
                h(6) = surf(a,Xf,-Y(i,j),Zf,'Tag','F');
                %set(h(5),'XData',Xf,'YData',Y(i,j),'ZData',Zf)
                %set(h(6),'XData',Xf,'YData',-Y(i,j),'ZData',Zf)
            end
            jblank = j; jblank(find(j,1))=0;
            iblank = i; ni=find(i==0); iblank([ni(1)-1;ni;ni(end)+1])=0;
            if j(end) %if flap extends to tip
                Xtip(i(1:LE),:)=Xtip(i(1:LE),:)-[dX(1:end/2),dX(1:end/2)];
                Ztip(i(1:LE),:)=Ztip(i(1:LE),:)-[dZ(1:end/2),dZ(1:end/2)];
            else
                jblank(find(j,1,'last'))=0;
            end
            Xtl = Xtip; Xtr = Xtip;
            Ztl = Ztip; Ztr = Ztip;
            Z(iblank,jblank)=nan;
        end
        
        %Ailerons
        if max(abs(A.DELTAL)) || max(abs(A.DELTAR))
            i=(x(:,1)>(PT.CHRDR-A.CHRDFI)/PT.CHRDR);
            j=(A.SPANFI<y0&y0<=A.SPANFO); j(find(j,1,'first')-1)=1;
            Xal=X(i,j);   Xar=X(i,j);   Zal=Z(i,j);   Zar=Z(i,j);
            for nj = 1:length(find(j))
                f=c(nj)*(X(i,nj)-min(X(i,nj)))/(max(X(:,nj)-min(X(:,nj))));
                dXl=f-f*cosd(mean(A.DELTAL)); dXr=f-f*cosd(mean(A.DELTAR));
                Xal(:,nj) = Xal(:,nj)-dXl;      Xar(:,nj) = Xar(:,nj)-dXr;
                dZl=f*sind(mean(A.DELTAL));     dZr=f*sind(mean(A.DELTAR));
                Zal(:,nj) = Zal(:,nj)-dZl;      Zar(:,nj) = Zar(:,nj)+dZr;
            end
            if length(h)<7 || ~isgraphics(h(7))
                h(7) = surf(a,Xar,Y(i,j),Zar,'Tag','A');
                h(8) = surf(a,Xal,-Y(i,j),Zal,'Tag','A');
            else
                delete(h), h = [];
                h(7) = surf(a,Xar,Y(i,j),Zar,'Tag','A');
                h(8) = surf(a,Xal,-Y(i,j),Zal,'Tag','A');
                %set(h(7),'XData',Xf,'YData',Y(i,j),'ZData',Zf)
                %set(h(8),'XData',Xf,'YData',-Y(i,j),'ZData',Zf)
            end
            jblank = j; jblank(find(j,1))=0;
            iblank = i; ni=find(i==0); iblank([ni(1)-1;ni;ni(end)+1])=0;
            if j(end) %if aileron extends to tip
                Xtl(i(1:LE),:)=Xtip(i(1:LE),:)-[dXl(1:end/2),dXl(1:end/2)];
                Ztl(i(1:LE),:)=Ztip(i(1:LE),:)-[dZl(1:end/2),dZl(1:end/2)];
                Xtr(i(1:LE),:)=Xtip(i(1:LE),:)-[dXr(1:end/2),dXr(1:end/2)];
                Ztr(i(1:LE),:)=Ztip(i(1:LE),:)+[dZr(1:end/2),dZr(1:end/2)];
            else
                jblank(find(j,1,'last'))=0;
            end
            Z(iblank,jblank)=nan;
        end
        
        %Plot Surface
        if isempty(h) || h(1)==0
            h(1) = surf(a,X,Y,Z,'Tag','WG');
            h(2) = surf(a,X,-Y,Z,'Tag','WG');
            h(3) = surf(a,Xtr,Ytip,Ztr,'Tag','WGtip');
            h(4) = surf(a,Xtl,-Ytip,Ztl,'Tag','WGtip');
        else
            set(h(1),'XData',X,'YData',Y,'ZData',Z);
            set(h(2),'XData',X,'YData',-Y,'ZData',Z);
            set(h(3),'XData',Xtr,'YData',Ytip,'ZData',Ztr);
            set(h(4),'XData',Xtl,'YData',-Ytip,'ZData',Ztl);
        end
        
        %Plot Selection
        if strcmp(choice(1:dot-1),'WG')
            g = Select(PT,a,X,Y,Z,choice(dot+1:end),jbreak);
        end
        
    case 'wing 2'
        
        %Plot Surface
        if isempty(h) || h(1)==0
            h(1) = surf(a,X,Y,Z,'Tag','NP{1}');
            h(2) = surf(a,X,-Y,Z,'Tag','NP{1}');
            h(3) = surf(a,Xtip,Ytip,Ztr,'Tag','NP{1}tip');
            h(4) = surf(a,Xtip,-Ytip,Ztl,'Tag','NP{1}tip');
     	else
            set(h(1),'XData',X,'YData',Y,'ZData',Z);
            set(h(2),'XData',X,'YData',-Y,'ZData',Z);
            set(h(3),'XData',Xtr,'YData',Ytip,'ZData',Ztr);
            set(h(4),'XData',Xtl,'YData',-Ytip,'ZData',Ztl);
        end
        
        %Plot Selection
        if strcmp(choice(1:dot-1),'NP{1}')
            g = Select(PT,a,X,Y,Z,choice(dot+1:end),jbreak);
        end
        
    case 'ht' %%%%%%%%%%%%%%%%%%%% HORIZONTAL TAIL %%%%%%%%%%%%%%%%%%%%%%%%
        
        %Elevator
        if max(abs(E.DELTA))
            i=(x(:,1)>(PT.CHRDR-E.CHRDFI)/PT.CHRDR);
            j=(E.SPANFI<y0&y0<=E.SPANFO); j(find(j,1,'first')-1)=1;
            Xe = X(i,j);                Ze = Z(i,j);
            for nj = 1:length(find(j))
                f=c(nj)*(X(i,nj)-min(X(i,nj)))/(max(X(:,nj)-min(X(:,nj))));
                dX=f-f*cosd(mean(E.DELTA));     Xe(:,nj) = Xe(:,nj) - dX;
                dZ=-f*sind(mean(E.DELTA));      Ze(:,nj) = Ze(:,nj) + dZ;
            end
            if length(h)<5 || ~isgraphics(h(5))
                h(5) = surf(a,Xe,Y(i,j),Ze,'Tag','E');
                h(6) = surf(a,Xe,-Y(i,j),Ze,'Tag','E');
            else
                delete(h), h = [];
                h(5) = surf(a,Xe,Y(i,j),Ze,'Tag','E');
                h(6) = surf(a,Xe,-Y(i,j),Ze,'Tag','E');
                %set(h(5),'XData',Xe,'YData',Y(i,j),'ZData',Ze);
                %set(h(6),'XData',Xe,'YData',-Y(i,j),'ZData',Ze);
            end
            jblank = j; jblank(find(j,1))=0;
            iblank = i; ni=find(i==0); iblank([ni(1)-1;ni;ni(end)+1])=0;
            if j(end) %if elevator extends to tip
                Xtip(i(1:LE),:)=Xtip(i(1:LE),:)-[dX(1:end/2),dX(1:end/2)];
                Ztip(i(1:LE),:)=Ztip(i(1:LE),:)+[dZ(1:end/2),dZ(1:end/2)];
            else
                jblank(find(j,1,'last'))=0;
            end
            X(iblank,jblank)=nan;
            Z(iblank,jblank)=nan;
        end
        
        %Plot Surface
        if isempty(h) || h(1)==0
            h(1) = surf(a,X,Y,Z,'Tag','HT');
            h(2) = surf(a,X,-Y,Z,'Tag','HT');
            h(3) = surf(a,Xtip,Ytip,Ztip,'Tag','HTtip');
            h(4) = surf(a,Xtip,-Ytip,Ztip,'Tag','HTtip');
        else
          	set(h(1),'XData',X,'YData',Y,'ZData',Z);
            set(h(2),'XData',X,'YData',-Y,'ZData',Z);
            set(h(3),'XData',Xtr,'YData',Ytip,'ZData',Ztr);
            set(h(4),'XData',Xtl,'YData',-Ytip,'ZData',Ztl);
        end

        %Plot Selection
        if strcmp(choice(1:dot-1),'HT')
            g = Select(PT,a,X,Y,Z,choice(dot+1:end),jbreak);
        end
        
    case 'ht 2'
        
        %Plot Surface
        if isempty(h) || h(1)==0
            h(1) = surf(a,X,Y,Z,'Tag','NP{2}');
            h(2) = surf(a,X,-Y,Z,'Tag','NP{2}');
            h(3) = surf(a,Xtip,Ytip,Ztip,'Tag','NP{2}tip');
            h(4) = surf(a,Xtip,-Ytip,Ztip,'Tag','NP{2}tip');
        else
          	set(h(1),'XData',X,'YData',Y,'ZData',Z);
            set(h(2),'XData',X,'YData',-Y,'ZData',Z);
            set(h(3),'XData',Xtr,'YData',Ytip,'ZData',Ztr);
            set(h(4),'XData',Xtl,'YData',-Ytip,'ZData',Ztl);
        end
        
        %Plot Selection
        if strcmp(choice(1:dot-1),'NP{2}')
            g = Select(PT,a,X,Y,Z,choice(dot+1:end),jbreak);
        end
        
    case 'vt' %%%%%%%%%%%%%%%% VERTICAL TAIL / PROPELLER %%%%%%%%%%%%%%%%%%
        
        %Rudder
        if max(abs(R.DELTA))
            i=(x(:,1)>(PT.CHRDR-R.CHRDFI)/PT.CHRDR);
            j=(R.SPANFI<y0&y0<=R.SPANFO); j(find(j,1,'first')-1)=1;
            Xr = X(i,j);                Zr = Z(i,j); Zr2 = Z(i,j);
            for nj = 1:length(find(j))
                f=c(nj)*(X(i,nj)-min(X(i,nj)))/(max(X(:,nj)-min(X(:,nj))));
                dX=f-f*cosd(mean(R.DELTA));     Xr(:,nj) = Xr(:,nj) - dX;
                dZ=f*sind(mean(R.DELTA));       Zr(:,nj) = Zr(:,nj) + dZ;
                if PT.Z, Zr2(:,nj) = Zr2(:,nj) - dZ; end
            end
            if length(h)<5 || ~isgraphics(h(5))
                h(5) = surf(a,Xr,Zr,Y(i,j),'Tag','R');
                if PT.Z, h(6) = surf(a,Xr,-Zr2,Y(i,j),'Tag','R'); end
            else
                set(h(5),'XData',Xr,'YData',Zr,'ZData',Y(i,j));
                if PT.Z, set(h(6),'XData',Xr,'YData',-Zr2,'ZData',Y(i,j)), end
            end
            jblank = j; jblank(find(j,1))=0;
            iblank = i; ni=find(i==0); iblank([ni(1)-1;ni;ni(end)+1])=0;
            if j(end) %if elevator extends to tip
                Xtip(i(1:LE),:)=Xtip(i(1:LE),:)-[dX(1:end/2),dX(1:end/2)];
                Ztip(i(1:LE),:)=Ztip(i(1:LE),:)+[dZ(1:end/2),dZ(1:end/2)];
            else
                jblank(find(j,1,'last'))=0;
            end
            X(iblank,jblank)=nan;
            Z(iblank,jblank)=nan;
        end
        
        %Regular Vertical Tail
        if isempty(h) || h(1)==0
            h(1) = surf(a,X,Z,Y,'Tag','VT');
            h(2) = surf(a,Xtip,Ztip,Ytip,'Tag','VTtip');
        else
          	set(h(1),'XData',X,'YData',Z,'ZData',Y);
            set(h(2),'XData',Xtip,'YData',Ztip,'ZData',Ytip);
        end
        
        %Second Vertical Tail
        if PT.Z || PT.DHDADI || PT.DHDADO
          	if length(h)<4 || h(4)==0
                if length(h)==3, delete(h(3)), end
                h(3) = surf(a,X,-Z,Y,'Tag','VT');
                h(4) = surf(a,Xtip,Ztip-2*PT.Ztip,Ytip,'Tag','VTtip');
            else
                set(h(3),'XData',X,'YData',-Z,'ZData',Y);
                set(h(4),'XData',Xtip,'YData',Ztip-2*PT.Ztip,'ZData',Ytip);
            end
        elseif length(h)==4 && h(3)&& h(4)
            delete(h(3:4)), h(3:4) = [0,0];
        end
        
        %Plot Selection
        if strcmp(choice(1:dot-1),'VT')
            g = Select(PT,a,X,Y,Z,choice(dot+1:end),jbreak,'v');
        end
        
    case 'vt 2'
        
        %Regular Vertical Tail
        if isempty(h) || h(1)==0
            h(1) = surf(a,X,Z,Y,'Tag','NP{3}');
            h(2) = surf(a,Xtip,Ztip,Ytip,'Tag','NP{3}tip');
        else
          	set(h(1),'XData',X,'YData',Z,'ZData',Y);
            set(h(2),'XData',Xtip,'YData',Ztip,'ZData',Ytip);
        end
        
        %Second Vertical Tail
        if PT.Z || PT.DHDADI || PT.DHDADO
          	if length(h)<4
                h(3) = surf(a,X,-Z,Y,'Tag','NP{3}');
                h(4) = surf(a,Xtip,-Ztip,Ytip,'Tag','NP{3}tip');
            else
                set(h(3),'XData',X,'YData',-Z,'ZData',Y);
                set(h(4),'XData',Xtip,'YData',-Ztip,'ZData',Ytip);
            end
        elseif length(h)==4 && h(3)&& h(4)
            delete(h(3:4)), h(3:4) = [0,0];
        end
        
        %Plot Selection
        if strcmp(choice(1:dot-1),'NP{3}')
            g = Select(PT,a,X,Y,Z,choice(dot+1:end),jbreak,'v');
        end
        
    case 'prop'
        
        %Plot Propeller
        Z=Z+PT.X-PT.Z; Ztip=Ztip+PT.X-PT.Z;
        if isempty(h) || h(1)==0
            h(1) = surf(a,Z,    X-PT.X+PT.Z-PT.CHRDR/2,Y);
            h(2) = surf(a,Ztip, Xtip-PT.X+PT.Z-PT.CHRDR/2, Ytip);
            h(3) = surf(a,Z,   -X+PT.X+PT.Z+PT.CHRDR/2,   -Y+2*PT.Y);
            h(4) = surf(a,Ztip,-Xtip+PT.X+PT.Z+PT.CHRDR/2,-Ytip+2*PT.Y);
        else
            set(h(1),'XData',Z,'YData',X-PT.X+PT.Z-PT.CHRDR/2,'ZData',Y);
            set(h(2),'XData',Ztip,'YData',Xtip-PT.X+PT.Z-PT.CHRDR/2,'ZData',Ytip);
            set(h(3),'XData',Z,'YData',-X+PT.X+PT.Z+PT.CHRDR/2,'ZData',-Y+2*PT.Y);
            set(h(4),'XData',Ztip,'YData',-Xtip+PT.X+PT.Z+PT.CHRDR/2,'ZData',-Ytip+2*PT.Y);
        end
        
        %Second Propeller
        if PT.Z
            if length(h)<8
                h(5)=surf(a,Z,    X-PT.X-PT.Z-PT.CHRDR/2,    Y);
                h(6)=surf(a,Ztip, Xtip-PT.X-PT.Z-PT.CHRDR/2, Ytip);
                h(7)=surf(a,Z,   -X+PT.X-PT.Z+PT.CHRDR/2,   -Y+2*PT.Y);
                h(8)=surf(a,Ztip,-Xtip+PT.X-PT.Z+PT.CHRDR/2,-Ytip+2*PT.Y);
            else
                set(h(5),'XData',Z,'YData',X-PT.X-PT.Z-PT.CHRDR/2,'ZData',Y);
                set(h(6),'XData',Ztip,'YData',Xtip-PT.X-PT.Z-PT.CHRDR/2,'ZData',Ytip);
                set(h(7),'XData',Z,'YData',-X+PT.X-PT.Z+PT.CHRDR/2,'ZData',-Y+2*PT.Y);
                set(h(8),'XData',Ztip,'YData',-Xtip+PT.X-PT.Z+PT.CHRDR/2,'ZData',-Ytip+2*PT.Y);
            end
     	elseif length(h)==8 && h(5) && h(6) && h(7) && h(8)
            delete(h(5:8)), h(5:8) = zeros(1,4);
        end
        
        %Tag
        for i=1:length(h), set(h,'Tag','NP{4}'); end
        
    case 'lift' %%%%%%%%%%%%%%%%%%% LIFT DISTRIBUTION %%%%%%%%%%%%%%%%%%%%%
        
        %Aerodynamic Twist
        if length(PT.alpha0L)>1 
            d_alpha = PT.alpha0L(end)-PT.alpha0L(end);
            theta = theta - linspace(0,d_alpha,length(theta));
        end
        
        % Approximate Fuselage Interference 
        % (set inboard chord to 1/2 true root chord)
%         n1 = find(PT.X>BD.X,1,'last');
%         n2 = find((PT.X+PT.CHRDR)<BD.X,1);
%         if ~isempty(n2)
%             if PT.Z<mean(BD.ZU(n1:n2)) && PT.Z>mean(BD.ZL(n1:n2))
%                 yfuse = mean(BD.R(n1:n2)); [yrange,index] = unique(y);
%                 nfuse = interp1(yrange,index,yfuse,'nearest');
%                 c(1:nfuse) = linspace(c(nfuse-1)/2,c(nfuse-1),nfuse);
%             end
%         end
        
        %Calculate Prandtl's Lifting Line
        PT = Lifting_Line(PT,y,c,theta);
        
        %Plot Lift Distribution
        Y = PT.spanwise.y;
        X = ones(length(Y),1)*PT.X+PT.xmac+PT.cbar(end)/4;
        Cl = PT.spanwise.Cl/PT.spanwise.scale*PT.CHRDR;
        Cl_ideal = PT.spanwise.Cl_ideal/PT.spanwise.scale*PT.CHRDR;
        plot3(a,X,Y,PT.Z+Cl,'-b',X,Y,PT.Z+Cl_ideal,'--k')
        
        %Plot Arrows
        ds = 1; color = [0.5,0.6,1];
        X = X(1:ds:length(X));
        Y = Y(1:ds:length(Y));
        Z = ones(length(Y),1)*PT.Z;
        zero = zeros(size(X));
        Cl = Cl(1:ds:length(Cl));
        quiver3(a,X,Y,Z,zero,zero,Cl,'color',color,'AutoScale','off')
        
    case 'downwash' %%%%%%%%%%%%%%%%% DOWNWASH PATH %%%%%%%%%%%%%%%%%%%%%%%
        
        %Plot Vortical Wake
        Z_eta = option(1); Z_w = option(2);
        X_wake=zeros(2,nj); Z_wake=X_wake; ZU_wake=X_wake; ZL_wake=X_wake;
        for j=1:nj
            X_wake(:,j) = [max(X(:,j));BD.X(end)];
            x_pos = X_wake(:,j)-X_wake(1,j);
            Z_wake(:,j) = Z(end,j)+(HT.Z+Z(end,j)-Z_eta)*x_pos/x_pos(end);
            ZU_wake(:,j) = Z_wake(:,j)+Z_w*x_pos/x_pos(end);
            ZL_wake(:,j) = Z_wake(:,j)-Z_w*x_pos/x_pos(end);
        end
        
        %Plot Estimated Wake Limits
        if ~isempty(isnan(X_wake)) && ~isempty(isnan(Z_wake)) && ...
                max(max(abs(Z_wake)))<BD.X(end)/4
            h(1) = surf(a,X_wake,Y(1:2,:),ZU_wake,'facealpha',0.3);
            h(2) = surf(a,X_wake,Y(1:2,:),ZL_wake,'facealpha',0.3);
            h(3) = surf(a,X_wake,-Y(1:2,:),ZU_wake,'facealpha',0.3);
            h(4) = surf(a,X_wake,-Y(1:2,:),ZL_wake,'facealpha',0.3);
        end
        tail_effectiveness = ['\eta_{HT}=',sprintf('%.1f%%',HT.eta*100)];
        text(VT.X-1,0,VT.Z+VT.SSPN/2,tail_effectiveness);
        
end

%Correct VT Position and Break Definition
if ~isempty(strfind(type,'vt'))||strcmp(type,'prop')
    offset = PT.Z; PT.Z = PT.Y; PT.Y = offset;
end

end

function g = Select(PT,a,X,Y,Z,choice,jbreak,type)
%Plot Lines Highlighting Selected Parameter

g = []; %holds disposable plots
[ni,nj] = size(X); le = ni/2+1;
if nargin<8, type = 'h'; end

%Distinguish Selection
xi = 0; xj = 0;
if strcmp(choice,'CHRDR') %root chord
    xj = 1;
elseif (strcmp(choice,'CHRDBP') || strcmp(choice,'SSPNOP')) && PT.SSPNOP %break chord
    xj = jbreak;
elseif strcmp(choice,'CHRDTP') || strcmp(choice,'SSPN') %tip chord
    xj = nj;
elseif strcmp(choice,'CHSTAT') || strcmp(choice,'SAVSI') || strcmp(choice,'SAVSO')
    xi = interp1(X(le:ni,1),le:ni,PT.X+PT.CHRDR*PT.CHSTAT,'nearest','extrap');
    if strcmp(type,'v'), xi = 2*le - xi; end%lower surface
    if PT.SSPNOP && ~strcmp(choice,'CHSTAT')
        if strcmp(choice,'SAVSI'), xj = -jbreak; else, xj = jbreak; end
    end
elseif strcmp(choice,'DHDADI') || strcmp(choice,'DHDADO')
    xi = le;
    if PT.SSPNOP
        if strcmp(choice,'DHDADI'), xj = -jbreak; else, xj = jbreak; end
    end
end

%Plot/Highlight
if ~strcmp(type,'v') %horizontal
    if xi && ~xj
        g(1) = plot3(a,X(xi,:),Y(xi,:),Z(xi,:),'k-');
        g(2) = plot3(a,X(xi,:),-Y(xi,:),Z(xi,:),'k-');
    elseif ~xi && xj
        g(1) = plot3(a,X(:,xj),Y(:,xj),Z(:,xj),'k-');
        g(2) = plot3(a,X(:,xj),-Y(:,xj),Z(:,xj),'k-');
    elseif xi && xj>0
        g(1) = plot3(a,X(xi,xj:end),Y(xi,xj:end),Z(xi,xj:end),'k-');
        g(2) = plot3(a,X(xi,xj:end),-Y(xi,xj:end),Z(xi,xj:end),'k-');
    elseif xi && xj<0
        g(1) = plot3(a,X(xi,1:-xj),Y(xi,1:-xj),Z(xi,1:-xj),'k-');
        g(2) = plot3(a,X(xi,1:-xj),-Y(xi,1:-xj),Z(xi,1:-xj),'k-');
    end
else %vertical
    double = PT.Z || PT.DHDADI || PT.DHDADO;
    if xi && ~xj
        if double
            g(1) = plot3(a,X(xi,:),Z(xi,:),Y(xi,:),'k-');
            g(2) = plot3(a,X(xi,:),-Z(xi,:),Y(xi,:),'k-');
        else
            g(1) = plot3(a,X(xi,:),Z(xi,:),Y(xi,:),'k-');
        end
    elseif ~xi && xj
        if double
            g(1) = plot3(a,X(:,xj),Z(:,xj),Y(:,xj),'k-');
            g(2) = plot3(a,X(:,xj),-Z(:,xj),Y(:,xj),'k-');
        else
            g(1) = plot3(a,X(:,xj),Z(:,xj),Y(:,xj),'k-');
        end
    elseif xi && xj>0
        if double
            g(1) = plot3(a,X(xi,xj:end),Z(xi,xj:end),Y(xi,xj:end),'k-');
            g(2) = plot3(a,X(xi,xj:end),-Z(xi,xj:end),Y(xi,xj:end),'k-');
        else
            g(1) = plot3(a,X(xi,xj:end),Z(xi,xj:end),Y(xi,xj:end),'k-');
        end
    elseif xi && xj<0
        if double
            g(1) = plot3(a,X(xi,1:-xj),Z(xi,1:-xj),Y(xi,1:-xj),'k-');
            g(2) = plot3(a,X(xi,1:-xj),-Z(xi,1:-xj),Y(xi,1:-xj),'k-');
        else
            g(1) = plot3(a,X(xi,1:-xj),Z(xi,1:-xj),Y(xi,1:-xj),'k-');
        end
    end
end

%Line Width and Color
if ~isempty(g), set(g,'LineWidth',1), end

end