import json

from graph_api.util.log import get_logger

logger = get_logger(__name__)


def load_from_path(file_path):
    """
    Loads to dictionary from path to json file.

    :param file_path:
    :return: Dict
    """
    with open(file_path, "rb") as file:
        return json.load(file)
