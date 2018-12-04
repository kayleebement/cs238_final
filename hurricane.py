import geopy.distance # pip install geopy
from math import atan2, sin, cos, sqrt, pow
import random
import collections
import itertools

hurricane_file = "hurricane_data.txt" # guide to data https://www.nhc.noaa.gov/data/hurdat/hurdat2-format-atlantic.pdf
hurricanes = []
population_file = "population.txt" # from google
cities = {}
driving_file = "driving_time.txt" # from google maps
driving_times = collections.defaultdict(dict)
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
max_resource_per_truck = 500 # max resources able to fit in a truck to transport from one place to the next

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
        ideal_resources = (pop/num_ppl_per_group) * max_resource_per_group * avg_hurricane_length * time_steps_per_day # everyone is able to have max resource for whole hurricane
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



# Calculates rewards given a state-action pair
def calculate_reward(s,time_idx):
    # Initialize reward
    reward = 0
    print(time_idx)

    # Pull storm data and map from 6 hr to 3 hr (average if time is not a 6 hr interval)
    if (time_idx%2) != 0:
        time_m = int((time_idx-1)/2)
        time_p = int((time_idx+1)/2)
        storm_x_m, storm_y_m = lat_long_to_grid(s['storm'][time_m]['lat'],s['storm'][time_m]['long'])
        storm_x_p, storm_y_p = lat_long_to_grid(s['storm'][time_p]['lat'],s['storm'][time_p]['long'])
        rad_m = s['storm'][time_m]['rad'] / grid_spacing
        rad_p = s['storm'][time_p]['rad'] / grid_spacing
        storm_x = (storm_x_m + storm_x_p)/2
        storm_y = (storm_y_m + storm_y_p)/2
        rad = (rad_m + rad_p)/2
    else:
        storm_x, storm_y = lat_long_to_grid(s['storm'][int(time_idx/2)]['lat'],s['storm'][int(time_idx/2)]['long'])        
        rad = s['storm'][int(time_idx/2)]['rad'] / grid_spacing

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
            print('Not enough resources in',c,'\nCurrent reward:',reward,'\n')

    return reward


# state is a dict {cities: <dict of cities>, road: <list>, storm: <dict>}
# each city contains num_ppl, num_resources, num_trucks
# each entry in road is a dict containing destination, resources, time steps left
# storm contains lat, long, speed, radius
def generate_actions(s):
    print("Generating actions...")
    actions = []
    cities = s['cities']
    city_names = cities.keys()
    for origin, data in cities.items():
        print("Creating actions for origin", origin)
        trucks = data['num_trucks']
        resources = data['num_resources']
        max_transportable = trucks * max_resource_per_truck
        curr_city = []
        curr_city.append({})
        if resources >= max_transportable:
            for i in range(trucks):
                num_resources = max_resource_per_truck * (i + 1)
                for destination in city_names:
                    if destination == origin:
                        continue
                    curr_city.append({'origin': origin, 'destination': destination, 'resources': num_resources})
        else:
            resources_left = resources
            num_resources = 0
            for i in range(resources // max_resource_per_truck):
                if resources_left >= max_resource_per_truck:
                    num_resources += max_resource_per_truck
                else:
                    num_resources += resources_left
                for destination in city_names:
                    if destination == origin:
                        continue
                    curr_city.append({'origin': origin, 'destination': destination, 'resources': num_resources})
        actions.append(curr_city[:])
        print("Length of actions for city", origin, len(curr_city))
    #all_actions = [[x, y, z] for x in actions[city_names[0]]]
    print("Generating all actions")
    all_actions = list(itertools.product(*actions)) # this doesn't finish bc the action space is still way too big......
    return all_actions



def select_action(s, d):
    print("Select Action at Depth:", d)
    if d == num_time_steps:
        return (None, 0)
    best_action, best_reward = (None, float("-inf"))
    actions = generate_actions(s)
    print("Length of actions list:", len(actions))
    for a in actions:
        a = list(filter(lambda x: x != {}, a))
        v = calculate_reward(s, d)
        s_prime = transition(s, a)
        best_next_a, best_next_r = select_action(s_prime, d + 1)
        v += best_next_r
        if v > best_reward:
            best_action = a
            best_reward = v
    return (best_action, best_reward)


# Generates initial state to begin simulation
def generate_state():
    state = collections.defaultdict(dict)
    # Randomly selects hurricane from given data
    state['storm'] = random.choice(hurricanes)[:]
    # Initial city state previously defined
    state['cities'] = cities
    # Sample roads entry: {'dest': <destination city>, 'resources': <number of resources travelling>, 'arrival': <timesteps left until arrival}
    state['roads'] = []

    return state


def transition(state, action):

    # Take actions and move items from origin to road
    for a in action:
        # Pull data
        origin = action[a]['origin']
        destination = action[a]['destination']
        moving = action[a]['resources']

        # Check if moving more resources than available
        if moving > state['cities'][origin]['resources']:
            moving = state['cities'][origin]['resources']
        
        # Subtract from origin
        state['cities'][origin]['resources'] = state['cities'][origin]['resources'] - moving

        # Move to road
        state['roads'].append({'destination':destination, 'resources':moving, 'arrival':travel_time})

    # Decrement items on roads
    for r in state['roads']:
        if state['roads'][r]['arrival'] > 0:
            state['roads'][r]['arrival'] = state['roads'][r]['arrival'] - 1
        else:
            # Remove from roads and add to destination
            state['cities'][destination]['resources'] = state['cities'][destination]['resources'] + state['roads'][r]['resources']
            state['roads'].remove(r)

    return state


avg_hurricane_length = read_hurricane_data()
read_population_data()
generate_resource_data()
read_grid_data()
read_driving_data()
curr_state = generate_state()
num_time_steps = len(curr_state['storm']) * 2 - 1
print(num_time_steps)
best_action, best_reward = select_action(curr_state, 0)