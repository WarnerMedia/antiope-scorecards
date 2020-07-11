ifndef AWS_REGIONS
override AWS_REGIONS = us-east-1
endif

ifndef EXECUTION_ID
	export EXECUTION_ID := $(shell date +%Y%b%d-%H%M)
endif

template_url="antiope-scorecards-${EXECUTION_ID}-Transformed-Template.yaml"



# Called by CodeBuild to do cloudformation package
package: stepfunctions.yaml
	export AWS_REGIONS=${AWS_REGIONS}; \
	export ACCOUNT_ID=$$(aws sts get-caller-identity --query Account --output text); \
	for AWS_REGION in $${AWS_REGIONS//:/ }; do \
		aws cloudformation package \
			--s3-bucket ${BUCKET_PREFIX}-cfn-artifacts-$${ACCOUNT_ID}-$${AWS_REGION} \
			--template-file main.yaml \
			--output-template-file main.$${AWS_REGION}.packaged.yaml; \
		aws s3 cp main.$${AWS_REGION}.packaged.yaml s3://${BUCKET_PREFIX}-cfn-artifacts-$${ACCOUNT_ID}-$${AWS_REGION}/${template_url}; \
	done

# Only required for temporary environments
package-api:
	export AWS_REGIONS=${AWS_REGIONS}; \
	export ACCOUNT_ID=$$(aws sts get-caller-identity --query Account --output text); \
	for AWS_REGION in $${AWS_REGIONS//:/ }; do \
		aws cloudformation package \
			--s3-bucket ${BUCKET_PREFIX}-cfn-artifacts-$${ACCOUNT_ID}-$${AWS_REGION} \
			--template-file api.yaml \
			--output-template-file api.$${AWS_REGION}.packaged.yaml; \
	done

# Only required for temporary environments
deploy-api:
	export AWS_REGIONS=${AWS_REGIONS}; \
	for AWS_REGION in $${AWS_REGIONS//:/ }; do \
		aws cloudformation deploy \
			--stack-name ${STACK_PREFIX}-${STAGE}-api \
			--template-file api.$${AWS_REGION}.packaged.yaml \
			--capabilities CAPABILITY_IAM \
			--parameter-overrides \
					Stage=${STAGE} \
					ResourcePrefix=${RESOURCE_PREFIX} \
					Domain=${DOMAIN} \
					CertArn=${CERT_ARN} \
					CognitoUserPoolArn=${COGNITO_USER_POOL_ARN} \
					UsersTable=${USERS_TABLE} \
					ConfigTable=${CONFIG_TABLE} \
					AccountsTable=${ACCOUNTS_TABLE} \
					RequirementsTable=${REQUIREMENTS_TABLE} \
					NCRTable=${NCR_TABLE} \
					ExclusionsResourcesTable=${EXCLUSIONS_RESOURCES_TABLE} \
					ScoresTable=${SCORES_TABLE} \
					AccountScoresTable=${ACCOUNT_SCORES_TABLE} \
					ScansTable=${SCANS_TABLE} \
					AuditTable=${AUDIT_TABLE} \
					ScorecardBucket=${SCORECARD_BUCKET} \
					ScorecardPrefix=${SCORECARD_PREFIX} \
					EsEndpoint=${ES_ENDPOINT} \
					EsRegion=${ES_REGION} \
					SnsArn=${SNS_ARN} \
					RemediationRoleName=${REMEDIATION_ROLE_NAME}; \
	done

# Only required for temporary environments
cleanup-api:
	export AWS_REGIONS=${AWS_REGIONS}; \
	for AWS_REGION in $${AWS_REGIONS//:/ }; do \
		aws cloudformation delete-stack \
			--stack-name ${STACK_PREFIX}-${STAGE}-api; \
	done
