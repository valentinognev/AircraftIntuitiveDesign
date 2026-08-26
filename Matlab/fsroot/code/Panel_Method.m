%2-D Vortex Panel Method
%Zachary Lietzau
function [a0,alpha0,Cm_ac] = Panel_Method(Data,N,Alpha,name,plot_option)
global ax

%Create Figure
if nargin<5, plot_option = 1; end
if plot_option == 1 || plot_option == 3
    res=get(0,'ScreenSize');
    fig=figure('Name',name,'NumberTitle','off','MenuBar','none',...
        'Position',[40,(res(4)-820)/2,res(3)/3,820]);
    ax{7} = [subplot(2,1,2),subplot(2,1,1)];
end

%Initialize Alpha Sweep Arrays
Cl_array = zeros(1,length(Alpha));    Cm_array = Cl_array;
LE_stall = 0;   alpha_stall = 0;

for loop=1:length(Alpha)
    
    %Establish coefficients for flow tangency equation
    [A,B,theta,V,X]=Coefficients(Data,N,Alpha(loop));   %main calculation
    
    %Solve for source and vortex strengths
    Results=A\B;
    Source=Results(1:N);
    Vortex=Results(N+1);
    
    %Induced velocities for panel sources and vortices found in "Coefficients"
    u_source=V{1};
    v_source=V{2};
    u_vortex=V{3};
    v_vortex=V{4};
    
    %Determine tangential velocity for each panel
    C = zeros(N); D = C;
    for i=1:N
        for j=1:N
            C(i,j)=sin(theta(i)-theta(j))*v_source(i,j)+...
                cos(theta(i)-theta(j))*u_source(i,j);
            D(i,j)=sin(theta(i)-theta(j))*v_vortex(i,j)+...
                cos(theta(i)-theta(j))*u_vortex(i,j);
        end
    end
    V=cos(theta-Alpha(loop))+C*Source+sum(D,2)*Vortex;
    
    %Pressure coefficient
    Cp=1-V.^2;
    LE=ceil(N/2)+1;             %leading edge point
    Cp_U=[1;Cp(LE:N)];          %upper surface Cp (starting at 1)
    Cp_L=[1;flipud(Cp(1:LE-1))];%lower surface Cp (starting at 1)
    x=[0,X(LE:N)]';             %begin x at LE
    
    %Plot airfoil and pressure distribution
    if plot_option
        
        hold on
        if length(Alpha)==1
            
            %clear plot
            delete(findall(ax{7},'Type','line'))
            
            %Geometry
            plot(ax{7}(1),Data(:,1),Data(:,2),'-b.','LineWidth',1,'MarkerSize',10);
            ylim(ax{7}(1),[min(Data(:,2))*2,max(Data(:,2))*2])
            xlim(ax{7}(1),[0,1]),title(ax{7}(1),'Airfoil Shape')
            xlabel(ax{7}(1),'x/c'), ylabel(ax{7}(1),'y/c')
            
            %Pressure distribution
            plot(ax{7}(2),x,Cp_U,'b',x,Cp_L,'r','LineWidth',2)
            xlim(ax{7}(2),[0,1]), set(ax{7}(2),'Ydir','reverse')
            title(ax{7}(2),['Pressure Distribution at \alpha = ',num2str(round(Alpha*180/pi,2)),'^{o}'])
            ylabel(ax{7}(2),'Pressure Coefficient, C_{p}')
        else
            %Geometry
            subplot(3,1,3)
            plot(Data(:,1),Data(:,2),'-b.','LineWidth',1,'MarkerSize',10)
            ylim([-0.25,0.25]), title('Airfoil Shape')
            xlabel('x/c'), ylabel('y/c'), xlim([0,1])
            
            %Pressure Distribution
            subplot(3,1,2), plot(x,Cp_U,'b',x,Cp_L,'r','LineWidth',2)
            set(gca,'Ydir','reverse'), title('Pressure Distribution')
            ylabel('Pressure Coefficient, C_{p}'), xlim([0,1]), ylim([-10,1])
        end
    end
    %Break lines into sections
    section=linspace(x(1),x(end),1000);
    dx=section(2)-section(1);
    
    %Interpolate data for each Section
    line1=interp1(x,Cp_L,section);
    line2=interp1(x,Cp_U,section);
    
    %Establish area for integration
    area=line1-line2;
    area_LE=area.*section;
    area_c4=area.*(section-0.25);
    
    %Plot the Measured Area
    %patch([section,fliplr(section)],[line1,fliplr(line2)],'c');
    
    %Lift Coefficient: CL=int(Cp(x)dx)
    Cl=trapz(area)*dx;
    
    %Moment Coefficient: CM=int(-Cp(x)[(x-xref)dx+(y-yref)dy])
    Cm_LE=-trapz(area_LE)*dx;
    Cm_c4=-trapz(area_c4)*dx;
    
    %Calculate center of pressure and aerodynamic center
    x_cp=-Cm_LE/Cl;
    
    %Iterative Results
    Cl_array(loop)=Cl;
    Cm_array(loop)=Cm_c4;
    
    %Predict LE separation (Minimum Cp method)
    if min(Cp)<-11, LE_stall=1; alpha_stall=Alpha(loop)*180/pi; break, end
    
    %Estimate turbulent separation (Stratford's Criterion)
    %     Vu=V(LE:N); rec=Cp_U==max(Cp_U); %beginning of turbulent recovery
    %     Cp_prime=1-(Vu/max(Vu)).^2; %canonical pressure distribution
    %     dx=x(2:end)-x(1:end-1);
    %     dCp_dx=(Cp_U(2:end)-Cp_U(1:end-1))./dx;
    %     dCp_dx2=(dCp_dx(2:end)-dCp_dx(1:end-1))./dx(1:end-1);
    %     k = zeros(size(dCp_dx2)); k(dCp_dx2<=0)=0.35; k(dCp_dx2>0)=0.39;
    %     x_prime=sum((Vu(1:rec)/max(Vu)).^3.*dx(1:rec)) + x - x(rec);
    %     Re=ATM.D*max(Vu)*x_prime/ATM.V;
    %     size(Cp_prime)
    %     size(x_prime)
    %     size(dCp_dx)
    %     left = Cp_prime.*sqrt(abs(x_prime(1:end-1).*dCp_dx));
    %     right = k.*(Re(2:end-1)/1E6).^0.1;
    %     find(Cp_prime>4/7,1,'first')
    
    
end

if length(Alpha)>1
    
    %Calculate Iterative Results
    a0=polyfit(Alpha(1:loop-1),Cl_array(1:loop-1),1); a0=a0(1);
    Cm_ac=mean(Cm_array);
    alpha0=interp1(Cl_array(1:loop-1),Alpha(1:loop-1),0,...
        'Linear','extrap')*180/pi;
    
    Alpha=Alpha*180/pi; Alpha_lim=[min(Alpha),max(Alpha)];
    if ~alpha_stall, alpha_stall=max(Alpha); end
    Alpha_est=[min(Alpha),alpha_stall]; %linspace(min(Alpha),alpha_stall);
    Cl_est=a0*pi/180*(Alpha_est-alpha0);
    if alpha_stall
        Cl_max=Cl_array(find(Cl_array,1,'last'));
    else
        Cl_max=Cl_array(end);
    end
    Cl_lim=[Cl_est(1),1.25*Cl_max];
    
    if plot_option
        subplot(3,1,1)
        plot(Alpha_lim,[0,0],'k',[0,0],Cl_lim,'k',...
            Alpha,Cl_array,'*r',Alpha_est,Cl_est,'b')
        xlim(Alpha_lim),ylim(Cl_lim)
        xlabel('Alpha (deg)'),ylabel('Cl'),title('Lift Curve Slope')
        
        %Plot Stall Prediction
        if LE_stall
            hold on
            plot(Alpha_lim,[Cl_max,Cl_max],'--k')
            text(alpha_stall/2-4,Cl_max+0.13,'Leading Edge Stall')
        end
        
        %Print Results
        String=[sprintf('a_0............%.3f (per rad)\n',a0),...
            sprintf('a_0............%.3f (per deg)\n',a0*pi/180),...
            sprintf('alpha0.......%.2f (deg)\n',alpha0),...
            sprintf('Cm_ac...........%.4f\n',Cm_ac)];
        Results=msgbox(String,'Results');
        axes=get(Results,'CurrentAxes');
        str=get(axes,'Children');
        set(str,'FontSize',10);
        waitfor(Results)
        if ishandle(fig), close(fig); end
    end
    
else
    
    if plot_option == 1
        %Diplay Single Case
        String=[sprintf('Cl.........................%.3f\n',Cl),...
            sprintf('Cm_LE...............%.3f\n',Cm_LE),...
            sprintf('Cm_ac................%.3f\n',Cm_c4),...
            sprintf('x_cp.....................%.3f\n',x_cp)];
        Results=msgbox(String,'Results');
        axes=get(Results,'CurrentAxes');
        str=get(axes,'Children');
        set(str,'FontSize',10);
        waitfor(Results)
        if ishandle(fig), close(fig); end
    end
    a0=Cl; alpha0=x_cp; Cm_ac=Cm_c4;
    %WG.TC=max(Data(:,2))-min(Data(:,2));    WG.DATA=Data;
end

if plot_option == 1, waitfor(fig), elseif plot_option == 2, pause(0.1), end

end