%Relief����ʵ��
%DΪ�����ѵ������,���뼯��ȥ�������Ϣ��Ŀ;kΪ�������������
function W = ReliefF (D,m,k);
Rows = size(D,1) ;%��������
Cols = size(D,2) ;%��������,������������
����type2 = sum((D(:,Cols)==2))/Rows ;
����type4 = sum((D(:,Cols)==4))/Rows ;
����%�Ƚ����ݼ���Ϊ2�࣬���Լӿ�����ٶ�
����D1 = zeros(0,Cols) ;%��һ��
����D2 = zeros(0,Cols) ;%�ڶ���
����for i = 1:Rows
����    if D(i,Cols)==2
����        D1(size(D1,1)+1,:) = D(i,:) ;
����    elseif D(i,Cols)==4
����        D2(size(D2,1)+1,:) = D(i,:) ;
����    end
����end
����W =zeros(1,Cols-1) ;%��ʼ������Ȩ�أ���0
����for i = 1 : m  %����m��ѭ��ѡ�����
����   %��D�����ѡ��һ������R
����    [R,Dh,Dm] = GetRandSamples(D,D1,D2,k) ;
����    %��������Ȩ��ֵ
����    for j = 1:length(W) %ÿ�������ۼ�һ�Σ�ѭ��
����        W(1,j)=W(1,j)-sum(Dh(:,j))/(k*m)+sum(Dm(:,j))/(k*m) ;%���չ�ʽ����Ȩ��
����    end
����end