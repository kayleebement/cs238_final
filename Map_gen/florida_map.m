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
% Jacksonville
cities(1,1) = 3.7;
cities(2,1) = 7.8;
% Miami
cities(1,2) = 4.6;
cities(2,2) = 5.3;
% Tampa
cities(1,3) = 3.3;
cities(2,3) = 6.3;
% Orlando
cities(1,4) = 3.8;
cities(2,4) = 6.8;
% St. Petersburg
cities(1,5) = 3.2;
cities(2,5) = 6.0;
% % Hialeah
cities(1,6) = 4.5;
cities(2,6) = 5.4;
% Tallahassee
cities(1,7) = 2.3;
cities(2,7) = 7.8;
% Port St. Lucie
cities(1,8) = 4.4;
cities(2,8) = 6.0;
% Cape Coral
cities(1,9) = 3.5;
cities(2,9) = 5.7;
% Fort Lauderdale
cities(1,10) = 4.6;
cities(2,10) = 5.5;
% Pensacol
cities(1,11) = 0.9;
cities(2,11) = 7.8;
% Key Largo
cities(1,12) = 4.4;
cities(2,12) = 4.7;
% Key West
cities(1,13) = 3.5;
cities(2,13) = 4.4;

% Remove cities: Hialeah
cities(:,6) = [];
rm_count = 1;
cities(:,12-rm_count) = [];

hold on
plot(cities(1,:),cities(2,:),'k.','MarkerSize',9)


%% Write output

file_ID = fopen('Hurricane.txt','w+');

% Write size of grid (multiply point size by 10 so everthing is integers)
grid_size = max(points'*10);
fprintf(file_ID,'Grid size\nX: %i\nY: %i\n\n',grid_size(1),grid_size(2));

% Write Florida points
fprintf(file_ID,'Florida:\n');
for i = 1:length(points)
    if points(2,i) > 4 && points(1,i) < 5
        fprintf(file_ID,'(%i,%i)\n',points(1,i)*10,points(2,i)*10);
    end
end

% Write other land
fprintf(file_ID,'\nNon-Floridian Land:\n');
for i = 1:length(points)
    if points(2,i) < 4 || points(1,i) > 5
        fprintf(file_ID,'(%i,%i)\n',points(1,i)*10,points(2,i)*10);
    end
end

% Write cities
fprintf(file_ID,'\nCities:\n');
for i = 1:length(cities)
    fprintf(file_ID,'(%i,%i)\n',cities(1,i)*10,cities(2,i)*10);
end



