resource "oci_functions_application" "logs_function_app" {
  depends_on     = [data.oci_core_subnet.input_subnet]
  compartment_id = var.compartment_ocid
  config = {
    "FORWARD_TO_NR"       = "True"
    "NR_LOG_ENDPOINT"     = var.newrelic_endpoint
    "NR_INGEST_KEY"       = var.newrelic_api_key
    "LOGGING_LEVEL"       = "INFO"
  }
  defined_tags  = {}
  display_name  = "${var.resource_name_prefix}-function-app"
  freeform_tags = local.freeform_tags
  network_security_group_ids = [
  ]
  shape = var.function_app_shape
  subnet_ids = [
    data.oci_core_subnet.input_subnet.id,
  ]
}

resource "oci_functions_function" "logs_function" {
  depends_on = [null_resource.FnImagePushToOCIR, oci_functions_application.logs_function_app]
  #Required
  application_id = oci_functions_application.logs_function_app.id
  display_name   = "${oci_functions_application.logs_function_app.display_name}-logs-function"
  memory_in_mbs  = "1024"

  #Optional
  defined_tags  = {}
  freeform_tags = local.freeform_tags
  image         = local.user_image_provided ? local.custom_image_path : local.docker_image_path
}
