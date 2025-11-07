import json
import sidradataquality.sdk.constants as const
from sidradataquality.sdk.log.logging import Logger

class DatabricksService():
    def __init__(self, spark):
        self.spark = spark
        self.logger = Logger(spark, self.__class__.__name__)

    def update_validation_status_column(self, failed_pks, table_name, asset_id):
        self.logger.debug(f"[Validation Service][update_validation_status_column] Updating validation column ({const.DATABRICKS_TABLE_ERROR_COLUMN_NAME}) in databricks table (table = {table_name})")
        self._set_failed_rows(failed_pks, table_name)
        self._set_correct_rows(asset_id, table_name)

    def _set_correct_rows(self, asset_id, table_name):
        sql_query = f'UPDATE {table_name} SET {const.DATABRICKS_TABLE_ERROR_COLUMN_NAME} = true WHERE {const.DATABRICKS_TABLE_IS_DELETED_COLUMN_NAME} = false AND {const.DATABRICKS_TABLE_ERROR_COLUMN_NAME} is null AND {const.DATABRICKS_TABLE_ID_ASSET_COLUMN_NAME} = {asset_id}'
        self.logger.debug(f"[Validation Service][update_validation_status_column][_set_correct_rows] Update query to execute: '{sql_query}'")
        self.spark.sql(sql_query)

    def _set_failed_rows(self, failed_pks, table_name):
        sql_filter = self._convert_failed_ids_to_sql_filter(failed_pks)
        sql_query = f'UPDATE {table_name} SET {const.DATABRICKS_TABLE_ERROR_COLUMN_NAME} = false WHERE {const.DATABRICKS_TABLE_IS_DELETED_COLUMN_NAME} = false AND ({sql_filter})'
        if sql_filter:
            self.logger.debug(f"[Validation Service][update_validation_status_column][_set_failed_rows] Update query to execute: '{sql_query}'")
            self.spark.sql(sql_query)
        else:
            self.logger.debug(f"[Validation Service][update_validation_status_column][_set_failed_rows] No errors in table '{table_name}'")

    def _convert_failed_ids_to_sql_filter(self, failed_pks):
        sql_filters = []
        
        for pks in failed_pks:
            data = json.loads(str(pks).replace("'", "\""))
            filter_conditions = []
            for key, value in data.items():
                if isinstance(value, str):
                    filter_conditions.append(f"{key} = '{value}'")
                else:
                    filter_conditions.append(f"{key} = {value}")
            sql_filter = " AND ".join(filter_conditions)
            sql_filters.append(f"({sql_filter})")
        return " OR ".join(sql_filters)
