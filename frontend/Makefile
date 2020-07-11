export BUCKET_PREFIX ?= antiope-scorecards
export RESOURCE_PREFIX ?= antiope-scorecards

build-code:
	yarn install
	export REACT_APP_API_URL=$$(aws ssm get-parameter --region us-east-1 --name /${RESOURCE_PREFIX}/${STAGE}/api/domain --query Parameter.Value --output text); \
	export REACT_APP_COGNITO_USER_POOL_ID=$$(aws ssm get-parameter --region us-east-1 --name /${RESOURCE_PREFIX}/${STAGE}/auth/user-pool-id --query Parameter.Value --output text); \
	export REACT_APP_COGNITO_APP_CLIENT_ID=$$(aws ssm get-parameter --region us-east-1 --name /${RESOURCE_PREFIX}/${STAGE}/auth/app-client-id --query Parameter.Value --output text); \
	export REACT_APP_COGNITO_DOMAIN=$$(aws ssm get-parameter --region us-east-1 --name /${RESOURCE_PREFIX}/${STAGE}/auth/domain --query Parameter.Value --output text).auth.${AWS_REGION}.amazoncognito.com; \
	yarn run build

upload-code:
	rm -rf frontend.zip
	cd build && zip ../frontend.zip -r .
	export ACCOUNT_ID=$$(aws sts get-caller-identity --query Account --output text); \
	aws s3 cp frontend.zip s3://${BUCKET_PREFIX}-upload-$${ACCOUNT_ID}/frontend.${STAGE}.zip

start-amplify:
	export ACCOUNT_ID=$$(aws sts get-caller-identity --query Account --output text); \
	export APP_ID=$$(aws ssm get-parameter --name /${RESOURCE_PREFIX}/${STAGE}/frontend/app-id --query Parameter.Value --output text --region ${AWS_REGION}); \
	export APP_BRANCH=$$(aws ssm get-parameter --name /${RESOURCE_PREFIX}/${STAGE}/frontend/branch --query Parameter.Value --output text --region ${AWS_REGION}); \
	aws amplify start-deployment --app-id $${APP_ID} --branch-name $${APP_BRANCH} --source-url s3://${BUCKET_PREFIX}-upload-$${ACCOUNT_ID}/frontend.${STAGE}.zip --region ${AWS_REGION} || true;
deploy:
	$(MAKE) build-code
	$(MAKE) upload-code
	$(MAKE) start-amplify
