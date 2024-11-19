[![New Relic Community header](https://opensource.newrelic.com/static/Community_Project-0c3079a4e4dbe2cbd05edc4f8e169d7b.png)](https://opensource.newrelic.com/oss-category/#new-relic-community)

![GitHub forks](https://img.shields.io/github/forks/newrelic/nr-oci-integration?style=social)
![GitHub stars](https://img.shields.io/github/stars/newrelic/nr-oci-integration?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/newrelic/nr-oci-integration?style=social)

# New Relic OCI Integrations

This repository contains integrations to forward metrics or logs from Oracle Cloud Infrastructure (OCI).

## Prerequisites

* [New Relic Ingest Key](https://docs.newrelic.com/docs/apis/intro-apis/new-relic-api-keys/#license-key)
* OCI user with Cloud Administrator role to create resources/stacks

## Installation

For convenience, Terraform configurations are supplied to create OCI Resource Manager (ORM) stacks. Each sub-section below outlines pre-requisites, steps, and resulting resources created for either metrics or logs ingestion.

### Metrics

#### Policy Stack

An ORM policy stack must be created in the home region of the tenancy. The policy stack creates:

* A dynamic group with rule `All {resource.type = 'serviceconnector'}`, which enables access to the connector hub
* A policy in the root compartment to allow connector hubs to read metrics and invoke functions. The following statements are added to the policy:

```
Allow dynamic-group <GROUP_NAME> to read metrics in tenancy
Allow dynamic-group <GROUP_NAME> to use fn-function in tenancy
Allow dynamic-group <GROUP_NAME> to use fn-invocation in tenancy
```

To create this stack in the OCI Portal:

1. Download the latest release in this repo & unzip
2. Navigate to _Resource Manager -> Stacks_
3. Select *Create stack*
4. Under *Stack configuration* select `Browse`
5. Select the entire `policy-orm-setup` directory & *Upload*
6. Optionally modify the name, description, compartment, and tags. Leave the option to use custom Terraform providers *unchecked*. Select *Next*
7. Name the dynamic group, user group, and policy to be created, or use the default names provided
8. Provide the name of the domain of the user running the stack. The default domain name is `Default`
9. Ensure that the *home region* of the tenancy is selected
10. Click Next -> Create to create stack.


#### Metrics Stack

After the policy stack is successfully created, create the Metrics stack, which creates the following resources:

* A VCN that routes traffic to New Relic (alternatively, use an existing VCN)
* Application that contains a function
* Function Application that contains the `metrics-function` to forward metrics. The Docker image is deployed to or pulled from the Container Registry.
* Service Connector that routes metrics to the Function Application

To create this stack in the OCI Portal:

2. Navigate to _Resource Manager -> Stacks_
3. Select *Create stack*
4. Under *Stack configuration* select `Browse`
5. Select the entire `nr-metric-reporter` directory & *Upload*
6. Optionally modify the name, description, compartment, and tags. Leave the option to use custom Terraform providers *unchecked*. Select *Next*
7. Leave *Tenancy* values unmodified, as these are specified by your current region and tenant.
8. For the rest of the configuration, see relevant sections below:

##### New Relic Configuration

| Input | Type | Required | Description
| ----- | ---- | -------- | -----------
| New Relic API Key | string | TRUE | [New Relic Ingest Key] used to forward metrics.
| New Relic Metric Endpoint | enum | TRUE | New Relic endpoint to forward metrics to. Either US or EU endpoint.

##### Network Options

| Input | Type | Required | Description
| ----- | ---- | -------- | -----------
| Create VCN | bool | FALSE | Creates a new VCN. Select if you do not want to use an existing VCN. All other config options should be left blank if this is checked.
| vcnCompartment | enum | FALSE | Compartment of existing VCN.
| existingVcn | enum | FALSE | If using an existing VCN, make sure it is allowed to make HTTP egress calls through NAT Gateway, is able to pull images from Container Registry using service gateway, has route table rules to allow NAT gateway/service gateway, and has security rules to send HTTP requests.
| Function Subnet OCID | enum | FALSE | OCID of function subnet to be used.

##### Function Settings

| Input | Type | Required | Description
| ----- | ---- | -------- | -----------
| Function Application shape | enum | TRUE | Shape of function application. The docker image build should match this input. Default: `GENERIC_ARM`
| Function Image Path | enum | FALSE | The full path to the function image in Container Registry (i.e: `iad.ocir.io/ido1234/myTenancy/nr-metrics-reporter:0.0.1`). If this is defined, OCI Docker user name/password are not required.
| OCI Docker registry user name | string | FALSE | The user name for Container Registry. Typically this is your user email address. Not required if `Function Image Path` is defined.
| OCI Docker registry password | string | FALSE | The user password for Container Registry. Typically this is a [user auth token](https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrygettingauthtoken.htm) generated. Not required if `Function Image Path` is defined.

##### Miscellaneous Settings

| Input | Type | Required | Description
| ----- | ---- | -------- | -----------
| Resource prefix | string | TRUE | Prefix string for all resources created. Default: `newrelic-metrics`
| Service Connector hub batch size | enum | FALSE | Payload batch size (in kb) in which to send to New Relic. Default: `5000`


9. Once all required configuration is input, select *Next*
10. Review inputs, and select `Create` to create stack. Check *Run apply* to create resources immediately.


Once the stack is created, metrics should be available in the New Relic portal. Open the query builder and run the following query to validate:
```
FROM Metric SELECT * where metricName like '%oci%'
```

### Logs

The Logs stack creates the following resources:

* A VCN that routes traffic to New Relic (alternatively, use an existing VCN)
* Application that contains a function
* Function Application that contains the `logs-function` to forward logs. The Docker image is deployed to or pulled from the Container Registry.
* Service Connector that routes logs to the Function Application

#### Prerequisites
* A Log Group containing a custom log or service log

To create a Logging group:

1. In the OCI portal, navigate to _Logging -> Log Groups_.
2. Select your compartment and click *Create Log Group*. A side panel opens.
3. Enter a descriptive name (i.e - `newrelic_log_group`), and optionally provide a description and tags.
4. Click *Create* to set up your new Log Group.
5. Under *Resources*, select *Logs*.
6. Click to *Create custom log* or *Enable service log* as desired.
7. Click *Enable Log*, to create your new OCI Log.

For more information on OCI Logs, see [Enabling Logging for a Resource](https://docs.oracle.com/en-us/iaas/Content/Logging/Task/enabling_logging.htm).

#### Logging Stack

See [Metrics Stack](###metrics-stack) for installation/configuration details - The logging stack config is virtually the same, except for the following differences:

* In step 5 under [Metrics Stack](###metrics-stack), select `nr-logs-reporter` directory instead.
* In addition to the configuration sections under [Metrics Stack](###metrics-stack), an additional configuration section `Logging Configuration` is required below.

##### Logging Configuration

| Input | Type | Required | Description
| ----- | ---- | -------- | -----------
| Log Group OCID | string | TRUE | The OCID of the Log Group containing the logs to be forwarded.
| Log OCID | string | FALSE | The OCID of the Log file to be forwarded.


Once the stack is created and resources are generated successfully, navigate to the New Relic portal under *Logs* to view logs.

## Contributing

We encourage your contributions to improve nr-oci-integration! Keep in mind when you submit your pull request, you'll need to sign the CLA via the click-through using CLA-Assistant. You only have to sign the CLA one time per project. If you have any questions, or to execute our corporate CLA, required if your contribution is on behalf of a company, please drop us an email at opensource@newrelic.com.

**A note about vulnerabilities**

As noted in our [security policy](../../security/policy), New Relic is committed to the privacy and security of our customers and their data. We believe that providing coordinated disclosure by security researchers and engaging with the security community are important means to achieve our security goals.

If you believe you have found a security vulnerability in this project or any of New Relic's products or websites, we welcome and greatly appreciate you reporting it to New Relic through [HackerOne](https://hackerone.com/newrelic).

## License

nr-oci-integration is licensed under the [Apache 2.0](http://apache.org/licenses/LICENSE-2.0.txt) License.
