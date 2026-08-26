function Data=NACA_Panel_Maker(pts,NACA)
global lib_path
% This function returns a given number of critical points
% for a given airfoil NACA designation.

% Recently added dependency on naca456 program by Ralph Carmichael

%Collect NACA Designation
n=1000; %precision of airfoil surface before interpolation
c=1;    %chord length

%Solve for 4-Digit and 5-Digit Series
if length(NACA)<6   %Not a 6-Series
    if length(NACA)==4  %4-Digit Designation
        %Given Values
        m=str2double(NACA(1))*c/100;    %maximum ordinate of mean line, camber
        p=str2double(NACA(2))*c/10;     %chordwise position of m
        t=str2double(NACA(3:4))*c/100;  %max thickness
        LE_slope=2*m/p;
        if p==0
            LE_slope=0;
            p=0.25;
        end
        %Camber Line and Camber Slope
        x1=linspace(0,p,n);
        y1=(m/p^2)*(2*p*x1-x1.^2);              %camber or mean line forward of m
        theta1=atan((m/p^2)*(2*p-2*x1));
        x2=linspace(p+0.1/n,c,n);
        y2=(m/(1-p)^2)*((1-2*p)+2*p*x2-x2.^2);  %camber line aft of m
        theta2=atan((m/(1-p)^2)*(2*p-2*x2));
        x=[x1,x2];
        
    elseif length(NACA)==5     %5-Digit Designation
        %Given Values
        switch str2double(NACA(1:3))
            case 210
                m=0.058*c;
                k=361.4;
            case 220
                m=0.126*c;
                k=51.64;
            case 230
                m=0.2025*c; %maximum ordinate of mean line, camber
                k=15.957;   %constant
            case 240
                m=0.29*c;
                k=6.643;
            case 250
                m=0.391*c;
                k=3.23;
        end
        p=c*str2double(NACA(2:3))/200;  %chordwise position of m
        t=c*str2double(NACA(4:5))/100;  %max thickness
        LE_slope=(k/6)*m^2*(3-m);
        
        %Camber Line Calculation
        x1=linspace(0,p,n);  %before m
        y1=(k/6)*(x1.^3-3*m*x1.^2+m^2*(3-m)*x1); %camber or mean line forward of m
        dy1_dx=(k/6)*(3*x1.^2-6*m*x1+m^2*(3-m)); %d/dx(camber line) forward
        theta1=atan(dy1_dx);
        x2=linspace(m+0.1/n,c,n);  %after m
        y2=(k/6)*m^3*(1-x2);    %camber line aft of m
        dy2_dx=-(k/6)*m^3;      %d/dx(camber line) aft
        theta2=atan(dy2_dx);
        x=[x1,x2];
    end
    
    %Surface Calculation
    y_t=(t/0.2)*(0.29690*sqrt(x)-0.126*x-0.35160*x.^2+0.2843*x.^3-0.1015*x.^4);
    if LE_slope==0  %if symmetric, surface is simply the thickness distribution
        x_upper=x;
        y_upper=y_t;
        x_lower=x;
        y_lower=-y_t;
    else            %if cambered, thickness distribution is taken perpendicular to camber line
        x_upper=[x(1:n)-y_t(1:n).*sin(theta1),x(n+1:end)-y_t(n+1:end).*sin(theta2)];
        y_upper=[y1+y_t(1:n).*cos(theta1),y2+y_t(n+1:end).*cos(theta2)];
        x_lower=[x(1:n)+y_t(1:n).*sin(theta1),x(n+1:end)+y_t(n+1:end).*sin(theta2)];
        y_lower=[y1-y_t(1:n).*cos(theta1),y2-y_t(n+1:end).*cos(theta2)];
    end
    
else    %6-Series Designation
    
    %if ~exist('NACA456/naca456', 'file') == 2
    %    a=str2double(inputdlg('Uniform Load Distribution, a, from 0 to 1'));
    %    if strcmp(NACA(3),'A')   %A series (straight trailing edge)
    %
    %    else
    %        %Given Values
    %        m=NACA(2);   %location of min. pressure
    %        cl=NACA(4);  %Cl_i or Cl design
    %        t=NACA(5:6); %max thickness
    %
    %        %Camber Line Calculation
    %        xc=linspace(0,c,2*n); %dimensional position
    %        x=xc/c;              %chordwise position
    %        g=-1/(1-a)*(a^2*(log(a)/2-1/4)+1/4);
    %        h=1/(1-a)*((1-a)^2*log(1-a)/2-(1-a)^2/4)+g;
    %        z=(a-x).^2*log(abs(a-x))/2-(1-x).^2*log(1-x)/2+(1-x).^2/4-(a-x).^2/4;
    %        y=cl/(2*pi*(a+1))*(1/(1-a)*z-x*log(x)+g-h*x);
    %
    %        %
    %        plot(xc,y)
    %    end
    
    % This method has the potential to obtain ordinates for 4-digit modified 
    % and 5-digit modified airfoils and way more options with 6-series inputs.
    current_path = pwd;
    %cd NACA456
    cd(fullfile(lib_path,'NACA456'))
    fid = fopen('naca.in','wt');
    fprintf(fid,'$NACA\n');
    fprintf(fid,'NAME=''NACA %s'',\n',NACA);
    if ~isempty(strfind(NACA,'A'))
        fprintf(fid,'PROFILE=''%sA'',\n',NACA(1:2));
        fprintf(fid,'CAMBER=''%sM'',\n',NACA(1));
    else
        fprintf(fid,'PROFILE=''%s'',\n',NACA(1:2));
        fprintf(fid,'CAMBER=''%s'',\n',NACA(1));
    end
    fprintf(fid,'TOC=%.2f,\n',str2double(NACA(end-1:end))/100);
  	fprintf(fid,'CL=%.1f,\n',str2double(NACA(end-2))/10);
    fprintf(fid,'DENCODE=3,\n');
    fprintf(fid,'/\n');
    fclose(fid);
    if ispc
        system('naca456');
    else
        setenv('DYLD_LIBRARY_PATH', '/usr/local/bin:/opt/local/lib:')
        system('./naca456');
    end
    fprintf('\n')
    check = dir('naca.gnu');
    if check.bytes
        data = dlmread('naca.gnu');
        cd(current_path)
    else
        warndlg(['Error generating ordinates for NACA ',NACA]), Data = []; 
        cd(current_path)
        return
    end
    le = floor(length(data)/2);
    x_upper = data(1:le,1);
    y_upper = data(1:le,2);
    x_lower = flipud(data(le+1:end,1));
    y_lower = flipud(data(le+1:end,2));
end

%Choose x values using cosine spacing
angle=linspace(0,pi,floor(pts/2)+1);
x_new=.5-cos(angle)/2;
y_upper=interp1(x_upper,y_upper,x_new,'Linear','extrap');
y_lower=interp1(x_lower,y_lower,x_new,'Linear','extrap');

%Output coordinates to main code
x=[fliplr(x_new),x_new(2:end)]';
y=[fliplr(y_lower),y_upper(2:end)]';
Data=[x,y];
% %close trailing edge
% Data(1,:)=[1,0];
% Data(end,:)=[1 0];

