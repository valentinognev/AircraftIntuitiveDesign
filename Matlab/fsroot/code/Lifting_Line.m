%Prandtl's Lifting Line Theory
%with Glauert's Fourier Method
function PT = Lifting_Line(PT,y,c,twist)
global AERO ATM AC WG BD

%Collect Known Variables
y0 = y(end); N = length(y);
alpha = AC.alpha(1)*pi/180; 
alpha_0 = (PT.alpha0L(1)-PT.i-twist)*pi/180; %radians
v_inf = AERO.MACH(1)*ATM.a;

%Computational Domain
n = 1:2:2*N-1;  %tip to root
theta = (1:N)'/N*pi/2; y1 = -cos(theta)*y0;
if isfield(PT,'CHRDBP') && PT.CHRDBP && PT.SSPNOP
    [~,index] = unique(y);  y = -y(index);
    theta = theta(index);   y1 = y1(index); 
    N = N-1;                n = n(index);
    alpha_0 = interp1(y,alpha_0(index),y1);
    c = interp1(y,c(index),y1);  
else
    y = -y;
    alpha_0 = interp1(y,alpha_0,y1);
    c = interp1(y,c,y1);  
end
y2 = y(end); dy = zeros(length(y1),1);
for i=1:length(y1)
    dy(i) = y1(i)-y2(i);
    y2(i+1) = y1(i)+dy(i);
end
dy = 2*dy;

%Calculate Coefficients
L = pi*c/(4*y0).*(alpha-alpha_0).*sin(theta);
R = sin(theta*n).*(pi*c*n/(4*y0)+repmat(sin(theta),1,N));
A_ij = R\L;

%Solve for Circulation
gamma = 4*v_inf*y0*sin(theta*n)*A_ij;

%Solve for Lift Distribution and Induced Drag
delta = sum(n(2:end)'.*(A_ij(2:end)/A_ij(1)).^2);
PT.e0 = 1/(1+delta)-0.01;    %planform efficiency factor
PT.e = PT.e0*(1-(max(BD.R)/WG.b)^2);
PT.K = 1/(pi*PT.e*PT.AR(end));   %induced drag coefficient
PT.CL = A_ij(1)*PT.AR(end)*pi;   %estimate component lift

%Distributions
y=[y1;-flipud(y1(1:end-1))];           
dy=[dy;flipud(dy(1:end-1))];
gamma=[gamma;flipud(gamma(1:end-1))];
gamma_ideal = 4*v_inf*y0*A_ij(1)*sin(theta);
gamma_ideal = [gamma_ideal;flipud(gamma_ideal(1:end-1))];

%Write to Part
PT.spanwise.y = y;   
PT.spanwise.dy = dy;  
PT.spanwise.Cl = 2*gamma/(v_inf*WG.S(end));
PT.spanwise.Cl_ideal = 2*gamma_ideal/(v_inf*WG.S(end));
PT.spanwise.scale = max(abs(PT.spanwise.Cl_ideal));

end

