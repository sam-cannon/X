import argparse
import logging
import os

import ai_tools.utilities as utilities_ai   
from flask import Flask, request, jsonify

import decorations_generator.utilities as utilities_backend
from decorations_generator.models import ModelsProcessor


log = logging.getLogger(__name__)


parser = argparse.ArgumentParser()
parser.add_argument("--debug", action="store_true")
parser.add_argument("--port", default=8051)
parser.add_argument("--host", default="0.0.0.0")
parser.add_argument("--url_base", default=None)

arguments, _ = parser.parse_known_args()

path_configuration = utilities_backend.get_project_path().joinpath("conf", "configuration.yaml")
configuration = utilities_backend.read_yaml(file_path=path_configuration)

#Apply the override to the Tracking URI to work in local desktop docker deployments
configuration["tracking_uri"] = os.getenv("TRACKING_URI", default=configuration["tracking_uri"])

#Apply the override to the Model URI to work in local desktop docker deployments
configuration["model_uri"] = os.getenv("MODEL_URI", default=configuration["model_uri"])

utilities_ai.configure_logging(path="decorations_generator_api/log/decorations_generator_api.log")
utilities_ai.setup_mlflow(configuration=configuration)


application = Flask(__name__)


@application.route("/api/ping", methods=["GET", "POST"])
def ping():
    log.debug("Ping request received")
    return jsonify({"message": "success"}), 200
 

@application.route("/api/run_processors", methods=["POST"])
def run_processors():
    data = request.get_json()
    log.debug(f"Request data: {data}")
    try:
        models_processor = ModelsProcessor(configuration=configuration)
        log.info(f"Processing input data using {configuration['model']} model")
        response = models_processor.process(
            bullets=data["bullets"], duty_location=data["duty_location"],
            duty_title=data["duty_title"], full_name=data["full_name"], medal=data["medal"], rank=data["rank"],
            branch=data["branch"], start_date=data["start_date"], end_date=data["end_date"], unit=data["unit"]
        )
        log.debug(f"Successfully processed input data")
        return jsonify({"message": response}), 200
    except Exception as e:
        log.error(f"An error occurred while processing input data: {e}")
        return jsonify({"message": "An error occurred obtaining a response. Please try again."}), 500


if __name__ == "__main__":
    application.run(debug=arguments.debug, host=arguments.host, port=arguments.port)
    