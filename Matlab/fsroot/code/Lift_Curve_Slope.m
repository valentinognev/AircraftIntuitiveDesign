%2-D Aerodynamic Parameters
%Zachary Lietzau

function PT=Lift_Curve_Slope(PT,n)
global AERO_In

%NACA Input
if length(PT.NACA{n})==6
    airfoil = str2double(PT.NACA{n}([1:2,4:end]));
else
    airfoil = str2double(PT.NACA{n});
end
if length(PT.NACA{n})>3 && ~isnan(airfoil) && airfoil
    Data = NACA_Panel_Maker(120,PT.NACA{n});
    if ~isempty(Data), PT.DATA{n} = Data; else, return, end
    name=sprintf('Airfoil Analysis: NACA %s',PT.NACA{n});
    PT.TC = max(Data(:,2))-min(Data(:,2));
else
    if length(PT.DATA)>=n, Data = PT.DATA{n}; end %adding tip airfoil data
    if ~strcmp(PT.NACA{n},'Data.'),[Data,PT.NACA{n}]=Panel_Points(PT,n);end
    if length(Data)>3
        PT.DATA{n} = Data;
        if ispc, path_brk='\'; else, path_brk = '/'; end %PC uses \ in path
        i1=strfind(PT.NACA{n},path_brk); i2=strfind(PT.NACA{n},'.');
        if ~isempty(i1) && ~isempty(i2)                 %airfoil
            Airfoil = PT.NACA{n}(i1(end)+1:i2-1);
        else
            Airfoil = 'Specified Geometry';
        end
        PT.TC = max(Data(:,2))-min(Data(:,2));
        name = ['Airfoil Analysis: ',Airfoil];
        %Airfoil = 'Points.';
    end
end

%Estimate Aero Parameters
if length(Data)>3

    %Number of panels (number of points-1)
    N=length(Data)-1; %if mod(N,2), N=N-1; Data(end,:)=[]; end
    
    %Autocorrect improper data inputs
    if sum(Data(1:N/2,2))>sum(Data(N/2+1:N,2))  %counter-clockwise data
        Data=flipud(Data);
    elseif sum(isnan(Data))>0   %corrects most data from airfoiltools.com
        stop=find(isnan(Data),1);
        Data(stop,:)=[];    %remove NaN
        Data(1:stop-1,:)=flipud(Data(1:stop-1,:));
        Data(stop,:)=[];    %remove repeat LE point
        Data=flipud(Data);
        N=N-2;
    end
    
    %Only an even number of panels (odd number of points) can be used
    if mod(N,2)  %if the number of panels is odd
        LE=find(Data(:,1)==0); %remove duplicate LE points
        if length(LE)>1
            Data(LE(2:end),:)=[];
        elseif LE<N/2 %less points on top
            Data(end-1,:)=[];   %removes an extra TE point if needed
        else
            Data(2,:)=[];
        end
        N=N-1;
    end

%     %Add Points
%     le = N/2;
%     x_upper = flipud(Data(1:le,1));
%     y_upper = flipud(Data(1:le,2));
%     x_lower = Data(le:end,1);
%     y_lower = Data(le:end,2);
%     
%     %Choose x values using cosine spacing
%     angle=linspace(0,pi,floor(200/2)+1);
%     x_new=.5-cos(angle)/2;
%     y_upper=interp1(x_upper,y_upper,x_new,'spline','extrap');
%     y_lower=interp1(x_lower,y_lower,x_new,'spline','extrap');
%     
%     %Output coordinates to main code
%     x=[fliplr(x_new),x_new(2:end)]';
%     y=[fliplr(y_lower),y_upper(2:end)]';
%     Data=[x,y]; N = length(x)-1;
    
    %Given angle of attack and setting free-stream velocity to 1
    input=get(AERO_In(1),'String');
    index=strfind(input,',');
    index2=strfind(input,':');
    if isempty(index)&&isempty(index2)
        Alpha=str2double(input);
    elseif isempty(index)
        Alpha=evalin('base',input);
    else
        j=1; Alpha = zeros(length(index));
        for i=1:length(index)
            Alpha(i)=str2double(input(j:index(i)));
            j=index(i);
        end
        Alpha(i+1)=str2double(input(j:end));
    end
    Alpha=Alpha*pi/180;  %radians
    
    %Send to 2-D Vortex Panel Method
    PT.DATA{n} = Data;
    if length(Alpha)>1
        [PT.a0(n),PT.alpha0(n),PT.Cm_ac(n)] = Panel_Method(Data,N,Alpha,name);
    else
        [Cl,x_cp,Cm_ac] = Panel_Method(Data,N,Alpha,name);
    end
    
elseif Data(1)>0
    
    PT.a0(n) = Data(1);
    PT.alpha0(n) = Data(2);
    PT.Cm_ac(n) = Data(3);
    
end

end