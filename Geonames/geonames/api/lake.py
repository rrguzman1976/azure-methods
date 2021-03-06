from os.path import split
from threading import Lock

from azure.core.exceptions import (ResourceNotFoundError,
                                   ResourceExistsError)
from azure.storage.filedatalake import DataLakeServiceClient

from geonames import LAKE_URL, STORE_KEY
from geonames.util.log import get_logger

logger = get_logger(__name__)


class LakeFactory(object):
    """
    Implementation of a singleton for managing lake resource.

    TODO:
    - Is this the best way to implement the singleton/factory pattern in Python?
    - Consider refactoring into a shared library.

    Inspired by:
    - https://github.com/Azure-Samples/azure-sql-db-python-rest-api

    """
    __instance = None
    __connection = None
    __lock = Lock()

    def __new__(cls):
        if LakeFactory.__instance is None:
            LakeFactory.__instance = object.__new__(cls)
        return LakeFactory.__instance

    def __get_connection(self):
        """
        Create a long-lived lake client.

        :return: the DataLakeServiceClient client
        """
        if not self.__connection:
            logger.info(f'Authenticating to data lake...')

            self.__connection = DataLakeServiceClient(account_url=LAKE_URL,
                                                      credential=STORE_KEY)

        return self.__connection

    def __remove_connection(self):
        self.__connection = None

    def upload_files(self, lake_container, lake_dir, files):
        """
        Upload local files to lake.

        :param lake_container: lake container
        :param lake_dir: lake target path
        :param files: list of local file paths
        :return: None
        """
        lake_client = self.__get_connection()
        fs = lake_client.get_file_system_client(file_system=lake_container)
        dc = fs.get_directory_client(directory=lake_dir)

        try:
            dc.create_directory()
        except ResourceExistsError as e:
            logger.error(f'Lake container exists', source=lake_container)
        except ResourceNotFoundError as e:
            logger.error(f'Lake container does not exist', source=lake_container)
            raise

        for file in files:
            with open(file, 'rb') as f:
                _, tail = split(file)

                fc = dc.create_file(file=tail)
                data = f.read()
                fc.append_data(data, offset=0, length=len(data))
                fc.flush_data(len(data))

                logger.info('Uploaded to lake', source=file
                            , target=f'{lake_dir}/{tail}')