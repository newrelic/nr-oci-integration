resource "oci_sch_service_connector" "logs_service_connector" {
  depends_on = [oci_functions_function.logs_function]
  #Required
  compartment_id = var.compartment_ocid
  display_name   = local.connector_name
  source {
    #Required
    kind = "logging"

    #Required
    log_sources {
      #Optional
      compartment_id = var.tenancy_ocid
      log_group_id = var.log_group_id
      log_id = var.log_id
    }
  }
  target {
    #Required
    kind = "functions"

    #Optional
    batch_size_in_kbs = 1000
    batch_time_in_sec = 60
    compartment_id    = var.tenancy_ocid
    function_id       = oci_functions_function.logs_function.id
  }

  #Optional
  defined_tags  = {}
  description   = "Terraform created connector to forward logs to New Relic"
  freeform_tags = local.freeform_tags
}
