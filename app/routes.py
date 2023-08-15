
from flask import Flask, request, jsonify
from app.PMRoutingMethodCompleto import RuteadorCompleto
from app.PMRoutingMethodxNumVh import RuteadorxNumVh
from app.PMRoutingMethodxCMax import RuteadorxCMax

def setup_routes(app):

    @app.route('/PMRoutingCompleto', methods=['POST'])
    def ApiCompleto():
        routes = []  # Initialize routes with an empty list
        try:
            # Extract data from JSON
            data = request.json
            locations = data['Locations']

            # Convertir las ubicaciones de lista de listas a lista de tuplas
            locations = [tuple(location) for location in data['Locations']]  

            demoras = data['Demoras']
            num_vehicles = data['CantidadDeRutas']
            carga_max = data['CargaMax']
            demandas = data.get('Demandas', 1)  # If 'Demandas' is not in the JSON, use 1 by default

            if len(locations) == 0:
                return jsonify({"error": "No se han pasado ubicaciones para rutear"}), 401

            if num_vehicles < 1:
                return jsonify({"error": "La cantidad de rutas debe ser mayor a 0"}), 402

            if carga_max < 1:
                return jsonify({"error": "La carga maxima debe ser mayor a 0"}), 403

            # Call the function RuteadorGaston
            routes, distances = RuteadorCompleto(locations,  demoras,  num_vehicles, carga_max, demandas, False, False)  # Assuming you don't wish to print or trace the solution in the API.
            
            return jsonify({"routes": routes,"distances": distances}), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            return jsonify({"errorcaca": str(e)}), 400

    @app.route('/PMRoutingxNumVh', methods=['POST'])
    def ApixNumVh():
        routes = []  # Initialize routes with an empty list
        try:
            # Extract data from JSON
            data = request.json
            locations = data['Locations']

            # Convertir las ubicaciones de lista de listas a lista de tuplas
            locations = [tuple(location) for location in data['Locations']]     
            num_vehicles = data['CantidadDeRutas']

            if len(locations) == 0:
                return jsonify({"error": "No se han pasado ubicaciones para rutear"}), 401

            if num_vehicles < 1:
                return jsonify({"error": "La cantidad de rutas debe ser mayor a 0"}), 402

            # Call the function RuteadorGaston
            routes, distances = RuteadorxNumVh(locations, num_vehicles, False, False)  # Assuming you don't wish to print or trace the solution in the API.
            
            return jsonify({"routes": routes,"Distances": distances}), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            return jsonify({"errorcaca": str(e)}), 400

    @app.route('/PMRoutingxCMax', methods=['POST']) ##NO ES UTIL PORQUE LE FALTA POLÍTICA DE OUTLYERS
    def ApixCMax():
        routes = []  # Initialize routes with an empty list
        try:
            # Extract data from JSON
            data = request.json
            locations = data['Locations']

            # Convertir las ubicaciones de lista de listas a lista de tuplas
            locations = [tuple(location) for location in data['Locations']]     
            carga_max = data['CargaMax']
            demandas = data.get('Demandas', 1)  # If 'Demandas' is not in the JSON, use 1 by default

            if len(locations) == 0:
                return jsonify({"error": "No se han pasado ubicaciones para rutear"}), 401

            if carga_max < 1:
                return jsonify({"error": "La carga maxima debe ser mayor a 0"}), 403

            # Call the function RuteadorGaston
            routes, distances = RuteadorxCMax(locations, carga_max, demandas, False, False)  # Assuming you don't wish to print or trace the solution in the API.
            
            return jsonify({"routes": routes,"distances": distances}), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            return jsonify({"errorcaca": str(e)}), 400
        
if __name__ == '__main__':
    app = Flask(__name__)
    setup_routes(app)
    app.run(debug=True, port=5008)
