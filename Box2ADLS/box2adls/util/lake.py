import logging
from os.path import split

from azure.core.exceptions import (ResourceNotFoundError,
                                   ResourceExistsError)

import box2adls.logging

logger = logging.getLogger(__name__)


def upload_files(lake_client, lake_container, lake_dir, files):
    """
    Upload local files to lake.

    :param lake_client: lake client
    :param lake_container: lake container
    :param lake_dir: lake target path
    :param files: list of local file paths
    :return: None
    """
    fs = lake_client.get_file_system_client(file_system=lake_container)
    dc = fs.get_directory_client(directory=lake_dir)

    try:
        dc.create_directory()
    except ResourceExistsError as e:
        logger.error(f'Lake container "{lake_container}" exists.')
    except ResourceNotFoundError as e:
        logger.error(f'Lake container "{lake_container}" does not exist.')
        raise

    for download in files:
        with open(download, 'rb') as f:
            _, tail = split(download)

            fc = dc.create_file(file=tail)
            data = f.read()
            fc.append_data(data, offset=0, length=len(data))
            fc.flush_data(len(data))

            logger.info(f'Uploaded to lake "{lake_dir}/{tail}"...')
