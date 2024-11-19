terraform {
  required_version = ">= 1.2.0"
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "5.46.0"
    }
  }
}

data "oci_identity_tenancy" "tenancy_metadata" {
  tenancy_id = var.tenancy_ocid
}

provider "oci" {
  tenancy_ocid = var.tenancy_ocid
}

locals {
  tenancy_home_region = data.oci_identity_tenancy.tenancy_metadata.home_region_key
  read_policy_group = var.dynamic_group_name
  freeform_tags = {
    newrelic-terraform = "true"
  }
}

resource "oci_identity_dynamic_group" "nr_serviceconnector_group" {
  #Required
  compartment_id = var.tenancy_ocid
  description    = "[DO NOT REMOVE] Dynamic group for service connector"
  matching_rule  = "All {resource.type = 'serviceconnector'}"
  name           = var.dynamic_group_name

  #Optional
  defined_tags  = {}
  freeform_tags = local.freeform_tags
}

resource "oci_identity_policy" "nr_metrics_policy" {
  depends_on     = [oci_identity_dynamic_group.nr_serviceconnector_group]
  compartment_id = var.tenancy_ocid
  description    = "[DO NOT REMOVE] Policy to have any connector hub read from monitoring source and write to a target function"
  name           = var.newrelic_metrics_policy
  statements = ["Allow dynamic-group ${var.dynamic_group_name} to read metrics in tenancy",
    "Allow dynamic-group ${var.dynamic_group_name} to use fn-function in tenancy",
    "Allow dynamic-group ${var.dynamic_group_name} to use fn-invocation in tenancy"
  ]
  defined_tags  = {}
  freeform_tags = local.freeform_tags
}
