import geopy.distance # pip install geopy
from math import atan2, sin, cos
import random
import collections

hurricane_file = "hurricane_data.txt" # guide to data https://www.nhc.noaa.gov/data/hurdat/hurdat2-format-atlantic.pdf
hurricanes = []
population_file = "population.txt" # from google
cities = {}
driving_file = "driving_time.txt" # from google maps
driving_times = collections.defaultdict(dict)
grid_file = "Map_gen/grid_points.txt"
grid_points = collections.defaultdict(dict)

time_step = 0
hrs_per_time_step = 3
time_steps_per_day = 24 / hrs_per_time_step
num_ppl_per_group = 30000 # max num of ppl traveling together
min_resource_per_group = 1 # min resources each group needs each time step
max_resource_per_group = 3 # max resources a group would take each time step
prob_resource_taking = [.166, .166, .166, .166, .166, .166] # prob_resource_taking[i] = probability that group will take i + 5 resources that day (would be interesting if this varies w # resources available - ie at beginning, ppl are greedy and overpreparing, near end ppl take closer to min)
travel_resource_per_time_step = 1 # resources used each time step of traveling (gas) for simplicity, assume all resources needed between one time step to next are taken from origin city
max_resource_per_truck = 240 # max resources able to fit in a truck to transport from one place to the next

# following values are from https://gist.github.com/jakebathman/719e8416191ba14bb6e700fc2d5fccc5
fl_min_lat = 24.3959
fl_max_lat = 31.0035
fl_min_long = -87.6256
fl_max_long = -79.8198


# grid_points is a dict {<x grid point>: <dict of data>}
# each y grid point is a dict {land: <int>, city <string>}
def read_grid_data():
    print("to do: read grid data")
    line_count = 0
    with open(grid_file, 'r') as f:
        for line in f:
            line_count = line_count + 1
            if line_count > 8:
                (grid_x, grid_y, land_id, city) = line.split(',')
                city = city.strip()
                grid_points[grid_x][grid_y] = {'land': int(land_id), 'city': city}
                if city != 'none':
                    print(grid_points[grid_x][grid_y])


# hurricanes is a list of hurricanes
# each hurricane is a list of time slots (at 6 hour intervals)
# each time slot is a dict {lat: <float>, long: <float>, speed:<float>, radius:<int>}
def read_hurricane_data():
    print("Reading Hurricane Data")
    status_idx = 3
    lat_idx = 4
    long_idx = 5
    wind_idx = 6
    status_hurricane = 'HU'
    total_days = 0
    min_radius = 333 # in km
    max_radius = 670 # in km
    with open(hurricane_file, 'r') as f:
        curr_hurricane = None
        curr_status_confirmed = False # confirmed that it reaches "hurricane" status (don't want tropical storms or anything lame)
        curr_florida_confirmed = False # confirmed that it hits florida
        for line in f:
            curr = line.split(",")
            num_cols = len(curr)
            if num_cols == 4:
                if curr_hurricane and curr_status_confirmed and curr_florida_confirmed:
                    hurricanes.append(curr_hurricane[:])
                    total_days += len(curr_hurricane) / 4
                curr_hurricane = []
                curr_status_confirmed = False
                curr_florida_confirmed = False
            else:
                curr = [x.strip() for x in curr]
                curr_time_step = {}
                lat = curr[lat_idx]
                lat = float(lat[:-1]) if lat[-1] == 'N' else -1 * float(lat[:-1])
                longit = curr[long_idx] 
                longit = -1 * float(longit[:-1]) if longit[-1] == 'W' else float(longit[:-1])
                curr_time_step["lat"] = lat
                curr_time_step["long"] = longit
                curr_time_step["wind"] = float(curr[wind_idx])
                curr_time_step["rad"] = random.randint(min_radius, max_radius)
                if not curr_status_confirmed and curr[status_idx] == status_hurricane: # it's offically a hurricane baby
                    curr_status_confirmed = True
                if not curr_florida_confirmed:
                    if lat >= fl_min_lat and lat <= fl_max_lat and longit >= fl_min_long and longit <= fl_max_long:
                        curr_florida_confirmed = True
                curr_hurricane.append(curr_time_step.copy())
    avg_hurricane_length = int(total_days / 205)
    return avg_hurricane_length
    

# cities is a dict {<city name>:<dict of data>}
# each city is a dict {<num_ppl>:<int>, <num_resources>:<int>, <num_trucks>:<int>}
def read_population_data():
    print("Reading Population Data")
    with open(population_file, 'r') as f:
        for line in f:
            (city, pop) = line.split(',')
            cities[city] = {'num_ppl': int(pop)}

# assigns number of resources and trucks for each city
def generate_resource_data():
    print("Generating Resource Data")
    total_resources = 0
    total_trucks = 0
    for city, data in cities.items():
        pop = data['num_ppl']
        ideal_resources = (pop/num_ppl_per_group) * (max_resource_per_group) * avg_hurricane_length * time_steps_per_day # everyone is able to have max resource for whole hurricane
        num_resources = random.randint(int(ideal_resources * 0.75), int(ideal_resources * 1.25)) # num resources randomly between 75% and 125% of ideal number
        ideal_trucks = num_resources / max_resource_per_truck # all resources able to be moved
        num_trucks = random.randint(int(ideal_trucks * 0.75), int(ideal_trucks * 0.75)) # num trucks random between 75% and 125% of ideal
        data['num_resources'] = num_resources
        data['num_trucks'] = num_trucks
        total_resources += num_resources
        total_trucks += num_trucks
    print(cities)
    print(total_resources)
    print(total_trucks)

# driving_times is a dict {<city>:<dict of data>}
# each city contains dict {<other city>:<float>, ...}
def read_driving_data():
    print("Reading Driving Data")
    with open(driving_file, 'r') as f:
        for line in f:
            (city1, city2, time_steps) = line.split(',')
            driving_times[city1][city2] = float(time_steps)
            driving_times[city2][city1] = float(time_steps)


def get_hurricane():
    curr_hurricane = random.choice(hurricanes)[:]
    num_time_steps = len(curr_hurricane) * 2
    return (curr_hurricane, num_time_steps)

# state is a dict {cities: <dict of cities>, road: <list>, storm: <dict>}
# each city contains num_ppl, num_resources, num_trucks
# each entry in road is a dict containing destination, resources, time steps left
# storm contains lat, long, speed, radius
def generate_actions(s):


def select_action(s, d):
    if d == num_time_steps:
        return (None, 0)
    best_action, best_reward = (None, float("-inf"))
    actions = generate_actions(s)
    for a in actions:
        v = get_reward(s, a)
        s_prime = get_next_state(s, a)
        best_next_a, best_next_r = select_action(s_prime, d + 1)
        v += best_next_r
        if v > best_reward:
            best_action = a
            best_reward = v
    return (best_action, best_reward)

read_grid_data()
avg_hurricane_length = read_hurricane_data()
read_population_data()
generate_resource_data()
read_driving_data()
curr_hurricane, num_time_steps = get_hurricane()

### PROBABLY GOING TO DELETE - IRRELEVANT 
def calc_angles_speeds():
    hrs_per_step = 6
    pi = 3.14
    max_bearing = None
    min_bearing = None
    checking = None
    counts = [0, 0, 0, 0]
    for hurricane in hurricanes:
        for t in range(1, len(hurricane)):
            prev_step = hurricane[t - 1]
            curr_step = hurricane[t]
            lat_1 = prev_step['lat']
            long_1 = prev_step['long']
            lat_2 = curr_step['lat']
            long_2 = curr_step['long']
            # calc speed
            coords_1 = (lat_1, long_1)
            coords_2 = (lat_2, long_2)
            dist = geopy.distance.distance(coords_1, coords_2).km
            speed = dist/hrs_per_step
            # calc bearing 
            long_delta = long_2 - long_1
            y = sin(long_delta) * cos(lat_2)
            x = cos(lat_1) * sin(lat_2) - sin(lat_1) * cos(lat_2) * long_delta
            bearing = atan2(y, x)
            bearing = bearing * 180 / pi
            curr_step["speed"] = speed
            curr_step["bearing"] = bearing
