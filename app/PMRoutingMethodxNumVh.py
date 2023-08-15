from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import matplotlib.pyplot as plt
import numpy as np
from geopy.distance import geodesic
from sklearn.cluster import KMeans

def compute_geodesic_distance_matrix(locations):
    """Creates callback to return geodesic distance between points."""
    distances = {}
    for from_counter, from_node in enumerate(locations):
        distances[from_counter] = {}
        for to_counter, to_node in enumerate(locations):
            if from_counter == to_counter:
                distances[from_counter][to_counter] = 0
            else:
                # Geodesic distance in meters without decimals
                distance = geodesic(from_node, to_node).meters
                distances[from_counter][to_counter] = int(distance)
    return distances

def create_data_model(locations, num_vehicles):
    """Stores the data for the problem."""
    data = {}
    data['locations'] = locations
    data['num_vehicles'] = num_vehicles
    data['depot'] = 0
    return data

def get_routes(solution, routing, manager):
    """Get vehicle routes from a solution and store them in an array."""
    routes = []
    distances = []  # List to store the distance for each route
    for route_nbr in range(routing.vehicles()):
        index = routing.Start(route_nbr)
        route = [manager.IndexToNode(index)]
        route_distance = 0  # Initialize distance for the current route
        previous_index = index
        while not routing.IsEnd(index):
            next_index = solution.Value(routing.NextVar(index))
            # Sum the distance from the previous location to the current location
            route_distance += routing.GetArcCostForVehicle(previous_index, next_index, route_nbr)
            previous_index = index
            index = next_index
            route.append(manager.IndexToNode(index))
        # Remove the last location (depot) from the route before adding it to routes
        routes.append(route[:-1])
        distances.append(route_distance)
    return routes, distances

def plot_routes(data, manager, routing, solution, figsize=(10, 10)):
    """Plots the routes on a map with only route indices as tags for each point."""

    # Get the locations and number of vehicles from the data model
    locations = data['locations']
    num_vehicles = data['num_vehicles']

    # Create a figure and axes
    fig, ax = plt.subplots(figsize=figsize)

    # Plot each route
    for vehicle_id in range(num_vehicles):
        # Get the route for the current vehicle
        index = routing.Start(vehicle_id)
        route = [manager.IndexToNode(index)]
        while not routing.IsEnd(index):
            index = solution.Value(routing.NextVar(index))
            route.append(manager.IndexToNode(index))

        # Get the color for the current route
        color = plt.cm.get_cmap('tab10', num_vehicles)(vehicle_id % num_vehicles)

        # Plot the route as a line connecting the locations
        lats = [location[0] for location in locations]
        lngs = [location[1] for location in locations]
        ax.plot(lngs, lats, 'o', color='black', markersize=5)  # Plot all locations
        ax.plot([lngs[i] for i in route], [lats[i] for i in route], marker='o', color=color, label=f'Route {vehicle_id}')

        # Add route indices as text for each point
        for i, (lat, lng) in enumerate(locations):
            if i in route:
                route_index = route.index(i) + 1  # Get the index of the point within the route
                ax.text(lng, lat, str(route_index), color='white', backgroundcolor='black',
                        ha='center', va='center')

    # Set the axes labels and title
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('Routes')

    # Add a legend
    ax.legend()

    # Display the plot
    plt.show()

def print_solution(data, manager, routing, assignment):
    """Prints assignment on console."""
    print(f'Objective: {assignment.ObjectiveValue()}')
    # Display dropped nodes.
    dropped_nodes = 'Dropped nodes:'
    for node in range(routing.Size()):
        if routing.IsStart(node) or routing.IsEnd(node):
            continue
        if assignment.Value(routing.NextVar(node)) == node:
            dropped_nodes += ' {}'.format(manager.IndexToNode(node))
    print(dropped_nodes)
    # Display routes
    total_distance = 0
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        route_distance = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            previous_index = index
            index = assignment.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
        plan_output += 'Distance of the route: {}m\n'.format(route_distance)
        print(plan_output)
        total_distance += route_distance
    print('Total Distance of all routes: {}m'.format(total_distance))

def main(locations, num_vehicles, printSolution, plotSolution):
        """Solve the VRP."""
        # Instantiate the data problem.
        data = create_data_model(locations, num_vehicles)
        distance_matrix = compute_geodesic_distance_matrix(data['locations'])

        # Create the routing index manager.
        manager = pywrapcp.RoutingIndexManager(len(distance_matrix),
                                            data['num_vehicles'], data['depot'])

        # Create Routing Model.
        routing = pywrapcp.RoutingModel(manager)
        
        # Create and register a transit callback.
        def distance_callback(from_index, to_index):
            """Returns the distance between the two nodes."""
            # Convert from routing variable Index to distance matrix NodeIndex.
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return distance_matrix[from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)

        # Define cost of each arc.
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)      

        # Setting first solution heuristic.
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION)
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
        search_parameters.time_limit.FromSeconds(1)

        # Solve the problem.
        solution = routing.SolveWithParameters(search_parameters)

        # Print solution on console.
        if solution:
            routes, distances = get_routes(solution, routing, manager)
            
            if printSolution:
                print_solution(data, manager, routing, solution)
                
            if plotSolution:
                plot_routes(data, manager, routing, solution, figsize=(10, 10))

            return routes, distances
        else:
            return None

def RuteadorxNumVh(InputLocations, InputNum_vehicles, printSolution = False, plotSolution = False):
    # Convertir ubicaciones a un numpy array para KMeans
    locations_np = np.array(InputLocations[1:])  # Excluir depósito
    
    # Realizar clustering con K-means
    kmeans = KMeans(n_clusters=InputNum_vehicles, random_state=0).fit(locations_np)
    cluster_indices = kmeans.labels_
    
    # Crear clusters y mantener un mapeo de índices originales
    clusters = []
    original_indices_mapping = []
    for i in range(InputNum_vehicles):
        cluster = [InputLocations[0]]  # Añadir depósito
        original_indices = [0]  # índice para el depósito
        cluster_data = locations_np[cluster_indices == i].tolist()
        for loc in cluster_data:
            index = InputLocations.index(tuple(loc))
            original_indices.append(index)
            cluster.append(loc)
        clusters.append(cluster)
        original_indices_mapping.append(original_indices)
    
    # Resolver VRP para cada cluster
    all_routes = []
    all_distances = []
    for idx, cluster in enumerate(clusters):
        routes, distances = main(cluster, 1, printSolution, plotSolution)
        # Mapear los índices de vuelta a sus valores originales
        mapped_routes = []
        for route in routes:
            mapped_route = [original_indices_mapping[idx][i] for i in route]
            mapped_routes.append(mapped_route)
        all_routes.extend(mapped_routes)
        all_distances.extend(distances)
    
    return all_routes, all_distances
