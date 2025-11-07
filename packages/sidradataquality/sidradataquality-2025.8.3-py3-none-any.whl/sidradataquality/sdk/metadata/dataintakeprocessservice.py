from sidradataquality.sdk.api.sidra.core.utils import Utils as CoreApiUtils
from sidradataquality.sdk.log.logging import Logger
import SidraCoreApiPythonClient

class DataIntakeProcessService():
  def __init__(self, spark):
    self.logger = Logger(spark, self.__class__.__name__)
    sidra_core_api_client = CoreApiUtils(spark).get_SidraCoreApiClient()
    self.metadata_dip_api_instance = SidraCoreApiPythonClient.MetadataDataIntakeProcessesDataIntakeProcessApi(sidra_core_api_client)

  def get_dip(self, id_dip):
    self.logger.debug(f"[DIP Service][get_dip] Retrieve DIP information for dip id {id_dip}")
    return self.metadata_dip_api_instance.api_metadata_data_intake_processes_id_get(int(id_dip))