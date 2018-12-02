%% Florida map creation

%% Setup

clear
% close all
clc

%% Load in image

Im = imread('carib_map.png');
Im = Im(1:end-175,125:end-70,:);
features = pic2points(Im,0.547,1,1000);
close all
points = features'/30;
points = round(points,1);

figure
g = scatter(points(1,:),points(2,:),'.');
% g.SizeData = 12;
h = gca;
% h.XTick = -30:0.1:30;
% h.YTick = -30:0.1:30;
grid on
axis equal
% xlim([0,12])
% ylim([0,9])


%% Add cities

cities = zeros(2,10);
city_names = cell(1,10);
% Jacksonville
cities(1,1) = 3.7;
cities(2,1) = 7.8;
city_names{1} = 'jacksonville';
% Miami
cities(1,2) = 4.6;
cities(2,2) = 5.3;
city_names{2} = 'miami';
% Tampa
cities(1,3) = 3.3;
cities(2,3) = 6.3;
city_names{3} = 'tampa';
% Orlando
cities(1,4) = 3.8;
cities(2,4) = 6.8;
city_names{4} = 'orlando';
% St. Petersburg
cities(1,5) = 3.2;
cities(2,5) = 6.0;
city_names{5} = 'st. petersburg';
% % Hialeah
cities(1,6) = 4.5;
cities(2,6) = 5.4;
city_names{6} = 'haileah';
% Tallahassee
cities(1,7) = 2.3;
cities(2,7) = 7.8;
city_names{7} = 'tallahassee';
% Port St. Lucie
cities(1,8) = 4.4;
cities(2,8) = 6.0;
city_names{8} = 'port st.lucie';
% Cape Coral
cities(1,9) = 3.5;
cities(2,9) = 5.7;
city_names{9} = 'cape coral';
% Fort Lauderdale
cities(1,10) = 4.6;
cities(2,10) = 5.5;
city_names{10} = 'fort lauderdale';
% Pensacol
cities(1,11) = 0.9;
cities(2,11) = 7.8;
city_names{11} = 'pensacola';
% Key Largo
cities(1,12) = 4.4;
cities(2,12) = 4.7;
city_names{12} = 'key largo';
% Key West
cities(1,13) = 3.5;
cities(2,13) = 4.4;
city_names{13} = 'key west';

% Remove cities: Hialeah
cities(:,6) = [];
city_names(6) = [];
rm_count = 1;
cities(:,12-rm_count) = [];
city_names(12-rm_count) = [];

hold on
plot(cities(1,:),cities(2,:),'k.','MarkerSize',9)


%% Plot bounding boxes

% Florida
fl_1(:,1) = [0.7,3.9];
fl_1(:,2) = [7.3,8.1];
plot([fl_1(1,1),fl_1(1,1)],[fl_1(1,2),fl_1(2,2)],'r')
plot([fl_1(1,1),fl_1(2,1)],[fl_1(1,2),fl_1(1,2)],'r')
plot([fl_1(1,1),fl_1(2,1)],[fl_1(2,2),fl_1(2,2)],'r')
plot([fl_1(2,1),fl_1(2,1)],[fl_1(1,2),fl_1(2,2)],'r')

fl_2(:,1) = [3.1,4.6];
fl_2(:,2) = [4.4,8.1];
plot([fl_2(1,1),fl_2(1,1)],[fl_2(1,2),fl_2(2,2)],'r')
plot([fl_2(1,1),fl_2(2,1)],[fl_2(1,2),fl_2(1,2)],'r')
plot([fl_2(1,1),fl_2(2,1)],[fl_2(2,2),fl_2(2,2)],'r')
plot([fl_2(2,1),fl_2(2,1)],[fl_2(1,2),fl_2(2,2)],'r')

% Cuba
cu(:,1) = [2.3,7.4];
cu(:,2) = [1.7,3.6];
plot([cu(1,1),cu(1,1)],[cu(1,2),cu(2,2)],'r')
plot([cu(1,1),cu(2,1)],[cu(1,2),cu(1,2)],'r')
plot([cu(1,1),cu(2,1)],[cu(2,2),cu(2,2)],'r')
plot([cu(2,1),cu(2,1)],[cu(1,2),cu(2,2)],'r')

% Haiti/DR
dr(:,1) = [7.8,10.3];
dr(:,2) = [0.6,1.8];
plot([dr(1,1),dr(1,1)],[dr(1,2),dr(2,2)],'r')
plot([dr(1,1),dr(2,1)],[dr(1,2),dr(1,2)],'r')
plot([dr(1,1),dr(2,1)],[dr(2,2),dr(2,2)],'r')
plot([dr(2,1),dr(2,1)],[dr(1,2),dr(2,2)],'r')

% PR
pr(:,1) = [11.0,11.8];
pr(:,2) = [0.7,1.1];
plot([pr(1,1),pr(1,1)],[pr(1,2),pr(2,2)],'r')
plot([pr(1,1),pr(2,1)],[pr(1,2),pr(1,2)],'r')
plot([pr(1,1),pr(2,1)],[pr(2,2),pr(2,2)],'r')
plot([pr(2,1),pr(2,1)],[pr(1,2),pr(2,2)],'r')


%% Write output
%
file_ID = fopen('grid_points.txt','w+');
%
% % Write size of grid (multiply point size by 10 so everthing is integers)
grid_size = max(points'*10);
fprintf(file_ID,'Grid size\nX: %i\nY: %i\n\n',grid_size(1),grid_size(2));

% Write grid points
fprintf(file_ID,'x,y,water/land,city\n');
fprintf(file_ID,'0: Water, 1: Land (Not Florida), 2: Land (Florida)\n');
fprintf(file_ID,'0: No city, >0 city ID\n\n');

for i = 1:grid_size(1)
    for k = 1:grid_size(2)
        point = [i;k]/10;
        % for i = 1:length(points)
        %     if i > 1 && any(all(point==points(:,1:i-1)))
        %         continue
        %     end
        fprintf(file_ID,'%i,%i,',point(1)*10,point(2)*10);
        % Check if florida
        if (point(1) >= fl_1(1,1) && point(1) <= fl_1(2,1) && ...
                point(2) >= fl_1(1,2) && point(2) <= fl_1(2,2))
            fprintf(file_ID,'2,');
        elseif (point(1) >= fl_2(1,1) && point(1) <= fl_2(2,1) && ...
                point(2) >= fl_2(1,2) && point(2) <= fl_2(2,2))
            fprintf(file_ID,'2,');
        elseif (point(1) >= cu(1,1) && point(1) <= cu(2,1) && ...
                point(2) >= cu(1,2) && point(2) <= cu(2,2))
            fprintf(file_ID,'1,');
        elseif (point(1) >= dr(1,1) && point(1) <= dr(2,1) && ...
                point(2) >= dr(1,2) && point(2) <= dr(2,2))
            fprintf(file_ID,'1,');
        elseif (point(1) >= pr(1,1) && point(1) <= pr(2,1) && ...
                point(2) >= pr(1,2) && point(2) <= pr(2,2))
            fprintf(file_ID,'1,');
        else
            fprintf(file_ID,'0,');
        end
        
        % Check if city
        city_flag = 0;
        for j = 1:length(cities)
            if all(point == cities(:,j))
                fprintf(file_ID,'%s\n',city_names{j});
                city_flag = 1;
            end
        end
        if ~city_flag
            fprintf(file_ID,'none\n');
        end
    end
end

fclose(file_ID);

%
% % Write Florida points
% fprintf(file_ID,'Florida:\n');
% for i = 1:length(points)
%     if points(2,i) > 4 && points(1,i) < 5
%         fprintf(file_ID,'(%i,%i)\n',points(1,i)*10,points(2,i)*10);
%     end
% end
%
% % Write other land
% fprintf(file_ID,'\nNon-Floridian Land:\n');
% for i = 1:length(points)
%     if points(2,i) < 4 || points(1,i) > 5
%         fprintf(file_ID,'(%i,%i)\n',points(1,i)*10,points(2,i)*10);
%     end
% end
%
% % Write cities
% fprintf(file_ID,'\nCities:\n');
% for i = 1:length(cities)
%     fprintf(file_ID,'(%i,%i)\n',cities(1,i)*10,cities(2,i)*10);
% end
%
%

