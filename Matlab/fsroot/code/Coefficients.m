function [A,B,theta,V,X,Y]=Coefficients(Data,N,alpha)

%Pull x and y coordinates from data array
x=Data(:,1);
y=Data(:,2);

%Initialize Arrays
X = zeros(1,N); Y = X;
theta = zeros(N,1);      
r = zeros(N);   beta = X;
u_source = r;   v_source = r;
u_vortex = r;   v_vortex = r;
A_ij = r;       A_iN1 = r;
A_N1j = r;      A_N1N1 = r;

for i=1:N
    %Position of panel i
    X(i)=(x(i)+x(i+1))/2;   %X defined at panel's center
    Y(i)=(y(i)+y(i+1))/2;   %Y defined at panel's center
    
    for j=1:N
        %Angle subtended by x-axis (calculated once for each panel)
        if i==1
            theta(j,1)=atan2(y(j+1)-y(j),x(j+1)-x(j));
        end
        
        %Position of j relative to i
        r(i,j)=sqrt((X(i)-x(j))^2+(Y(i)-y(j))^2);   %distance from node j to panel i
        r(i,j+1)=sqrt((X(i)-x(j+1))^2+(Y(i)-y(j+1))^2);
        if i==j
            beta(i,j)=pi;   %angle subtended at (X(i),Y(i)) by panel j
        else
            beta(i,j)=atan2((Y(i)-y(j+1))*(X(i)-x(j))-(X(i)-x(j+1))*(Y(i)-y(j)),... %atan2 is the 4 quadrant atan (-pi,pi)
                (X(i)-x(j+1))*(X(i)-x(j))+(Y(i)-y(j+1))*(Y(i)-y(j))); %it is equivalent to 2*atan(y/(sqrt(x^2+y^2)+x))
        end
        
        %Calculate the velocity components along panel-fixed axes
        u_source(i,j)=-log(r(i,j+1)/r(i,j))/(2*pi);
        v_source(i,j)=beta(i,j)/(2*pi);
        u_vortex(i,j)=v_source(i,j);
        v_vortex(i,j)=-u_source(i,j);
        
        %Determine useful coefficients for flow tangency equation
        A_ij(i,j)=-sin(theta(i)-theta(j))*u_source(i,j)+cos(theta(i)-theta(j))*v_source(i,j);
        A_iN1(i,j)=cos(theta(i)-theta(j))*v_vortex(i,j)-sin(theta(i)-theta(j))*u_vortex(i,j);
        if i==1||i==N
            A_N1j(i,j)=sin(theta(i)-theta(j))*v_source(i,j)+cos(theta(i)-theta(j))*u_source(i,j);
            A_N1N1(i,j)=sin(theta(i)-theta(j))*v_vortex(i,j)+cos(theta(i)-theta(j))*u_vortex(i,j);
        end
    end
end

%Establish coefficients for system of linear equations (Ax=B)
%A is the N+1 by N+1 matrix of coefficients
A_iN1=sum(A_iN1,2);
A_N1j=sum(A_N1j,1);
A_N1N1=sum(sum(A_N1N1));
A=[A_ij,A_iN1;A_N1j,A_N1N1];
%B is the N+1 element column vector on the right side of the equation
b_i=sin(theta-alpha);
b_n1=-(cos(theta(1)-alpha)+cos(theta(N)-alpha));
B=[b_i;b_n1];

%V is a cell array with the source and sink velocities for each panel
V={u_source,v_source,u_vortex,v_vortex};

end