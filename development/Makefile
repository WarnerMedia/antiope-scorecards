



ci-nonprod:
	cd ci && $(MAKE) ci-nonprod
ci-prod:
	cd ci && $(MAKE) ci-prod
ci-pipeline-prod:
	cd ci && $(MAKE) ci-pipeline-prod
ci-pipeline-nonprod:
	cd ci && $(MAKE) ci-pipeline-nonprod

export LOCAL_DYNAMODB_JAR=DynamoDBLocal.jar
local-dynamodb:
	rm -rf dynamodb.local
	curl -L https://s3.us-west-2.amazonaws.com/dynamodb-local/dynamodb_local_latest.zip > dynamodb.local.zip
	unzip dynamodb.local.zip -d local-dynamodb
start-local-dynamodb: local-dynamodb
	if [[ ! $$(pgrep -f $${LOCAL_DYNAMODB_JAR}) ]]; then \
		java -Xmx2g -Djava.library.path=./local-dynamodb/DynamoDBLocal_lib -jar local-dynamodb/$${LOCAL_DYNAMODB_JAR} -inMemory -sharedDb & \
	fi;
stop-local-dynamodb:
	pkill -f $${LOCAL_DYNAMODB_JAR}
lint:
	pylint app tests
	cd templates && $(MAKE) stepfunctions.yml
	cfn-lint templates/*[!0-9].yml
test: start-local-dynamodb
	source tests/unit/unit.env ;\
	IS_LOCAL=true pytest --cov=app --cov-report term-missing --cov-report html:coverage tests/unit -vv
integration-test:
	export AWS_DEFAULT_REGION=${AWS_REGION}; \
	export API_STAGE=$${API_STAGE:=$$STAGE}; \
	export API_ENDPOINT=$$(aws ssm get-parameter --region ${AWS_REGION} --name /${RESOURCE_PREFIX}/$${API_STAGE}/api/domain --query Parameter.Value --output text); \
	pytest tests/integration --verbose

export LOCAL_STEPFUNCTION_JAR=StepFunctionsLocal.jar
local-step-function:
	rm -rf local-step-function
	curl -L https://docs.aws.amazon.com/step-functions/latest/dg/samples/StepFunctionsLocal.zip > StepFunctionsLocal.zip
	unzip StepFunctionsLocal.zip -d local-step-function
start-local-step-function: local-step-function
	if [[ ! $$(pgrep -f $${LOCAL_STEPFUNCTION_JAR}) ]]; then \
		java -jar local-step-function/$${LOCAL_STEPFUNCTION_JAR} --step-functions-endpoint http://localhost:8083 --sqs-endpoint http://localhost:9000 --lambda-endpoint http://localhost:9000 > step-function-local.log & \
	fi
stop-local-step-function:
	pkill -f $${LOCAL_STEPFUNCTION_JAR}
test-step-function: start-local-step-function
	# note: not reliable enough for automated testing
	pytest tests/stepfunction/$(test) --verbose -vv

swagger-server:
	cd swagger-editor && $(MAKE) swagger-server
sdk-generate:
	cd sdk && $(MAKE) generate


deploy-temp-api: build
	source parameters.local; \
	cd cloudformation; \
	$(MAKE) package-api; \
	$(MAKE) deploy-api
cleanup-temp-api:
	source parameters.local; \
	cd cloudformation; \
	$(MAKE) cleanup-api; \
	aws logs describe-log-groups \
		--log-group-name-prefix /aws/lambda/${RESOURCE_PREFIX}-$${STAGE} \
		--query logGroups[].[logGroupName] \
		--output text | xargs -I {} aws logs delete-log-group --log-group-name {}