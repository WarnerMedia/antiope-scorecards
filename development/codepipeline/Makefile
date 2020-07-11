
ifndef CONFIG
$(error Execute from repository root)
endif

# get all the variables that start with CFT_TAG_ and return list like key="value"
TAGS = $(foreach v, $(.VARIABLES),$(if $(filter CFT_TAG_%,$(v)),$(subst CFT_TAG_,,$(v))="$($(v))"))

ifneq ($(strip $(TAGS)),)
TAGS_FLAG = --tags
else
TAGS_FLAG =
endif

ci-roles:
	export TAGS=$$(env | grep -v MAKEFLAGS | grep CFT_TAG_); \
	export TAGS=$${TAGS//CFT_TAG_/}; \
	aws cloudformation deploy \
		--stack-name ${STACK_PREFIX}-ci-roles \
		--region us-east-1 \
		--template-file roles.yml \
		--capabilities CAPABILITY_NAMED_IAM \
		--no-fail-on-empty-changeset \
		$(TAGS_FLAG) $(TAGS) \
		--parameter-overrides \
			RolePrefix=${ROLE_PREFIX} \
			BucketPrefix=${BUCKET_PREFIX}

ci-buckets:
	export TAGS=$$(env | grep -v MAKEFLAGS | grep CFT_TAG_); \
	export TAGS=$${TAGS//CFT_TAG_/}; \
	aws cloudformation deploy \
		--stack-name ${STACK_PREFIX}-artifact-buckets \
		--region us-east-1 \
		--template-file bucket.yml \
		--no-fail-on-empty-changeset \
		--capabilities CAPABILITY_NAMED_IAM \
		$(TAGS_FLAG) $(TAGS) \
		--parameter-overrides \
				BucketPrefix=${BUCKET_PREFIX} \
				ResourcePrefix=${RESOURCE_PREFIX}

ci-pipeline-nonprod:
	export TAGS=$$(env | grep -v MAKEFLAGS | grep CFT_TAG_); \
	export TAGS=$${TAGS//CFT_TAG_/}; \
	aws cloudformation deploy \
		--stack-name ${STACK_PREFIX}-ci-pipeline \
		--region us-east-1 \
		--template-file pipeline.yml \
		--no-fail-on-empty-changeset \
		--capabilities CAPABILITY_NAMED_IAM \
		$(TAGS_FLAG) $(TAGS) \
		--parameter-overrides \
				Stage1=dev \
				Stage2=qa \
				UserPrefix=${USER_PREFIX} \
				RolePrefix=${ROLE_PREFIX} \
				BucketPrefix=${BUCKET_PREFIX} \
				ResourcePrefix=${RESOURCE_PREFIX} \
				StackPrefix=${STACK_PREFIX}
ci-pipeline-prod:
	export TAGS=$$(env | grep -v MAKEFLAGS | grep CFT_TAG_); \
	export TAGS=$${TAGS//CFT_TAG_/}; \
	aws cloudformation deploy \
		--stack-name ${STACK_PREFIX}-ci-pipeline \
		--region us-east-1 \
		--template-file pipeline.yml \
		--no-fail-on-empty-changeset \
		--capabilities CAPABILITY_NAMED_IAM \
		$(TAGS_FLAG) $(TAGS) \
		--parameter-overrides \
				Stage1=uat \
				UserPrefix=${USER_PREFIX} \
				RolePrefix=${ROLE_PREFIX} \
				BucketPrefix=${BUCKET_PREFIX} \
				ResourcePrefix=${RESOURCE_PREFIX} \
				StackPrefix=${STACK_PREFIX}

upload-app-config-nonprod:
	zip -j config.zip ../config.local/dev.json ../config.local/qa.json
	aws s3 cp config.zip s3://${BUCKET_PREFIX}-upload-${NONPROD_ACCOUNT}/config.zip
download-app-config-nonprod:
	aws s3 cp s3://${BUCKET_PREFIX}-upload-${NONPROD_ACCOUNT}/config.zip config.zip
	unzip config.zip -d ../config.local/
upload-app-config-prod:
	zip -j config.zip ../config.local/uat.json ../config.local/prod.json
	aws s3 cp config.zip s3://${BUCKET_PREFIX}-upload-${PROD_ACCOUNT}/config.zip
download-app-config-prod:
	aws s3 cp s3://${BUCKET_PREFIX}-upload-${PROD_ACCOUNT}/config.zip config.zip
	unzip config.zip -d ../config.local/

ci-nonprod: ci-roles ci-buckets ci-pipeline-nonprod
ci-prod: ci-roles ci-buckets ci-pipeline-prod


