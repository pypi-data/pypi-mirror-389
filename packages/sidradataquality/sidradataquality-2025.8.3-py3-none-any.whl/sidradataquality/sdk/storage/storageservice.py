import re
from datetime import datetime, timedelta
from operator import attrgetter
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, ResourceTypes, AccountSasPermissions, generate_account_sas, ContainerSasPermissions, generate_container_sas
import sidradataquality.sdk.constants as const
from sidradataquality.sdk.log.logging import Logger
from sidradataquality.sdk.databricks.utils import Utils

class StorageService():
    def __init__(self, spark):
        self.logger = Logger(spark, self.__class__.__name__)
        self.spark = spark
        self.databricks_utils = Utils(spark)

    # This methods seems not used and the secret account key could be wrong because it cannot be equal to the dq account key
    def get_blob_data_lake_service_client(self):
        return self._get_blob_service('resources', const.SECRET_STORAGE_ACCOUNT_NAME, const.SECRET_STORAGE_ACCOUNT_KEY)
    
    def get_blob_service_client(self):
        return self._get_blob_service(const.SECRET_DATABRICKS_SCOPE, const.SECRET_STORAGE_ACCOUNT_NAME, const.SECRET_STORAGE_ACCOUNT_KEY)

    def get_or_create_container(self, blob_service_client, destination_container) -> str:
        if not [ container for container in blob_service_client.list_containers(destination_container) if container.name == destination_container ]:
            try:
                blob_service_client.create_container(destination_container.lower())
            except ResourceExistsError as e:
                # Ignore error if the container already exists because it could happen due a race condition and if the container already exists simply return the destination container
                if e.error_code != 'ContainerAlreadyExists':
                    raise e    
        return destination_container

    def get_or_create_container_in_data_quality_storage(self, container_name):
        blob_service = self.get_blob_service_client()
        return self.get_or_create_container(blob_service, container_name)

    def get_dq_connection_string(self):
        storage_account_name = self.databricks_utils.get_databricks_secret(const.SECRET_DATABRICKS_SCOPE, const.SECRET_STORAGE_ACCOUNT_NAME)
        storage_account_key = self.databricks_utils.get_databricks_secret(const.SECRET_DATABRICKS_SCOPE, const.SECRET_STORAGE_ACCOUNT_KEY)
        return f'DefaultEndpointsProtocol=https;AccountName={storage_account_name};AccountKey={storage_account_key};'
    
    def get_data_quality_url(self):
        storage_account_name = self.databricks_utils.get_databricks_secret(const.SECRET_DATABRICKS_SCOPE, const.SECRET_STORAGE_ACCOUNT_NAME)
        return f'wasbs://{const.STORAGE_DEFAULT_CONTAINER}@{storage_account_name}.blob.core.windows.net/'
    
    def set_access_to_dq_storage(self):
        storage_account_name = self.databricks_utils.get_databricks_secret(const.SECRET_DATABRICKS_SCOPE, const.SECRET_STORAGE_ACCOUNT_NAME)
        storage_account_key = self.databricks_utils.get_databricks_secret(const.SECRET_DATABRICKS_SCOPE, const.SECRET_STORAGE_ACCOUNT_KEY)
        self.spark.conf.set('fs.azure.account.key.' + storage_account_name + '.blob.core.windows.net', storage_account_key)

    def upload_file_to_datalake(self, name, path, content, destination_container = const.STORAGE_DEFAULT_CONTAINER):
        blob_service = self.get_blob_data_lake_service_client()
        self._upload_file(blob_service, name, path, content, destination_container)

    def upload_file_to_data_quality_storage(self, name, path, content, destination_container = const.STORAGE_DEFAULT_CONTAINER):
        blob_service = self.get_blob_service_client()
        self._upload_file(blob_service, name, path, content, destination_container)

    def get_data_quality_mount_point(self, path, container = const.STORAGE_DEFAULT_CONTAINER):
        storage_account_name = self.databricks_utils.get_databricks_secret(const.SECRET_DATABRICKS_SCOPE, const.SECRET_STORAGE_ACCOUNT_NAME)
        storage_account_key = self.databricks_utils.get_databricks_secret(const.SECRET_DATABRICKS_SCOPE, const.SECRET_STORAGE_ACCOUNT_KEY)
        source = f"wasbs://{container}@{storage_account_name}.blob.core.windows.net"
        mount_point = f"/mnt/{storage_account_name}_{container}"
        if path is not None and path != '':
            source = f'{source}/{path}'
            mount_point = f'{mount_point}/{path}'
        return self._mount_container(source, mount_point, storage_account_name, storage_account_key)
    
    def _mount_container(self, source, mount_point, storage_account, storage_key):
        config_key = f"fs.azure.account.key.{storage_account}.blob.core.windows.net"
        dbutils = self.databricks_utils.get_db_utils()
        try:
            dbutils.fs.mount(
            source = source,
            mount_point = mount_point,
            extra_configs = {config_key:storage_key})
        except Exception as e:
            if not any(mount.mountPoint == mount_point for mount in dbutils.fs.mounts()):
                self.logger.exception(f"[Storage Service][_mount_container] There was an error mounting '{mount_point}': {e.reason}")
                raise e                   
        return mount_point    

    def _upload_file(self, blob_service, name, path, content, destination_container):
        container = self.get_or_create_container(blob_service, destination_container)
        blob_client = blob_service.get_blob_client(container, f"{path}/{name}")
        blob_client.upload_blob(content, overwrite=True)

    def _get_blob_service(self, databricks_scope, storage_account_name_secret, storage_account_key_secret):
        storage_account_name = self.databricks_utils.get_databricks_secret(databricks_scope, storage_account_name_secret)
        storage_account_key = self.databricks_utils.get_databricks_secret(databricks_scope, storage_account_key_secret)
        service = BlobServiceClient(account_url='https://{addsto}.blob.core.windows.net/'.format(addsto = storage_account_name), credential=storage_account_key)
        return service