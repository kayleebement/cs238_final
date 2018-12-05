import geopy.distance # pip install geopy
from math import atan2, sin, cos, sqrt, pow
import random
import collections
import itertools
import copy

hurricane_file = "hurricane_data.txt" # guide to data https://www.nhc.noaa.gov/data/hurdat/hurdat2-format-atlantic.pdf
hurricanes = []
storm_time = []
population_file = "population.txt" # from google
cities = {}
driving_file = "driving_time.txt" # from google maps
driving_times = collections.defaultdict(dict)
closest_cities = collections.defaultdict(list)
grid_file = "Map_gen/grid_points.txt"
grid_points = collections.defaultdict(dict)

hrs_per_time_step = 3
time_steps_per_day = 24 / hrs_per_time_step
num_ppl_per_group = 30000 # max num of ppl traveling together
min_resource_per_group = 0.5 # min resources each group needs each time step
min_resource_per_group_storm = 1 # if in storm, need 2 resource per group
max_resource_per_group = 1 # max resources a group would take each time step
prob_resource_taking = [.166, .166, .166, .166, .166, .166] # prob_resource_taking[i] = probability that group will take i + 5 resources that day (would be interesting if this varies w # resources available - ie at beginning, ppl are greedy and overpreparing, near end ppl take closer to min)
travel_resource_per_time_step = 1 # resources used each time step of traveling (gas) for simplicity, assume all resources needed between one time step to next are taken from origin city
max_resource_per_truck = 250 # max resources able to fit in a truck to transport from one place to the next

# following values are from https://gist.github.com/jakebathman/719e8416191ba14bb6e700fc2d5fccc5
fl_min_lat = 24.3959
fl_max_lat = 31.0035
fl_min_long = -87.6256
fl_max_long = -79.8198
grid_min_lat = 18.0111
grid_max_lat = fl_max_lat
grid_min_long = -88.7844
grid_max_long = -65.6445
grid_max_x = 0;
grid_max_y = 0;
grid_spacing = 0;   # Spacing between grid lines in km


# grid_points is a dict {<x grid point>: <dict of data>}
# each y grid point is a dict {land: <int>, city <string>}
def read_grid_data():
    print("Reading Grid Data")
    line_count = 0
    with open(grid_file, 'r') as f:
        for line in f:
            line_count = line_count + 1
            if line_count == 2:
                global grid_max_x
                grid_max_x = int(line[3:len(line)])
            elif line_count == 3:
                global grid_max_y
                grid_max_y = int(line[3:len(line)])
            elif line_count > 8:
                (grid_x, grid_y, land_id, city) = line.split(',')
                city = city.strip()
                grid_points[grid_x][grid_y] = {'land': int(land_id), 'city': city}
                if city != 'none':
                    cities[city]['grid_x'] = int(grid_x)
                    cities[city]['grid_y'] = int(grid_y)
                    print(grid_points[grid_x][grid_y])
    global grid_spacing
    grid_spacing = (grid_max_long - grid_min_long) / grid_max_x * 111 * cos((grid_min_lat + grid_max_lat)/2) # 111 km btw long lines at equator


# Converts a latitude/longitude to the nearest grid point
def lat_long_to_grid(latitude,longitude):
    grid_x = (longitude - grid_min_long) / (grid_max_long - grid_min_long) * (grid_max_x - 1) + 1
    grid_y = (latitude - grid_min_lat) / (grid_max_lat - grid_min_lat) * (grid_max_y - 1) + 1
    return (round(grid_x), round(grid_y))


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
        ideal_resources = (pop/num_ppl_per_group) * min_resource_per_group * avg_hurricane_length * time_steps_per_day # everyone is able to have max resource for whole hurricane
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
            time = int(time_steps)
            driving_times[city1][city2] = time
            driving_times[city2][city1] = time
            if time == 1:
                closest_cities[city1].append(city2)
                closest_cities[city2].append(city1)


# Calculates rewards given a state-action pair
def calculate_reward(s,time_idx):
    # Initialize reward
    reward = 0

    # Pull storm data and map from 6 hr to 3 hr (average if time is not a 6 hr interval)
    if (time_idx%2) != 0:
        time_m = int((time_idx-1)/2)
        time_p = int((time_idx+1)/2)
        storm_x_m, storm_y_m = lat_long_to_grid(storm_time[time_m]['lat'],storm_time[time_m]['long'])
        storm_x_p, storm_y_p = lat_long_to_grid(storm_time[time_p]['lat'],storm_time[time_p]['long'])
        rad_m = storm_time[time_m]['rad'] / grid_spacing
        rad_p = storm_time[time_p]['rad'] / grid_spacing
        storm_x = (storm_x_m + storm_x_p)/2
        storm_y = (storm_y_m + storm_y_p)/2
        rad = (rad_m + rad_p)/2
    else:
        storm_x, storm_y = lat_long_to_grid(storm_time[int(time_idx/2)]['lat'],storm_time[int(time_idx/2)]['long'])        
        rad = storm_time[int(time_idx/2)]['rad'] / grid_spacing

    # Loop through all cities to accumulate reward
    for c in s['cities']:
        n_resources = s['cities'][c]['num_resources']
        n_people = s['cities'][c]['num_ppl']

        # Check if city is in storm
        city_x = s['cities'][c]['grid_x']
        city_y = s['cities'][c]['grid_y']
        dist = sqrt( pow(city_x - storm_x,2) + pow(city_y - storm_y,2))
        if dist > rad:
            min_r = min_resource_per_group
        else:
            min_r = min_resource_per_group_storm

        # If not enough resources in area, there is a negative reward proportional to amount of resources lacking
        if n_resources/(n_people/num_ppl_per_group) < min_r:
            reward = reward - n_people/num_ppl_per_group/n_resources*min_r*10;
            # print('Not enough resources in',c,'\nCurrent reward:',reward,'\n')

    return reward


# state is a dict {cities: <dict of cities>, road: <list>, storm: <dict>}
# each city contains num_ppl, num_resources, num_trucks
# each entry in road is a dict containing destination, resources, time steps left
# storm contains lat, long, speed, radius
def generate_actions(s):
    # print("Generating actions...")
    actions = []
    cities = s['cities']
    city_names = cities.keys()
    for origin, data in cities.items():
        # print("Creating actions for origin", origin)
        trucks = data['num_trucks']
        resources = data['num_resources']
        max_transportable = trucks * max_resource_per_truck
        curr_city = []
        curr_city.append({})
        if resources >= max_transportable:
            for i in range(trucks):
                num_resources = max_resource_per_truck * (i + 1)
                for destination in closest_cities[origin]:
                    curr_city.append({'origin': origin, 'destination': destination, 'resources': num_resources})
        else:
            resources_left = resources
            num_resources = 0
            for i in range(resources // max_resource_per_truck):
                if resources_left >= max_resource_per_truck:
                    num_resources += max_resource_per_truck
                else:
                    num_resources += resources_left
                for destination in closest_cities[origin]:
                    curr_city.append({'origin': origin, 'destination': destination, 'resources': num_resources})
        actions.append(curr_city[:])
        print("Length of actions for city", origin, len(curr_city))
    #all_actions = [[x, y, z] for x in actions[city_names[0]]]
    # print("Generating all actions")
    all_actions = list(itertools.product(*actions)) # this doesn't finish bc the action space is still way too big......
    return all_actions



def select_action(s, d, t):
    # if d == num_time_steps:
    if t + d + 1 == num_time_steps or d == 1:
        return ([], s, calculate_reward(s, d))
    best_action, best_s_prime, best_reward = (None, None, float("-inf"))
    actions = generate_actions(s)
    count_a = 0
    dim_a = len(actions)
    for a in actions:
        # print(count_a,'/',dim_a)
        count_a = count_a + 1
        a = list(filter(lambda x: x != {}, a))
        v = calculate_reward(s, d)
        s_prime = transition(s, a, 0, d)
        best_next_a, best_next_s_prime, best_next_r = select_action(s_prime, d + 1, t + 1)
        v += best_next_r
        if v > best_reward:
            best_action = a
            best_s_prime = s_prime
            best_reward = v

    return (best_action, best_s_prime, best_reward)


# Generates initial state to begin simulation
def generate_state():
    state = collections.defaultdict(dict)
    # Randomly selects hurricane from given data
    global storm_time
    storm_time = random.choice(hurricanes)[:]
    state['storm'] = storm_time[1]
    # Initial city state previously defined
    state['cities'] = cities
    # Sample roads entry: {'dest': <destination city>, 'resources': <number of resources travelling>, 'arrival': <timesteps left until arrival}
    state['roads'] = []

    return state


def transition(state, action, truth_flag, time_idx):
    next_state = copy.deepcopy(state)

    # Increment storm
    if (time_idx%2) != 0:
        time_m = int((time_idx-1)/2)
        time_p = int((time_idx+1)/2)
        storm_x_m, storm_y_m = lat_long_to_grid(storm_time[time_m]['lat'],storm_time[time_m]['long'])
        storm_x_p, storm_y_p = lat_long_to_grid(storm_time[time_p]['lat'],storm_time[time_p]['long'])
        rad_m = storm_time[time_m]['rad'] / grid_spacing
        rad_p = storm_time[time_p]['rad'] / grid_spacing
        storm_x = (storm_x_m + storm_x_p)/2
        storm_y = (storm_y_m + storm_y_p)/2
        rad = (rad_m + rad_p)/2
    else:
        storm_x, storm_y = lat_long_to_grid(storm_time[int(time_idx/2)]['lat'],storm_time[int(time_idx/2)]['long'])        
        rad = storm_time[int(time_idx/2)]['rad'] / grid_spacing

    # Add in uncertainty
    if not truth_flag:
        storm_x = storm_x
        storm_y = storm_y
        rad = rad

    # Take actions and move items from origin to road
    for a in action:
        # Pull data
        origin = a['origin']
        destination = a['destination']
        moving = a['resources']
        
        # Subtract from origin
        next_state['cities'][origin]['num_resources'] = state['cities'][origin]['num_resources'] - moving

        # Move to road
        travel_time = driving_times[origin][destination]
        next_state['roads'].append({'destination':destination, 'resources':moving, 'arrival':travel_time})

    # Decrement items on roads
    removal = []
    for r in next_state['roads']:
        if r['arrival'] > 1:
            r['arrival'] = r['arrival'] - 1
        elif r['arrival'] == 1:
            # Remove from roads and add to destination
            destination = r['destination']
            next_state['cities'][destination]['num_resources'] = state['cities'][destination]['num_resources'] + r['resources']
            # r['arrival'] = r['arrival'] - 1
            # state['roads'].remove(r)
            removal.append(r)

    for r in removal:
    	next_state['roads'].remove(r)

    return next_state


avg_hurricane_length = read_hurricane_data()
read_population_data()
generate_resource_data()
read_grid_data()
read_driving_data()

actions = []
reward = 0
curr_state = generate_state()
num_time_steps = len(storm_time) * 2 - 1

for time_step in range(num_time_steps):
    print("Time step: ", time_step)
    print("State: ", curr_state)
    best_action, best_s_prime, best_reward = select_action(curr_state, 0, time_step)
    actions.append(best_action)
    reward += best_reward
    curr_state = best_s_prime.copy()

print("Actions:", actions)
print("Reward: ", reward)