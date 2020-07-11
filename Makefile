SHELL := /bin/bash

ifndef env
# $(error env is not set)
	env ?= dev
endif

include config-files/config.$(env)
export


ifndef MAIN_STACK_NAME
$(error MAIN_STACK_NAME is not set)
endif

ifndef BUCKET
$(error BUCKET is not set)
endif

ifndef version
	export version := $(shell date +%Y%b%d-%H%M)
endif


# Global Vars
export DEPLOY_PREFIX=deploy-packages

# Local to this Makefile Vars
CONFIG_PREFIX=config-files
MAIN_TEMPLATE=cloudformation/antiope-scorecards-Template.yaml
OUTPUT_TEMPLATE_PREFIX=antiope-scorecards-Template-Transformed
OUTPUT_TEMPLATE=$(OUTPUT_TEMPLATE_PREFIX)-$(version).yaml
TEMPLATE_URL ?= https://s3.amazonaws.com/$(BUCKET)/$(DEPLOY_PREFIX)/$(OUTPUT_TEMPLATE)


# --------------
#
# Build Targets
#

package: build
	aws cloudformation package --template-file $(MAIN_TEMPLATE) --s3-bucket $(BUCKET) --s3-prefix $(DEPLOY_PREFIX)/scorecards-transform --output-template-file cloudformation/$(OUTPUT_TEMPLATE)  --metadata build_ver=$(version)
	aws s3 cp cloudformation/$(OUTPUT_TEMPLATE) s3://$(BUCKET)/$(DEPLOY_PREFIX)/
# 	rm cloudformation/$(OUTPUT_TEMPLATE)


build: cloudformation/api.yaml $(shell find ./app)
	rm -rf build;
	mkdir -p build;
	cat cloudformation/api.yaml | yq .Resources.Api.Properties.DefinitionBody > build/swagger.packaged.json
	cp -r app/* build;
	pip install -r build/requirements.txt -t build;


#
# Deploy Targets
#

deploy: cft-validate package cft-deploy push-config

# Actually perform the deploy using cft-deploy and the manifest file (for params) from the code bundle and templates in the S3 bucket
cft-deploy: package
ifndef MANIFEST
	$(error MANIFEST is not set)
endif
	cft-deploy -m config-files/$(MANIFEST) --template-url $(TEMPLATE_URL) pTemplateURL=$(TEMPLATE_URL)   --force

# promote an existing stack to a new environment
# Assumes cross-account access to the lower environment's DEPLOY_PREFIX
promote: cft-promote push-config

# Run cft-deploy with a different manifest on a previously uploaded code bundle and transformed template
cft-promote:
ifndef MANIFEST
	$(error MANIFEST is not set)
endif
ifndef template
	$(error template is not set)
endif
	cft-deploy -m config-files/$(MANIFEST) --template-url $(template) pTemplateURL=$(template)   --force



### Optional targets

upload-code:
	rm -rf backend.zip
	git archive -o backend.zip HEAD
	export ACCOUNT_ID=$$(aws sts get-caller-identity --query Account --output text); \
	aws s3 cp backend.zip s3://${BUCKET_PREFIX}-upload-$${ACCOUNT_ID}/backend.zip

start-pipeline:
	aws codepipeline start-pipeline-execution --name ${RESOURCE_PREFIX}-pipeline --region us-east-1
start-amplify:
	export ACCOUNT_ID=$$(aws sts get-caller-identity --query Account --output text); \
	export APP_ID=$$(aws ssm get-parameter --name /${RESOURCE_PREFIX}/${STAGE}/frontend/app-id --query Parameter.Value --output text --region ${AWS_REGION}); \
	export APP_BRANCH=$$(aws ssm get-parameter --name /${RESOURCE_PREFIX}/${STAGE}/frontend/branch --query Parameter.Value --output text --region ${AWS_REGION}); \
	aws amplify start-deployment --app-id $${APP_ID} --branch-name $${APP_BRANCH} --source-url s3://${BUCKET_PREFIX}-upload-$${ACCOUNT_ID}/frontend.${STAGE}.zip --region ${AWS_REGION} || true;


#
# Management Targets
#
manifest:
ifndef manifest
	$(error manifest is not set)
endif
	cft-generate-manifest -t $(MAIN_TEMPLATE) -m $(manifest) --stack-name $(MAIN_STACK_NAME) --region $(AWS_DEFAULT_REGION)

sync-scorecards:
	aws s3 sync s3://$(SCORECARD_BUCKET)/$(SCORECARD_PREFIX)/ Scorecards/ --exclude "CloudSploit/*"

# Copy the manifest and config file up to S3 for backup & sharing
push-config:
	@aws s3 cp config-files/$(MANIFEST) s3://$(BUCKET)/${CONFIG_PREFIX}/$(MANIFEST)
	@aws s3 cp config-files/config.$(env) s3://$(BUCKET)/${CONFIG_PREFIX}/config.$(env)

# Pull down the latest config and manifest from S3
pull-config:
	aws s3 sync s3://$(BUCKET)/${CONFIG_PREFIX}/ config-files/


route53-record-commands:
	export STACK=$$(aws cloudformation describe-stacks --region ${AWS_REGION} --stack-name ${STACK_PREFIX}-${STAGE}); \
	export AMPLIFY_CERT_DOMAIN=$$(echo $$STACK | jq -r '.Stacks[0].Outputs[] | select(.OutputKey == "AmplifyCertDomain").OutputValue'); \
	export AMPLIFY_CERT_RECORD=$$(echo $$STACK | jq -r '.Stacks[0].Outputs[] | select(.OutputKey == "AmplifyCertRecord").OutputValue'); \
	export AMPLIFY_CERT_CHANGE_BATCH=$$(echo "{\"Changes\":[{\"Action\":\"UPSERT\",\"ResourceRecordSet\":{\"Name\":\"$${AMPLIFY_CERT_DOMAIN}\",\"Type\":\"CNAME\",\"TTL\":300,\"ResourceRecords\":[{\"Value\":\"$${AMPLIFY_CERT_RECORD}\"}]}}]}"); \
	export AMPLIFY_APP_ID=$$(echo $$STACK | jq -r '.Stacks[0].Outputs[] | select(.OutputKey == "AmplifyAppId").OutputValue'); \
	export AMPLIFY_DOMAIN_NAME=$$(echo $$STACK | jq -r '.Stacks[0].Outputs[] | select(.OutputKey == "AmplifyDomainName").OutputValue'); \
	export AMPLIFY_APP_DIST=$$(echo $$AMPLIFY_DOMAIN_ASSOCIATION | jq -r '.domainAssociation.subDomains[0].dnsRecord'); \
	export AMPLIFY_APP_RECORD=$$(echo $${AMPLIFY_APP_DIST//CNAME/}); \
	export AMPLIFY_APP_CHANGE_BATCH=$$(echo "{\"Changes\":[{\"Action\":\"UPSERT\",\"ResourceRecordSet\":{\"Name\":\"$${AMPLIFY_DOMAIN_NAME}\",\"Type\":\"CNAME\",\"TTL\":300,\"ResourceRecords\":[{\"Value\":\"$${AMPLIFY_APP_RECORD}\"}]}}]}"); \
	export API_DOMAIN=$$(echo $$STACK | jq -r '.Stacks[0].Outputs[] | select(.OutputKey == "ApiDomain").OutputValue'); \
	export API_RECORD=$$(echo $$STACK | jq -r '.Stacks[0].Outputs[] | select(.OutputKey == "ApiRecord").OutputValue'); \
	export API_CHANGE_BATCH=$$(echo "{\"Changes\":[{\"Action\":\"UPSERT\",\"ResourceRecordSet\":{\"Name\":\"$${API_DOMAIN}\",\"Type\":\"CNAME\",\"TTL\":300,\"ResourceRecords\":[{\"Value\":\"$${API_RECORD}\"}]}}]}"); \
	echo aws route53 change-resource-record-sets --hosted-zone-id HOSTED_ZONE_ID --change-batch \'$$AMPLIFY_CERT_CHANGE_BATCH\'; \
	echo aws route53 change-resource-record-sets --hosted-zone-id HOSTED_ZONE_ID --change-batch \'$$AMPLIFY_APP_CHANGE_BATCH\'; \
	echo aws route53 change-resource-record-sets --hosted-zone-id HOSTED_ZONE_ID --change-batch \'$$API_CHANGE_BATCH\'; \



#
# Testing & Cleanup Targets
#
# Validate all the CFTs. Inventory is so large it can only be validated from S3
cft-validate:
	cft-validate -t cloudformation/antiope-scorecards-Template.yaml


# Clean up dev artifacts
clean:
	rm -rf build
	rm -f cloudformation/$(OUTPUT_TEMPLATE_PREFIX)*

# Run pep8 style checks on lambda
pep8:
	cd aws-inventory/lambda && $(MAKE) pep8
	cd search-cluster/lambda && $(MAKE) pep8

# Purge all deploy packages in the Antiope bucket.
# WARNING - if you do this, you will no longer be able to promote code.
purge-deploy-packages:
	aws s3 rm s3://$(BUCKET)/$(DEPLOY_PREFIX)/ --recursive

# Pull down the deploy packages from the Antiope Bucket.
# Use this when you want to see what Cloudformation serverless transforms has done
sync-deploy-packages:
	aws s3 sync s3://$(BUCKET)/$(DEPLOY_PREFIX)/ Scratch/$(DEPLOY_PREFIX)/ --delete
