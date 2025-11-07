import shutil
from datetime import datetime
from dateutil.parser import parse
from pyspark.sql.functions import udf, collect_list, explode, col
from sidradataquality.sdk.log.logging import Logger
from sidradataquality.sdk.metadata.validationservice import ValidationService as MetadataValidationService
from sidradataquality.sdk.storage.storageservice import StorageService
from sidradataquality.sdk.metadata.providerservice import ProviderService
import sidradataquality.sdk.constants as const
import sidradataquality.sdk.databricks.utils as databricksutils

import great_expectations as gx
from great_expectations.render.renderer import ValidationResultsPageRenderer, ProfilingResultsPageRenderer, ExpectationSuitePageRenderer
from great_expectations.render.view import DefaultJinjaPageView

#This function cannot be included in the class because it launch the error: 
#Could not serialize object: PySparkRuntimeError: [CONTEXT_ONLY_VALID_ON_DRIVER] It appears that you are attempting to reference SparkContext from a broadcast variable, action, or transformation. SparkContext can only be used on the driver, not in code that it run on workers. For more information, see SPARK-5063.
def _generate_html_section(success, run_time, run_name, datasource_name, expectation_suite_name):
    long_date = run_time.strftime(const.DATETIME_LONG_FORMAT)
    short_date = run_time.strftime(const.DATETIME_SHORT_FORMAT)
    timestamp = int(run_time.timestamp())
    replaced_section = const.SECTION_TEMPLATE.replace(const.PLACEHOLDER_RUN_TIME_LONG_FORMAT, long_date).replace(const.PLACEHOLDER_RUN_TIME_SORT, str(timestamp))
    replaced_section = replaced_section.replace(const.PLACEHOLDER_RUN_NAME, run_name).replace(const.PLACEHOLDER_RUN_TIME_SHORT_FORMAT, short_date)
    replaced_section = replaced_section.replace(const.PLACEHOLDER_DATASOURCE_NAME, datasource_name).replace(const.PLACEHOLDER_EXPECTATION_SUITE_NAME, expectation_suite_name)
    if success:
        replaced_section = replaced_section.replace(const.PLACEHOLDER_ICON_RESULT, const.ICON_SUCCESS).replace(const.PLACEHOLDER_RESULT_TEXT, const.RESULT_TEXT_SUCCESS)
    else:
        replaced_section = replaced_section.replace(const.PLACEHOLDER_ICON_RESULT, const.ICON_FAILED).replace(const.PLACEHOLDER_RESULT_TEXT, const.RESULT_TEXT_FAILED)
    return replaced_section    

class ReportService():
    def __init__(self, spark):
        self.logger = Logger(spark, self.__class__.__name__)
        self.spark = spark
        self.dbutils = databricksutils.Utils(spark).get_db_utils()
        self.metadata_validation_service = MetadataValidationService(spark)
        self.storage_service = StorageService(spark)
        self.metadata_provider_service = ProviderService(spark)   
   
    def render(self, validations_result):
        self.logger.debug(f"[Report Service][render] Render report from results")
        return DefaultJinjaPageView().render(ValidationResultsPageRenderer().render(validations_result))

    def render_with_custom_style(self, validations_result):
        self.logger.debug(f"[Report Service][apply_custom_css_style] Apply custom CSS style to report")
        html_content = self.render(validations_result)
        style_content = self._get_custom_style()
        return html_content.replace('<style></style>', f'<style>{style_content}</style>')

    def generate_report(self, provider_item_id, run_id, execution_date):
        self.logger.debug(f'[Report Service][generate_report] Get Report for Provider: "{provider_item_id}" and run id "{run_id}"')
        report = self.metadata_validation_service.get_validation_report_location(run_id)
        if report is None:
            self.logger.debug(f'[Report Service][generate_report] There is not information about the report associated to the intake process: "{run_id}"')
            return 
        reports_root_path = report.report_path
        report_path = f'{reports_root_path}/{const.STORAGE_REPORTS_FOLDER}'
        result_path = f'{self.storage_service.get_data_quality_url()}{reports_root_path}/{const.STORAGE_RESULTS_FOLDER}'
        
        self.logger.debug(f'[Report Service][generate_report] Get Provider ItemId: "{provider_item_id}"')
        provider = self.metadata_provider_service.get_provider_by_item_id(provider_item_id)
        provider_title = provider_item_id if provider is None else provider.database_name

        self.logger.debug(f'[Report Service][generate_report] Access to files located on: "{result_path}"')
        self.storage_service.set_access_to_dq_storage()
        df = self.spark.read.option("multiline", "true").option("recursiveFileLookup", "true").json(result_path)
        data = df.select("success", col("run_id.run_time"), col("run_id.run_name"), col("checkpoint_config.batch_request.datasource_name"), col("checkpoint_config.expectation_suite_name"))

        self.logger.debug(f'[Report Service][generate_report] Generate report index based on files in location: "{report_path}"')
        html_section_list = self._get_html_section_list(data, execution_date)

        section1block2_1data = ','.join(html_section_list)
        section1block1_header = provider_title

        content = self._get_report_index_template()
        content = content.replace(const.PLACEHOLDER_DATA, section1block2_1data).replace(const.PLACEHOLDER_HEADER, section1block1_header)

        self.logger.debug(f'[Report Service][generate_report] Create report index for provider: "{provider_title}" in "{report_path}"')
        self.storage_service.upload_file_to_data_quality_storage(const.INDEX_REPORT_FILE_NAME, report_path, content)

        self.logger.debug(f'[Report Service][generate_report] Generate compressed file for provider: "{provider_title}" in "{reports_root_path}"')
        self._generate_compressed_file(reports_root_path, run_id)

    def _get_html_section_list(self, data, execution_date):
        udf_func = udf(lambda success, run_time, run_name, datasource_name, expectation_suite_name: _generate_html_section(success, execution_date, run_name, datasource_name, expectation_suite_name))
        data = data.withColumn("html_section", udf_func(data["success"], data["run_time"], data["run_name"], data["datasource_name"], data["expectation_suite_name"]))
        html_section_list = data.select(collect_list('html_section')).first()[0]
        return html_section_list

    def _generate_compressed_file(self, reports_root_path, run_id):
        mount_point = self.storage_service.get_data_quality_mount_point(reports_root_path)
        try:
          mount_path = f'/dbfs{mount_point}/{const.STORAGE_REPORTS_FOLDER}'
          destination_file = f'{const.ZIP_REPORT_FILE_NAME}_{run_id}'
          result_file = shutil.make_archive(root_dir=mount_path, format='zip', base_name=destination_file)
          source = f'file:///{result_file}'
          destination = f'dbfs:{mount_point}'
          self.logger.debug(f'Copy compressed file from {result_file} to {destination}')
          self.dbutils.fs.cp(source, destination)
          self.logger.debug(f'Remove temporal file {result_file}')
          self.dbutils.fs.rm(source)
        finally:
          self.dbutils.fs.unmount(mount_point)

    def _get_report_index_template(self):
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
  <title>Data Docs created by Great Expectations</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta charset="UTF-8">
  <title></title>

  <link rel="stylesheet" href="https://unpkg.com/bootstrap-table@1.19.1/dist/bootstrap-table.min.css">
  <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" />
  <link rel="stylesheet" type="text/css"
    href="https://unpkg.com/bootstrap-table@1.19.0/dist/extensions/filter-control/bootstrap-table-filter-control.min.css">
  <link rel="stylesheet" type="text/css"
    href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datepicker/1.9.0/css/bootstrap-datepicker.min.css">
  <link rel="stylesheet"
    href="https://cdn.jsdelivr.net/npm/@forevolve/bootstrap-dark@1.1.0/dist/css/bootstrap-prefers-dark.css" />

  <style>
    body {
      position: relative;
    }
    
    .container {
      padding-top: 50px;
    }
    
    .sticky {
      position: -webkit-sticky;
      position: sticky;
      top: 90px;
      z-index: 1;
    }
    
    .ge-section {
      clear: both;
      margin-bottom: 30px;
      padding-bottom: 20px;
    }
    
    .popover {
      max-width: 100%;
    }
    
    .cooltip {
      display: inline-block;
      position: relative;
      text-align: left;
      cursor: pointer;
    }
    
    .cooltip .top {
      min-width: 200px;
      top: -6px;
      left: 50%;
      transform: translate(-50%, -100%);
      padding: 10px 20px;
      color: #FFFFFF;
      background-color: #222222;
      font-weight: normal;
      font-size: 13px;
      border-radius: 8px;
      position: absolute;
      z-index: 99999999 !important;
      box-sizing: border-box;
      box-shadow: 0 1px 8px rgba(0, 0, 0, 0.5);
      display: none;
    }
    
    .cooltip:hover .top {
      display: block;
      z-index: 99999999 !important;
    }
    
    .cooltip .top i {
      position: absolute;
      top: 100%;
      left: 50%;
      margin-left: -12px;
      width: 24px;
      height: 12px;
      overflow: hidden;
    }
    
    .cooltip .top i::after {
      content: '';
      position: absolute;
      width: 12px;
      height: 12px;
      left: 50%;
      transform: translate(-50%, -50%) rotate(45deg);
      background-color: #222222;
      box-shadow: 0 1px 8px rgba(0, 0, 0, 0.5);
    }
    
    ul {
      padding-inline-start: 20px;
    }
    
    .show-scrollbars {
      overflow: auto;
    }
    
    td .show-scrollbars {
      max-height: 80vh;
    }
    
    /*.show-scrollbars ul {*/
    /*  padding-bottom: 20px*/
    /*}*/
    
    .show-scrollbars::-webkit-scrollbar {
      -webkit-appearance: none;
    }
    
    .show-scrollbars::-webkit-scrollbar:vertical {
      width: 11px;
    }
    
    .show-scrollbars::-webkit-scrollbar:horizontal {
      height: 11px;
    }
    
    .show-scrollbars::-webkit-scrollbar-thumb {
      border-radius: 8px;
      border: 2px solid white; /* should match background, can't be transparent */
      background-color: rgba(0, 0, 0, .5);
    }
    
    #ge-cta-footer {
      opacity: 0.9;
      border-left-width: 4px
    }
    
    .carousel-caption {
        position: relative;
        left: 0;
        top: 0;
    }
    
    footer {
      position: fixed;
      border-top: 1px solid #98989861;
      bottom: 0;
      left: 0;
      right: 0;
      height: 32px;
      padding: 4px;
      font-size: 14px;
      text-align: right;
      width: 100%;
      background: white;
      z-index: 100000;
    }
    footer a {
      padding-right: 8px;
      color: #ff6210;
      font-weight: 600;
    }
    
    footer a:hover {
        color: #bc490d;
        text-decoration: underline;
    }
    
    /* some css overrides for dark mode*/
    @media (prefers-color-scheme: dark) {
      .table {
        color: #f1f1f1 !important;
        background-color: #212529;
      }
      .table-bordered{
        border: #f1f1f1;
      }
      .table-hover tbody tr:hover {
        color: #f1f1f1;
        background-color: rgba(255,255,255,.075);
      }
      .form-control:disabled,
      .form-control[readonly]{
        background-color: #343a40;
        opacity: .8;
      }
    
      .bg-light {
        background: inherit !important;
      }
    
      .code-snippet {
        background: #CDCDCD !important;
      }
    
      .alert-secondary a {
        color: #0062cc;
      }
    
      .alert-secondary a:focus, .alert-secondary a:hover{
        color: #004fa5;
      }
    
      .navbar-brand a {
        background: url('https://great-expectations-web-assets.s3.us-east-2.amazonaws.com/full_logo_dark.png') 0 0 no-repeat;
        background-size: 228.75px 50px;
        display: inline-block
      }
      .navbar-brand a img {
        visibility:hidden
      }
      footer {
        border-top: 1px solid #ffffff61;
        background: black;
        z-index: 100000;
      }
      footer a {
        color: #ff6210;
      }
    
      footer a:hover {
        color: #ff6210;
      }
    }
  </style>

  <style>
:root {
  --primary: #8672fa;
  --primary-hover: #9887fb;
  --secondary: #66e1e4;
  --secondary-hover: #57bfc2;
  --white: #ffffff;
  --black: #15212f;
  --gray: #e9ecf0;
  --danger: #cc3366;
}

body {
  color: var(--black);
}

/* NAVBAR */

.navbar {
  background: var(--white);
}

.navbar-brand {
  width: 150px;
  height: 50px;
  background-repeat: no-repeat;
  background-size: contain;
  background-position: center;
  background-image: url(data:image/png;base64,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);
}

.navbar-brand.h-100 {
  height: 50px !important;
}

.navbar-brand a {
  display: none;
}

.navbar-expand-md::before {
  position: absolute;
  content: "powered by";
  top: 2px;
  right: 0;
  width: 200px;
  height: auto;
  padding-left: 25px;
  font-size: 0.8em;
  z-index: 4;
  text-align: left;
  background: var(--white);
}

.navbar-expand-md::after {
  position: absolute;
  content: "";
  top: 20px;
  right: 0px;
  width: 200px;
  height: 40px;
  background: var(--white);
  background-image: url("https://great-expectations-web-assets.s3.us-east-2.amazonaws.com/logo-long.png?d=20221102T130030.199543Z");
  background-repeat: no-repeat;
  background-size: contain;
  z-index: 5;
}

/* BUTTONS */

.btn-primary {
  color: var(--white) !important;
  background-color: var(--primary);
  border-color: var(--primary);
  cursor: pointer;
}

.btn-primary:hover,
.btn-primary.active,
.btn-primary:active {
  background-color: var(--primary-hover) !important;
  border-color: var(--primary-hover) !important;
}

.btn-warning,
.btn-info,
.btn-secondary {
  background-color: var(--secondary);
  border-color: var(--secondary);
  color: var(--white) !important;
}

.btn-warning:hover,
.btn-warning.active,
.btn-warning:active,
.btn-info:hover,
.btn-info.active,
.btn-info:active,
.btn-secondary:hover,
.btn-secondary.active,
.btn-secondary:active {
  background-color: var(--secondary-hover) !important;
  border-color: var(--secondary-hover) !important;
  color: var(--white) !important;
}

.btn-primary:focus,
.btn-primary.focus,
.btn-info:focus,
.btn-secondary:focus,
.btn-warning:focus {
  box-shadow: none !important;
}

/* TEXTS */

a {
  color: var(--primary) !important;
}

.alert-secondary {
  background-color: var(--gray) !important;
}

.text-danger {
  color: var(--danger) !important;
}

.table {
  color: var(--black) !important;
}

.alert a {
  word-break: break-word;
}

/* RESPONSIVE */

@media (width < 1500px) {
  .nav-item {
    padding-right: 10px !important;
    padding-left: 10px !important;
  }
  .nav-link {
    padding: 0.4rem 0.5rem;
  }
  .breadcrumb {
    font-size: 0.9em;
  }
}

@media (width < 1100px) {
  .navbar::before {
    top: 8px;
    width: 150px;
    padding-left: 20px;
    font-size: 0.7em;
  }
  .navbar::after {
    top: 25px;
    width: 150px;
  }
  .breadcrumb {
    font-size: 0.8em;
  }
}

@media (width < 950px) {
  .navbar::before {
    top: 11px;
    width: 120px;
    padding-left: 16px;
    font-size: 0.6em;
  }
  .navbar::after {
    top: 25px;
    width: 120px;
  }
}

@media (width < 875px) {
  .breadcrumb {
    font-size: 0.8em;
  }
}

@media (width < 800px) {
  .navbar-brand {
    width: 120px;
  }
  .breadcrumb {
    font-size: 0.7em;
  }
}

@media (prefers-color-scheme: dark) {
  body {
    color: #ffffff; /* Texto blanco o claro */
  }
  .breadcrumb-item.active {
    color: #ced4da;
  }
  .table {
    color: #ffffff !important;
  }
  .alert-secondary {
    color: #383d41;
    background-color: #e2e3e5 !important;
    border-color: #d6d8db;
  }
  .navbar {
    background: transparent;
  }
  .navbar-expand-md::after {
    display: none;
  }
  .navbar-expand-md::before {
    background: transparent;
  }
  .navbar-brand {
    background-image: url(data:image/png;base64,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);
  }
  .navbar::before {
    background-color: rgb(25, 29, 33);
    top: 5px;
    width: 210px;
    padding-left: 32px;
  }
  .navbar-brand a {
    background-color: rgb(25, 29, 33);
    display: inline-block;
    position: fixed;
    top: 18px;
    right: 0;
    width: 210px;
    height: 50px;
  }
  .navbar-brand a img {
    width: 100%;
  }
}
@media (prefers-color-scheme: dark) and (width < 1100px) {
  .navbar::before {
    top: 3px;
  }
}
@media (prefers-color-scheme: dark) and (width < 950px) {
  .navbar::before {
    top: 5px;
  }
}
  </style>

  <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-lite@4"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
  <script src="https://kit.fontawesome.com/8217dffd95.js"></script>
  <script src="https://code.jquery.com/jquery-3.4.1.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.12.9/umd/popper.min.js"
    integrity="sha384-ApNbgh9B+Y1QKtv3Rn7W3mgPxhU9K/ScQsAP7hUibX39j7fakFPskvXusvfa0b4Q"
    crossorigin="anonymous"></script>
  <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js"
    integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM"
    crossorigin="anonymous"></script>
  <script src="https://unpkg.com/bootstrap-table@1.19.1/dist/bootstrap-table.min.js"></script>
  <script
    src="https://unpkg.com/bootstrap-table@1.19.1/dist/extensions/filter-control/bootstrap-table-filter-control.min.js"></script>
  <script
    src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datepicker/1.9.0/js/bootstrap-datepicker.min.js"></script>

  <link rel="shortcut icon" href="./static/images/favicon.ico" type="image/x-icon" />
</head>

<body>
  <nav class="navbar navbar-expand-md sticky-top border-bottom" style="height: 70px" aria-label="Brands Header">
    <div class="mr-auto">
      <nav class="d-flex align-items-center" aria-label="Great Expectation Logo">
        <div class="float-left navbar-brand m-0 h-100">
          <a href="#">
            <img class="NO-CACHE"
              src="https://great-expectations-web-assets.s3.us-east-2.amazonaws.com/logo-long.png?d=20240514T152059.877242Z&dataContextId=b0ac6be6-1920-4cad-b720-e927c6b4276b"
              alt="Great Expectations" style="width: auto; height: 50px" />
          </a>
        </div>
      </nav>
    </div>
  </nav>
  <div class="container-fluid pt-4 pb-4 pl-5 pr-5">
    <div class="row">
      <div class="col-lg-2 col-md-2 col-sm-12 d-sm-block px-0">
        <div class="mb-4">
          <div class="col-12 p-0">
            <p>
              The Sidra Data Quality report you are viewing has been created with 
              <a href="https://greatexpectations.io">Great Expectations</a> framework.
            </p>
          </div>
        </div>
        <div class="sticky">
        </div>
      </div>
      <div class="col-md-10 col-lg-10 col-xs-12 pl-md-4 pr-md-3">
        <div id="section-1" class="ge-section container-fluid mb-1 pb-1 pl-sm-3 px-0">
          <div class="row">
            <div id="section-1-content-block-1" class="col-12 ge-index-page-site-name-title">
              <div id="section-1-content-block-1-header" class="alert alert-secondary">
                <div>
                  <span>
                    <strong>Data Docs</strong> | SECTION1BLOCK1_HEADER
                  </span>
                </div>
              </div>
            </div>

            <div id="section-1-content-block-2" class="col-12 ge-index-page-tabs-container">
              <div id="section-1-content-block-2-tabs-container">
                <ul class="nav nav-tabs" id=section-1-content-block-2-tabs-nav>
                  <li class="nav-item">
                    <a class="nav-link active" id="Validation-Results-tab" data-toggle="tab" href="#Validation-Results"
                      role="tab" aria-selected="true" aria-controls="Validation-Results">
                      Validation Results
                    </a>
                  </li>
                </ul>

                <div class="tab-content" id="section-1-content-block-2-tabs-content">
                  <div class="tab-pane fade show active" id="Validation-Results" role="tabpanel" aria-labelledby="Validation-Results-tab">
                    <div id="section-1-content-block-2-1-body-table-toolbar" class="ml-1">
                      <button class="btn btn-sm btn-secondary ml-1"
                        onclick="clearTableFilters('section-1-content-block-2-1-body-table')">Clear Filters</button>
                    </div>

                    <table id="section-1-content-block-2-1-body-table"
                      class="table-sm ge-index-page-validation-results-table" data-toggle="table">
                    </table>

                    <script>
                      function rowStyleLinks(row, index) {
                        return {
                          css: {
                            cursor: "pointer"
                          }
                        }
                      }

                      function rowAttributesLinks(row, index) {
                        return {
                          "class": "clickable-row",
                          "data-href": row._table_row_link_path
                        }
                      }

                      function expectationSuiteNameFilterDataCollector(value, row, formattedValue) {
                        return row._expectation_suite_name_sort;
                      }

                      function validationSuccessFilterDataCollector(value, row, formattedValue) {
                        return row._validation_success_text;
                      }

                      function getFormattedDateWithoutTime(d) {

                        let month = '' + (d.getMonth() + 1);
                        let day = '' + d.getDate();
                        let year = d.getFullYear();

                        if (month.length < 2)
                          month = '0' + month;
                        if (day.length < 2)
                          day = '0' + day;

                        return [year, month, day].join('-');
                      }

                      function formatRuntimeDateForFilter(text, value, field, data) {
                        const cellValueAsDateObj = new Date(value);
                        return text == getFormattedDateWithoutTime(cellValueAsDateObj);
                      }

                      function clearTableFilters(tableId) {
                        $(`#${tableId}`).bootstrapTable('clearFilterControl');
                        $(`#${tableId}`).bootstrapTable('resetSearch');
                      }
                    </script>

                    <script>
                      $('#section-1-content-block-2-1-body-table').bootstrapTable(
                        Object.assign(
                          {
                            columns: [{ 'field': 'validation_success', 'title': 'Status', 'sortable': 'true', 'align': 'center', 'filterControl': 'select', 'filterDataCollector': 'validationSuccessFilterDataCollector' }, { 'field': 'run_time', 'title': 'Run Time', 'sortName': '_run_time_sort', 'sortable': 'true', 'filterControl': 'datepicker', 'filterCustomSearch': 'formatRuntimeDateForFilter', 'filterDatepickerOptions': { 'clearBtn': 'true', 'autoclose': 'true', 'format': 'yyyy-mm-dd', 'todayHighlight': 'true' } }, { 'field': 'run_name', 'title': 'Run Name', 'sortable': 'true', 'filterControl': 'input' }, { 'field': 'datasource_name', 'title': 'Datasource Name', 'sortName': '_datasource_name_sort', 'sortable': 'true', 'filterControl': 'input' }, { 'field': 'expectation_suite_name', 'title': 'Expectation Suite', 'sortName': '_expectation_suite_name_sort', 'sortable': 'true', 'filterControl': 'select', 'filterDataCollector': 'expectationSuiteNameFilterDataCollector' }],
                            data: [SECTION1BLOCK2_1DATAHERE],
                            toolbar: '#section-1-content-block-2-1-body-table-toolbar'
                          },
                          { 'search': 'true', 'trimOnSearch': 'false', 'visibleSearch': 'true', 'rowStyle': 'rowStyleLinks', 'rowAttributes': 'rowAttributesLinks', 'sortName': 'run_time', 'sortOrder': 'desc', 'pagination': 'true', 'filterControl': 'true', 'iconSize': 'sm', 'toolbarAlign': 'right', 'showSearchClearButton': 'true' }
                        )
                      );

                      $(document).ready(function () {
                        $("#section-1-content-block-2-1-body-table").on('click-row.bs.table', function (e, row, $element) {
                          window.location = $element.data("href");
                        })
                      }
                      );

                    </script>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
    '''
        
    def _get_custom_style(self):
        return '''
:root {
  --primary: #8672fa;
  --primary-hover: #9887fb;
  --secondary: #66e1e4;
  --secondary-hover: #57bfc2;
  --white: #ffffff;
  --black: #15212f;
  --gray: #e9ecf0;
  --danger: #cc3366;
}

body {
  color: var(--black);
}

/* NAVBAR */

.navbar {
  background: var(--white);
}

.navbar-brand {
  width: 150px;
  height: 50px;
  background-repeat: no-repeat;
  background-size: contain;
  background-position: center;
  background-image: url(data:image/png;base64,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);
}

.navbar-brand.h-100 {
  height: 50px !important;
}

.navbar-brand a {
  display: none;
}

.navbar-expand-md::before {
  position: absolute;
  content: "powered by";
  top: 2px;
  right: 0;
  width: 200px;
  height: auto;
  padding-left: 25px;
  font-size: 0.8em;
  z-index: 4;
  text-align: left;
  background: var(--white);
}

.navbar-expand-md::after {
  position: absolute;
  content: "";
  top: 20px;
  right: 0px;
  width: 200px;
  height: 40px;
  background: var(--white);
  background-image: url("https://great-expectations-web-assets.s3.us-east-2.amazonaws.com/logo-long.png?d=20221102T130030.199543Z");
  background-repeat: no-repeat;
  background-size: contain;
  z-index: 5;
}

/* BUTTONS */

.btn-primary {
  color: var(--white) !important;
  background-color: var(--primary);
  border-color: var(--primary);
  cursor: pointer;
}

.btn-primary:hover,
.btn-primary.active,
.btn-primary:active {
  background-color: var(--primary-hover) !important;
  border-color: var(--primary-hover) !important;
}

.btn-warning,
.btn-info,
.btn-secondary {
  background-color: var(--secondary);
  border-color: var(--secondary);
  color: var(--white) !important;
}

.btn-warning:hover,
.btn-warning.active,
.btn-warning:active,
.btn-info:hover,
.btn-info.active,
.btn-info:active,
.btn-secondary:hover,
.btn-secondary.active,
.btn-secondary:active {
  background-color: var(--secondary-hover) !important;
  border-color: var(--secondary-hover) !important;
  color: var(--white) !important;
}

.btn-primary:focus,
.btn-primary.focus,
.btn-info:focus,
.btn-primary:focus,
.btn-secondary:focus,
.btn-warning:focus {
  box-shadow: none !important;
}

/* TEXTS */

a {
  color: var(--primary) !important;
}

.alert-secondary {
  background-color: var(--gray) !important;
}

.text-danger {
  color: var(--danger) !important;
}

.table {
  color: var(--black) !important;
}

.alert a {
  word-break: break-word;
}

/* RESPONSIVE */

@media (width < 1500px) {
  .nav-item {
    padding-right: 10px !important;
    padding-left: 10px !important;
  }
  .nav-link {
    padding: 0.4rem 0.5rem;
  }
  .breadcrumb {
    font-size: 0.9em;
  }
}

@media (width < 1100px) {
  .navbar::before {
    top: 8px;
    width: 150px;
    padding-left: 20px;
    font-size: 0.7em;
  }
  .navbar::after {
    top: 25px;
    width: 150px;
  }
  .breadcrumb {
    font-size: 0.8em;
  }
}

@media (width < 950px) {
  .navbar::before {
    top: 11px;
    width: 120px;
    padding-left: 16px;
    font-size: 0.6em;
  }
  .navbar::after {
    top: 25px;
    width: 120px;
  }
}

@media (width < 875px) {
  .breadcrumb {
    font-size: 0.8em;
  }
}

@media (width < 800px) {
  .navbar-brand {
    width: 120px;
  }
  .breadcrumb {
    font-size: 0.7em;
  }
}

@media (prefers-color-scheme: dark) {
  body {
    color: #ffffff; /* Texto blanco o claro */
  }
  .breadcrumb-item.active {
    color: #ced4da;
  }
  .table {
    color: #ffffff !important;
  }
  .alert-secondary {
    color: #383d41;
    background-color: #e2e3e5 !important;
    border-color: #d6d8db;
  }
  .navbar {
    background: transparent;
  }
  .navbar-expand-md::after {
    display: none;
  }
  .navbar-expand-md::before {
    background: transparent;
  }
  .navbar-brand {
    background-image: url(data:image/png;base64,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);
  }
  .navbar::before {
    background-color: rgb(25, 29, 33);
    top: 5px;
    width: 210px;
    padding-left: 32px;
  }
  .navbar-brand a {
    background-color: rgb(25, 29, 33);
    display: inline-block;
    position: fixed;
    top: 18px;
    right: 0;
    width: 210px;
    height: 50px;
  }
  .navbar-brand a img {
    width: 100%;
  }
}
@media (prefers-color-scheme: dark) and (width < 1100px) {
  .navbar::before {
    top: 3px;
  }
}
@media (prefers-color-scheme: dark) and (width < 950px) {
  .navbar::before {
    top: 5px;
  }
}
        '''
