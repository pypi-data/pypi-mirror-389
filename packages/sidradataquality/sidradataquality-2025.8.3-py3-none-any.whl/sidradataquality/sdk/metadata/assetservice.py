from sidradataquality.sdk.api.sidra.core.utils import Utils as CoreApiUtils
from sidradataquality.sdk.log.logging import Logger
import SidraCoreApiPythonClient

class AssetService():
    def __init__(self, spark):
        self.logger = Logger(spark, self.__class__.__name__)
        sidra_core_api_client = CoreApiUtils(spark).get_SidraCoreApiClient()
        self.metadata_asset_api_instance = SidraCoreApiPythonClient.MetadataAssetsAssetsApi(sidra_core_api_client)

    def get_asset(self, asset_id):
        self.logger.debug(f"[Asset Service][get_asset] Retrieve Asset information for asset id {asset_id}")
        return self.metadata_asset_api_instance.api_metadata_assets_id_get(int(asset_id))