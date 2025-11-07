from sidradataquality.sdk.api.sidra.core.utils import Utils as CoreApiUtils
from sidradataquality.sdk.api.sidra.dataquality.utils import Utils as DataQualityApiUtils
from sidradataquality.sdk.log.logging import Logger
import sidradataquality.sdk.constants as const
import SidraCoreApiPythonClient
import SidraDataQualityApiPythonClient

class EntityService():
  def __init__(self, spark):
    self.logger = Logger(spark, self.__class__.__name__)
    sidra_core_api_client = CoreApiUtils(spark).get_SidraCoreApiClient()
    sidra_dataquality_api_client = DataQualityApiUtils(spark).get_SidraDataQualityApiClient()
    self.metadata_entity_api_instance = SidraCoreApiPythonClient.MetadataEntitiesEntityApi(sidra_core_api_client)
    self.validation_suite_api_instance = SidraDataQualityApiPythonClient.SidraDataQualityApiSValidationSuitesApi(sidra_dataquality_api_client)

  def get_entity_primary_keys(self, id_entity):
    self.logger.debug(f"[Entity Service][get_entity_primary_keys] Retrieve primary key for entity {id_entity}")
    entity_columns = self.metadata_entity_api_instance.api_metadata_entities_id_entity_attributes_get(int(id_entity))
    entity_pks = [col.name for col in entity_columns if col.is_primary_key]
    entity_pks.append(const.DATABRICKS_TABLE_ID_ASSET_COLUMN_NAME)
    return entity_pks
  
  def get_entity_suite(self, item_id_entity):
    self.logger.debug(f"[Entity Service][get_entity_suite] Retrieve Entity suite for entity item id {item_id_entity}")
    suites = self.validation_suite_api_instance.api_validations_suites_get(field='IdEntity', text=str(item_id_entity))
    if len(suites) > 0:
      return suites[0]
    return None
  
  def get_entity(self, id_entity):
    self.logger.debug(f"[Entity Service][get_entity] Retrieve Entity information for entity id {id_entity}")
    return self.metadata_entity_api_instance.api_metadata_entities_id_get(int(id_entity))
    
