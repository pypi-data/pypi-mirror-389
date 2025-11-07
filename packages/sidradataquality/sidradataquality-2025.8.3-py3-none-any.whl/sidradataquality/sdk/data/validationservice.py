import json
import time
from datetime import datetime
from dateutil import *

import sidradataquality.sdk.databricks.utils as databricksutils
import sidradataquality.sdk.constants as const
from sidradataquality.sdk.log.logging import Logger
from sidradataquality.sdk.settings.settingsservice import SettingsService
from sidradataquality.sdk.report.reportservice import ReportService
from sidradataquality.sdk.metadata.providerservice import ProviderService
from sidradataquality.sdk.metadata.validationservice import ValidationService as MetadataValidationService
from sidradataquality.sdk.metadata.entityservice import EntityService
from sidradataquality.sdk.metadata.assetservice import AssetService
from sidradataquality.sdk.metadata.dataintakeprocessservice import DataIntakeProcessService
from sidradataquality.sdk.storage.storageservice import StorageService
from sidradataquality.sdk.databricks.databricksservice import DatabricksService
from sidradataquality.sdk.greatexpectations.contextservice import ContextService

from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.core.expectation_configuration import ExpectationConfiguration
from great_expectations.core.run_identifier import RunIdentifier
from great_expectations.checkpoint import Checkpoint

class ValidationService():
    def __init__(self, spark):
        self.logger = Logger(spark, self.__class__.__name__)
        self.spark = spark
        self.databricks_utils = databricksutils.Utils(spark)
        self.dbutils = databricksutils.Utils(spark).get_db_utils()
        self.settings_service = SettingsService(spark)
        self.report_service = ReportService(spark)
        self.metadata_provider_service = ProviderService(spark)
        self.metadata_validation_service = MetadataValidationService(spark)
        self.metadata_entity_service = EntityService(spark)
        self.metadata_asset_service = AssetService(spark)
        self.metadata_dip_service = DataIntakeProcessService(spark)
        self.storage_service = StorageService(spark)
        self.databricks_service = DatabricksService(spark)
        self.context_service = ContextService(spark)

    # intake_run_id: If it is null, the validation is not part of an intake process, it could be a call done from an intake process outside a DIP
    # asset_id: The validation will be done only for this asset_id. The asset cannot be null. If the validation is done for the whole data of the entity (re-execution) it will call to another function (pending)
    #           If intake_run_id is not null, the report will contain all the validation for the specific intake execution. 
    #           If intake_run_id is null and the asset_id is not null, the report will contain only the results for this asset_id
    #           If intake_run_id is null and the asset_id is null, the report will contain the results for the whole entity_id -> execute_validations_for_entity(self, entity_id, execution_date)
    # entity_id: It cannot be null. The validations are associated to this entity and the asset_id -> for a whole entity -> execute_validations_for_entity(self, entity_id, execution_date)
    # execution_date: It cannot be null. It could be the date for the intake execution.
    def execute_validations_for_entity_asset(self, entity_id, asset_id, intake_run_id, execution_date):
        # If service is not deployed, we skip the execution
        if not self.databricks_utils.service_is_enabled():
            return False

        entity = self.metadata_entity_service.get_entity(entity_id)
        self.logger.debug(f"[Validation Service][execute_validations_for_entity] Check if there are validations for entity {entity.name}")
        entity_suite = self.metadata_entity_service.get_entity_suite(entity.item_id)
        
        # If there is no suite for the entity, we skip the execution
        if entity_suite is None or entity_suite.is_disabled is True:
            self.logger.debug(f"[Validation Service][execute_validations_for_entity] There are not validations or there are not enabled for entity {entity.name}")
            return False
        
        entity_suite_name = entity_suite.name
        asset = self.metadata_asset_service.get_asset(asset_id)
        entity_pk_columns = self.metadata_entity_service.get_entity_primary_keys(entity.id)
        entity_validations = self.metadata_validation_service.get_validations_by_entity(entity.item_id)
        provider = self.metadata_provider_service.get_provider_by_id(entity.id_provider)
        table_name = f"{provider.database_name}.{entity.table_name}"
        dip = self.metadata_dip_service.get_dip(entity.id_data_intake_process)
        self.logger.debug(f"[Validation Service][execute_validations_for_entity] Validate asset '{asset.id}' for entity '{entity.name}' with table name '{table_name}'")
        triggered_by = const.VALIDATION_TRIGGERED_BY_DIP_EXECUTION if dip is not None else const.VALIDATION_TRIGGERED_BY_LANDING_INTAKE

        # Get/Create validation context
        context = self.context_service.get_context(provider, entity, asset_id, intake_run_id, execution_date)
        report_path = self.context_service.report_path
        result_path = self.context_service.result_path

        asset_id = str(asset.id)
        self.metadata_validation_service.set_asset_results(result_path, entity.item_id, asset.item_id, const.ASSET_VALIDATION_STATUS_PENDINGVALIDATION)

        # Check all data vs sampled data
        self.metadata_validation_service.set_asset_results(result_path, entity.item_id, asset.item_id, const.ASSET_VALIDATION_STATUS_INPROGRESS)
        check_full_asset, error_count = self.check_sampled_data_if_required(context, entity.table_name, entity_suite_name, entity_validations, table_name, asset.id, f"{asset_id}-sampled")

        if check_full_asset is False:
            # Sampling required and sampled data with to much errors
            self.logger.debug(f"[Validation Service][execute_validations_for_entity][Asset_{asset.id}] Sampled data with to much errors")
            self.metadata_validation_service.set_asset_results(result_path, entity.item_id, asset.item_id, const.ASSET_VALIDATION_STATUS_ERROR, error_count)
        else:
            # Check all data
            self.logger.debug(f"[Validation Service][execute_validations_for_entity][Asset_{asset.id}] Execute validations for all data")
            df_to_validate = self.get_validation_df(context, entity.table_name, table_name, asset.id)
            validation_result_data, validation_result = self.execute_validations(context, df_to_validate, entity_suite_name, entity_validations, asset_id, entity_pk_columns)

            # Save HTML report in storage account
            file_name = f"{asset_id}.html"
            self.logger.debug(f"[Validation Service][execute_validations_for_entity][Asset_{asset.id}] Report path: {report_path}")
            self.storage_service.upload_file_to_data_quality_storage(file_name, report_path, validation_result_data[const.VALIDATION_RESULT_DATA_REPORT], const.STORAGE_DEFAULT_CONTAINER)

            # Save JSON results in storage account
            file_name = f"{asset_id}.json"
            self.logger.debug(f"[Validation Service][execute_validations_for_entity][Asset_{asset.id}] Results path: {result_path}")
            self.storage_service.upload_file_to_data_quality_storage(file_name, result_path, str(validation_result), const.STORAGE_DEFAULT_CONTAINER)
            
            # Update SidraPassedValidation in Databricks
            self.databricks_service.update_validation_status_column(validation_result_data[const.VALIDATION_RESULT_DATA_ROWS_FAILED_IDS], table_name, asset.id)

            # Update entity delta and asset status in database
            self.logger.debug(f"[Validation Service][execute_validations_for_entity][Asset_{asset.id}] Update validation errors and entity delta")
            self.metadata_validation_service.set_asset_results(result_path, entity.item_id, asset.item_id, const.ASSET_VALIDATION_STATUS_VALIDATED, validation_result_data[const.VALIDATION_RESULT_DATA_ROWS_FAILED_COUNT], file_name)
            self.metadata_validation_service.set_entity_delta(entity.item_id)

        # Update Validation Report tracking
        dip_item_id = dip.item_id if dip is not None else None
        self.metadata_validation_service.set_validation_report_tracking(triggered_by, dip_item_id, intake_run_id, entity.item_id, execution_date, self.context_service.base_path)
        return True

    def get_validation_df(self, context, entity_name, table_name, asset_id, only_count = False, sample = 0.0):
        self.logger.debug(f"[Validation Service][get_validation_df] Get validation dataframe from {table_name} (asset = {asset_id})")

        df = self.spark.sql(f"SELECT * FROM {table_name} WHERE {const.DATABRICKS_TABLE_IS_DELETED_COLUMN_NAME} = false AND {const.DATABRICKS_TABLE_ID_ASSET_COLUMN_NAME} = {asset_id}")
        df_name = str(asset_id)

        if sample > 0.0:
            self.logger.debug(f"[Validation Service][get_validation_df] Applying sampling {sample}")
            df_name = f"{df_name}_sampled"
            df = df.sample(False, sample, False)

        if only_count is True:
            return df.count()
        else:
            return context.sources.add_or_update_spark(name=entity_name).add_dataframe_asset(
                name=asset_id,
                dataframe=df)
    
    def get_information_from_result(self, validation_result_details, entity_pk_columns, df_row_count):
        self.logger.debug(f"[Validation Service][get_information_from_result] Getting information from validation results")
        failed_rows_per_expectation = []
        failed_rows_ids = []

        statistics = validation_result_details.get_statistics()[const.GE_STATISTICS][validation_result_details.list_validation_result_identifiers()[0]]
        validations_result = validation_result_details.list_validation_results()[0]  

        for validation_results in validations_result[const.GE_VALIDATION_RESULTS]:
            result = validation_results[const.GE_VALIDATION_RESULT]
            if result:
                failed_rows_per_expectation.append({
                    "expectation": validation_results[const.GE_VALIDATION_RESULTS_EXPECTATION_CONFIG][const.GE_VALIDATION_RESULTS_EXPECTATION_CONFIG_TYPE],
                    "failed_rows": result.get(const.GE_VALIDATION_RESULT_UNEXPECTED_VALUES, [])
                })

        for expectation_failed_rows in failed_rows_per_expectation:
            failed_rows = expectation_failed_rows['failed_rows']
            for failed_row in failed_rows:
                row_pks = {}
                for pk_column in entity_pk_columns:
                    row_pks[pk_column] = failed_row[pk_column]
                failed_rows_ids.append(row_pks) if row_pks not in failed_rows_ids else failed_rows_ids

        return {
            const.VALIDATION_RESULT_DATA_ROWS_FAILED_PERCENT: round((len(failed_rows_ids) * 100 / df_row_count), 2),
            const.VALIDATION_RESULT_DATA_VALIDATIONS_FAILED: statistics[const.GE_STATISTICS_UNSUCCESSFUL_EXPECTATIONS],
            const.VALIDATION_RESULT_DATA_REPORT: self.report_service.render_with_custom_style(validations_result),
            const.VALIDATION_RESULT_DATA_ROWS_FAILED_IDS: failed_rows_ids,
            const.VALIDATION_RESULT_DATA_ROWS_FAILED_COUNT: len(failed_rows_ids)
        }

    # https://greatexpectations.io/blog/id-pk-helps-you-find-your-problem-data
    def execute_validations(self, context, df_to_validate, entity_suite, entity_validations, execution_id, pk_columns = None):
        self.logger.debug(f"[Validation Service][execute_validations] Setting up validations for execution (suite = {entity_suite}, execution id = {execution_id})")

        batch_request = df_to_validate.build_batch_request()
        context.add_or_update_expectation_suite(expectation_suite_name=entity_suite)

        validator = context.get_validator(
            batch_request=batch_request,
            expectation_suite_name=entity_suite,
        )

        for validation in entity_validations:
            validator.expectation_suite.add_expectation(ExpectationConfiguration(expectation_type=validation.expectation_type.name, kwargs=json.loads(validation.parameters)))
        
        validator.save_expectation_suite(discard_failed_expectations=False)
        
        if pk_columns is None: # Take all columns as PK if not specified
            self.logger.debug(f"[Validation Service][execute_validations] No primary key specified, taking all columns as identifiers (except binary ones due to GE limitations)")
            pk_columns = [col for col, data_type in df_to_validate.dataframe.dtypes if data_type not in ["binary"]] # Binary not supported by GE
        
        checkpoint = Checkpoint(
            name=str(execution_id),
            run_name_template=str(execution_id),
            data_context=context,
            batch_request=batch_request,
            expectation_suite_name=entity_suite,
            action_list=[
                {
                    "name": "store_validation_result",
                    "action": { "class_name": "StoreValidationResultAction" },
                },
                { 
                    "name": "update_data_docs", 
                    "action": { "class_name": "UpdateDataDocsAction" }
                },
            ],
            runtime_configuration= {
                "result_format": {
                    "result_format": "COMPLETE", 
                    "unexpected_index_column_names": pk_columns
                }
            }
        )

        context.add_or_update_checkpoint(checkpoint=checkpoint)

        self.logger.debug(f"[Validation Service][execute_validations] Executing validations ({checkpoint.name})")
        checkpoint_result = checkpoint.run()
        
        return self.get_information_from_result(checkpoint_result, pk_columns, df_to_validate.dataframe.count()), checkpoint_result

    def check_sampled_data_if_required(self, context, entity_name, entity_suite, entity_validations, table_name, asset_id, run_id):
        check_all_asset = True
        failed_rows_count = '0'
        settings = self.settings_service.get_validation_settings()
        df_to_validate_count = self.get_validation_df(context, entity_name, table_name, asset_id, True)

        if df_to_validate_count > int(settings[const.SETTINGS_SAMPLING_ROW_COUNT_THRESHOLD]): # Too big, checking sampled data first
            sampling_percentage = float(settings[const.SETTINGS_SAMPLING_PERCENTAGE]) / 100.0
            sampled_df_to_validate = self.get_validation_df(context, entity_name, table_name, asset_id, False, sampling_percentage)
            validation_result_data, validation_result = self.execute_validations(context, sampled_df_to_validate, entity_suite, entity_validations, run_id)
            failed_rows_count = validation_result_data[const.VALIDATION_RESULT_DATA_ROWS_FAILED_COUNT]

            if float(validation_result_data[const.VALIDATION_RESULT_DATA_ROWS_FAILED_PERCENT]) > float(settings[const.SETTINGS_SAMPLING_MAX_ERROR_PERCENTAGE]): # To much errors, asset marked as error
                check_all_asset = False

        return check_all_asset, failed_rows_count