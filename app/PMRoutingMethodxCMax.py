def RuteadorxCMax(inputLocations, InputCarga_max, InputDemandas = 1, printSolution = False, plotSolution = False):

    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp
    import matplotlib.pyplot as plt
    import numpy as np
    from geopy.distance import geodesic

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

    def create_data_model(locations, carga_max, demandas = 1):
        """Stores the data for the problem."""
        data = {}
        data['locations'] = locations
        data['num_vehicles'] = len(locations) - 1
        data['depot'] = 0

        demands = [demandas] * (len(locations))
        demands[0] = 0
        data['demands'] = demands
        data['vehicle_capacities'] = [carga_max] * data['num_vehicles']
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
        total_load = 0
        for vehicle_id in range(data['num_vehicles']):
            index = routing.Start(vehicle_id)
            plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
            route_distance = 0
            route_load = 0
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                route_load += data['demands'][node_index]
                plan_output += ' {0} Load({1}) -> '.format(node_index, route_load)
                previous_index = index
                index = assignment.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(
                    previous_index, index, vehicle_id)
            plan_output += ' {0} Load({1})\n'.format(manager.IndexToNode(index),
                                                    route_load)
            plan_output += 'Distance of the route: {}m\n'.format(route_distance)
            plan_output += 'Load of the route: {}\n'.format(route_load)
            print(plan_output)
            total_distance += route_distance
            total_load += route_load
        print('Total Distance of all routes: {}m'.format(total_distance))
        print('Total Load of all routes: {}'.format(total_load))

    def main(locations, carga_max, demandas, printSolution, plotSolution):
        """Solve the VRP with time windows."""
        # Instantiate the data problem.
        data = create_data_model(locations, carga_max, demandas)

        distance_matrix =  compute_geodesic_distance_matrix(data['locations'])

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

        # Add Capacity constraint.
        def demand_callback(from_index):
            """Returns the demand of the node."""
            # Convert from routing variable Index to demands NodeIndex.
            from_node = manager.IndexToNode(from_index)
            return data['demands'][from_node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(
            demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            data['vehicle_capacities'],  # vehicle maximum capacities
            True,  # start cumul to zero
            'Capacity')

        # # Setting first solution heuristic.
        # search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        # search_parameters.first_solution_strategy = (
        #     routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

        # Setting first solution heuristic.
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
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
            raise ValueError("No hay solución, revisar parámetros")

   
    routes, distances  = main(inputLocations, InputCarga_max, InputDemandas, printSolution, plotSolution)
    
    return routes, distances
