function [Data,Airfoil]=Panel_Points(PT,n)
global lib_path
% Data input options:
% 1) Text or Excel file
% 2) Type or paste values directly (works with airfoiltools.com)
% 3) Input aerodynamic parameters directly

Airfoil = PT.NACA{n};
if ispc, i1=strfind(Airfoil,'\'); else, i1=strfind(Airfoil,'/'); end
i2 = strfind(Airfoil,'.');
if isempty(i1) %search for airfoil data file
    file = dir(fullfile(lib_path,'Airfoils',[Airfoil,'.*']));
    if isempty(file), file = dir(fullfile(lib_path,'Airfoils',[upper(Airfoil),'.*'])); end
    if ~isempty(file)
        Airfoil = fullfile(file(1).folder,file(1).name);
    end
    if ispc, i1=strfind(Airfoil,'\'); else, i1=strfind(Airfoil,'/'); end
    i2 = strfind(Airfoil,'.');
end
if isempty(i1) && isempty(i2)
    choice=questdlg('How would you like to define your airfoil?',...
        'Data Input','Data File','Input Points',...
        'Input Aero Parameters','Input Aero Parameters');
elseif strcmp(Airfoil,'Defined.')
    choice = 'Input Aero Parameters';
elseif strcmp(Airfoil,'Type_pts.')
    choice = 'Input Points';
elseif strcmp(Airfoil,'Load_pts.')
    choice='Data File'; i1=[]; i2=[];
else
    choice='Data File';
end

switch choice
    case 'Data File' %load a text or excel file containing the points
        if isempty(i1) && isempty(i2)
            %if exist('Airfoils','dir'), cd Airfoils, fl = 1; else, fl = 0; end
            [File,Path]=uigetfile({'*.txt;*.dat;*.shp;*.xlsx',...
                'All Data Files';'*.txt','Text File';'*.dat',...
                'Data File';'*.shp','Shape File';'*.xlsx','Excel File'},...
                'Choose Airfoil Data File',fullfile(lib_path,'Airfoils'));
            Airfoil = [Path,File]; %if fl, cd .., end
            if isempty(Airfoil), Data = 0; Airfoil = ''; return, end
        end
        if ~isempty(regexpi(Airfoil,'.txt','once'))||...
                ~isempty(regexpi(Airfoil,'.dat','once'))
            Data=dlmread(Airfoil);
        elseif ~isempty(regexpi(Airfoil,'.shp','once'))
            fid=fopen(Airfoil); fgetl(fid);
            CData=textscan(fid,'%f\t%f');
            Data(:,1)=CData{1}; Data(:,2)=CData{2};
        elseif ~isempty(regexpi(Airfoil,'.xlsx','once'))
            Data=xlsread(Airfoil);
        end
            
    case 'Input Points' %user types or pastes individual points
        
        prompt=sprintf('Enter the points in the format "x y"');
        strmat=cell2mat(inputdlg(prompt,'Points',25));
        Data = zeros(length(strmat),2);
        for k=1:size(strmat,1)          %retrieve data line by line
            str=strtrim(strmat(k,:));   %remove any unwanted spaces
            id=find(str==' ',1);        %delimeter between x and y
            Data(k,:)=[str2double(str(1:id-1)),...
                str2double(str(id+1:end))];
        end
        if isempty(strmat), Data = zeros(1,3); end
        Airfoil = 'Points.';
        
    case 'Input Aero Parameters' %user inputs a0, alpha0, Cm_ac
        prompt = {'2-D Lift Curve Slope','Alpha_0L (deg)', 'Cm_ac'};
        %default = {'2*pi','-2','-0.06'};
        default = {num2str(PT.a0(n)),num2str(PT.alpha0(n)),num2str(PT.Cm_ac(n))};
        vals = inputdlg(prompt,'Aero Parameters',1,default);
        a0 = eval(vals{1}); if a0<0, a0 = a0*180/pi; end %correct /deg
        alpha_0 = str2double(vals{2});
        Cm_ac = str2double(vals{3});
        Data = [a0,alpha_0,Cm_ac];
        Airfoil = 'Defined.';
    otherwise
        Data = 0;
        Airfoil = '';
end

end