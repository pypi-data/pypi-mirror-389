import sidradataquality.sdk.databricks.utils as databricksutils
import SidraDataQualityApiPythonClient
import sidradataquality.sdk.constants as const

class Utils():
   def __init__(self, spark):
      self.spark = spark
      self.dbutils = databricksutils.Utils(spark).get_db_utils()
     
   def get_SidraDataQualityApiClient(self):
      # Configure OAuth2 access token for authorization: oauth2
      configuration = SidraDataQualityApiPythonClient.Configuration(
         host = self.dbutils.secrets.get(scope=const.SECRET_DATABRICKS_SCOPE, key=const.SECRET_API_URL),
         auth_url = self.dbutils.secrets.get(scope='api', key='auth_url'),
         scope = self.dbutils.secrets.get(scope=const.SECRET_DATABRICKS_SCOPE, key=const.SECRET_API_SCOPE),
         client_id = self.dbutils.secrets.get(scope=const.SECRET_DATABRICKS_SCOPE, key=const.SECRET_CLIENT_ID),
         client_secret = self.dbutils.secrets.get(scope=const.SECRET_DATABRICKS_SCOPE, key=const.SECRET_CLIENT_SECRET)
      )
      return SidraDataQualityApiPythonClient.ApiClient(configuration)  