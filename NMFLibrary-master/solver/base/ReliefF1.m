%������
clear;clc;
load('data.data');
D=data(:,2:size(data,2));
m =80 ;%��������
k = 8;
N=20;%���д���
for i =1:N
    W(i,:) = RelifF (D,m,k);
end
for i = 1:N    %��ÿ�μ����Ȩ�ؽ��л�ͼ,��ͼN�Σ�������Ч��
    plot(1:size(W,2),W(i,:));
    hold on ;
end
for i = 1:size(W,2)  %����N���У�ÿ�����Ե�ƽ��ֵ
    result(1,i) = sum(W(:,i))/size(W,1) ;
end
xlabel('���Ա��');
ylabel('����Ȩ��');
title('ReliefF�㷨�������ٰ����ݵ�����Ȩ��');
axis([1 10 0 0.3])
%------- ����ÿһ�ֵ����Ա仯����
xlabel('�������');
ylabel('����Ȩ��');
name =char('����','ϸ����С������','ϸ����̬������','��Եճ����','����Ƥϸ���ߴ�','���','BlandȾɫ��','��������','�˷���');
name=cellstr(name);

for i = 1:size(W,2)
    figure
    plot(1:size(W,1),W(:,i));
    xlabel('�������') ;
    ylabel('����Ȩ��') ;
    title([char(name(i))  '(����' num2Str(i) ')������Ȩ�ر仯']);
end