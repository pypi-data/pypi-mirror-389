from sidradataquality.sdk.databricks.utils import Utils
from sidradataquality.sdk.security.auth import Auth
from sidradataquality.sdk.api.sidra.dataquality.utils import Utils as DataQualityApiUtils
from sidradataquality.sdk.log.logging import Logger
import requests
import json
import SidraDataQualityApiPythonClient

class SettingsService():
    def __init__(self, spark):
        self.logger = Logger(spark, self.__class__.__name__)
        self.spark = spark
        self.databricks_utils = Utils(spark)
        self.auth = Auth(spark)
        self.token = self.auth.get_token()
        sidra_dataquality_api_client = DataQualityApiUtils(spark).get_SidraDataQualityApiClient()
        self.validation_management_api_instance = SidraDataQualityApiPythonClient.SidraDataQualityApiSManagementSettingsApi(sidra_dataquality_api_client)
        
    def get_dsu_secret(self, secret_name):
        dsu_akv = self.databricks_utils.get_databricks_secret('resources', 'dsu_key_vault_name')
        url = 'https://{key_vault}.vault.azure.net/secrets/{secret_name}?api-version=2016-10-01'.format(key_vault=dsu_akv, secret_name=secret_name)
        
        try: 
            headers = {'Authorization': f'Bearer {self.token}'}
            r = requests.get(url=url, headers=headers)
        except: # TODO: See if we can catch a specific exception
            self.token = self.auth.get_token()
            headers = {'Authorization': f'Bearer {self.token}'}
            r = requests.get(url=url, headers=headers)
        
        data = r.json()
        if ('value' in data):
            return data['value']
        else:
            raise(Exception(data))
    
    def get_validation_settings(self):
        self.logger.debug(f"[Settings Service][get_validation_settings] Get validation settings")
        settings = self.validation_management_api_instance.api_management_settings_get()
        
        settings_dict = {}
        for setting in settings:
            settings_dict[str(setting.key)] = str(setting.value)
            
        return settings_dict
    