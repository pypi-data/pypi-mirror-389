from sidradataquality.sdk.api.sidra.core.utils import Utils as CoreApiUtils
from sidradataquality.sdk.api.sidra.dataquality.utils import Utils as DataQualityApiUtils
from sidradataquality.sdk.log.logging import Logger
import SidraCoreApiPythonClient
import SidraDataQualityApiPythonClient

class ProviderService():
    def __init__(self, spark):
        self.logger = Logger(spark, self.__class__.__name__)
        sidra_core_api_client = CoreApiUtils(spark).get_SidraCoreApiClient()
        sidra_dataquality_api_client = DataQualityApiUtils(spark).get_SidraDataQualityApiClient()
        self.validation_provider_api_instance = SidraDataQualityApiPythonClient.SidraDataQualityApiSMetadataProvidersApi(sidra_dataquality_api_client)
        self.metadata_provider_api_instance = SidraCoreApiPythonClient.MetadataProvidersProviderApi(sidra_core_api_client)

    def get_assets_to_validate(self, provider_item_id, asset_status):
        self.logger.debug(f"[Provider Service][get_assets_to_validate] Retrieve assets to validate in status {asset_status} for provider {provider_item_id}")
        return self.validation_provider_api_instance.api_providers_provider_item_id_assets_to_validate_get(str(provider_item_id), asset_status=str(asset_status))
    
    def get_provider_by_id(self, provider_id):
        self.logger.debug(f"[Provider Service][get_provider_by_id] Retrieve provider information for provider id '{provider_id}'")
        return self.metadata_provider_api_instance.api_metadata_providers_id_get(int(provider_id))
    
    def get_provider_by_item_id(self, provider_item_id):
        self.logger.debug(f"[Provider Service][get_provider_by_item_id] Retrieve provider information for provider itemId '{provider_item_id}'")
        result = self.metadata_provider_api_instance.api_metadata_providers_get(field='ItemId', text=str(provider_item_id))
        if result.total_items == 1:
            return result.items[0]
        return None