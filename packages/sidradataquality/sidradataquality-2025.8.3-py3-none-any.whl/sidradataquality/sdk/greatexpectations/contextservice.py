import sidradataquality.sdk.constants as const
from sidradataquality.sdk.log.logging import Logger
from sidradataquality.sdk.storage.storageservice import StorageService

import great_expectations as gx

class ContextService():
    def __init__(self, spark):
        self.logger = Logger(spark, self.__class__.__name__)
        self.spark = spark
        self.storage_service = StorageService(spark)
        self.context_path = ''
        self.report_path = ''
        self.result_path = ''
        self.base_path = ''

    def get_context(self, provider, entity, asset_id, intake_run_id, execution_date):
        self.logger.debug("[Context Service][get_context] Get Great Expectation Context")
        # In order to maintain backwards compatibility we will check if the runId exist or the assetId exist to configure the context
        if (intake_run_id is None or intake_run_id == ''):
            # validation for an asset using the old report (deprecated in favor of reports at provider level)
            #reports/<providername>/<entityname>/<date>/<file.html>
            #results/<providername>/<entityname>/<date>/<file.json>
            self.context_path = self._get_context_path(f'{provider.database_name}/{entity.table_name}'.lower())
            storage_entity_path = f'{provider.database_name}/{entity.table_name}/{execution_date.strftime("%Y/%m/%d")}'.lower()
            self.report_path = f"{const.STORAGE_REPORTS_FOLDER}/{storage_entity_path}"
            self.result_path = f"{const.STORAGE_RESULTS_FOLDER}/{storage_entity_path}"
            self.base_path = f"{self.report_path}/{asset_id}.html"
            context = gx.get_context(context_root_dir=self.context_path)
        else:
            # validation for an asset but the report will be generated at provider level
            base_folder = f'{const.STORAGE_REPORTS_SUBFOLDER_BY_PROVIDER}'
            process_identifier = f'{provider.item_id}/{execution_date.strftime("%Y/%m/%d/%H%M%S")}/{intake_run_id}'
            entity_path = f'{provider.database_name}_{entity.table_name}/{asset_id}/{execution_date.strftime("%Y%m%d%H%M%S")}'

            self.context_path = self._get_context_path(f'{provider.database_name}/{intake_run_id}/{entity.table_name}')
            self.base_path = self._get_storage_account_base_path(base_folder, process_identifier)
            self.report_path = self._get_storage_account_full_path(self.base_path, f'{const.STORAGE_REPORTS_FOLDER}/{const.STORAGE_VALIDATIONS_FOLDER}/{entity_path}')
            self.result_path = self._get_storage_account_full_path(self.base_path, f'{const.STORAGE_RESULTS_FOLDER}/{entity_path}')
            context = gx.get_context(context_root_dir=self.context_path)

        return context 

    def _get_context_path(self, base_folder):
        path = f"/dbfs/{const.STORAGE_DEFAULT_CONTAINER}/{base_folder}/gx/"
        self.logger.debug(f"[Context Service][_get_context_path] Context path: {path}")
        return path   
    
    #ProviderReports/<providerItemId>/<year>/<month>/<day>/<time>/<DIPRunId>/reports/validations/<database_name>_<table_name>/<asset_id>/YYYYmmddHHMMSS/<file.html>
    #ProviderReports/<providerItemId>/<year>/<month>/<day>/<time>/<DIPRunId>/results/<database_name>_<table_name>/<asset_id>/YYYYmmddHHMMSS/<file.json>
    def _get_storage_account_base_path(self, base_folder, process_identifier):
        path = f"{base_folder}/{process_identifier}".lower()
        return path
    
    def _get_storage_account_full_path(self, base_folder, file_location):
        path = f"{base_folder}/{file_location}".lower()
        self.logger.debug(f"[Context Service][_get_storage_account_report_path] Report path: {path}")
        return path