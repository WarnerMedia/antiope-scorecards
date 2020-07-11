# Makefile build steps


## Upload/Download app configuration
* `make download-app-config-prod`
* `make download-app-config-nonprod`
* `make upload-app-config-prod`
* `make upload-app-config-nonprod`

These make commands upload and download the app configuration from s3.
The configuration file `dev.json`, `staging.json`, `prod.json` are unzipped into `config.local/`

Note: `staging.json` is contained in the prod configuration, since the `staging` environment
is deployed by the production codepipeline.


## Deploy CI/CD pipeline
* `make ci-prod`
* `make ci-nonprod`

These make commands deploy the ci/cd pipeline stacks and upload the app config.
They deploy the three CI/CD cloudformation stacks.

* `make ci-pipeline-prod`
* `make ci-pipeline-nonprod`

These make commands deploy just the CodePipeline stack.


## Create DNS update commands
* `make route53-record-commands-nonprod`
* `make route53-record-commands-prod`

These make commands output AWS cli commands to create/update needed DNS records for the API, frontend, and frontend certificate validation.
After running the command, insert the hostedzone ID into the command in the place indicated.

## Linting
* `make lint`

This command runs `pylint` against the application code.


## Tests
* `make test`

This command runs unit tests.

The project dependencies must have been previously installed.
Development dependencies are recorded in `requirements-dev.txt`.
Application dependencies are recorded in `app/requirements.txt`.
Install via `pip install -r <requirementsfile>`.

* `make test-step-function`

This command runs tests to check the logic in the step functions.
Optionally specify a specific test file to run from `tests/stepfunction/*_test.py` using the variable `TEST`.

These tests use AWS's local-step-function implementation, and a lightweight lambda emulator to check the input and output from the various lambda function tasks in the step function.
Occasionally the local-step-function encounters `broken pipe` and `connection reset` errors when connecting to the lambda emulator.
These are false positives.

* `make integration-test`

This command runs the integration tests.

Use the `STAGE` variable to indicate which environment to run these tests against.
These tests currently require AWS credentials in order to setup test users.


## Test Dependency steps
* local-dynamodb
* local-step-function

These make targets download and extract AWS's local dynamodb and step function implementations respectively

* start-local-dynamodb
* start-local-step-function

These make targets ensure that the local services are running

* `make stop-local-dynamodb`
* `make stop-local-step-function`

These make commands can be used to stop the local AWS service implementation.

This is useful to reset the internal state of the service.


## Build / Deploy steps
* build

This make target prepares the source code for deployment by installing python dependencies


* package

This make command uses `aws cloudformation package` to zip and upload the lambda code and the cloudformation templates to S3.


* upload-code

This make command uploads the code from the git repo to S3.
This is used by the github action that triggers the AWS ci/cd.

* start-pipeline

This make command starts the AWS Codepipeline executing.
It is called by the github action after `upload-code`

* start-amplify

This make command starts the amplify conosle deployment process for the frontend


## Misc
* `make swagger-server`

This command opens a browser with a swagger (open API spec) editor.

The browser is refreshed after making edits to the `api.yml` cloudformation template.
This command is useful so you don't have to copy the api spec between the browser and the editor.

* `make sdk-generate`

This command generates and SDK using the open API SDK generator.
This sdk is used by the integration tests.
