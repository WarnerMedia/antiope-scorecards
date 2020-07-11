# CI

## Deploying the CI infrastructure

There are a couple of things you must configure to deploy CI.

First you should set up the application configuration. Make a `config.local` directory with three files in it (one for each stage of deployment): `dev.json`, `qa.json`, and `uat.json`. Each file should look like this:

```json
{
  "Parameters": {
    "ResourcePrefix": "",
    "Domain": "",
    "ApiDomain": "",
    "CertArn": "",
    "Stage": ""
  },
  "Tags": {
    "Key": "Value"
  }
}
```

Once you have all of those created, then you're ready to deploy the CI. The steps required to deploy CI are as follows (**from the repository root**):

```sh
# get nonprod account credentials
make ci-nonprod CONFIG=config.<env>

# get prod account credentials
make ci-prod CONFIG=config.<env>
```

After updating the ci, upload the application config using `make upload-app-config-nonprod` or `make upload-appconfig-prod`
If you are just updating the application config, or if you want to download the config, you can do one of the following:

```sh
make download-app-config-prod
make download-app-config-nonprod
make upload-app-config-prod
make upload-app-config-nonprod
```

CI Variables:

- `PROD_ACCOUNT` - the ID of the production AWS account
- `NONPROD_ACCOUNT` - the ID of the non-production AWS account

The CI Variables are optional:

- `USER_PREFIX` - The prefix to apply to any IAM users created for CI/CD (`antiope-scorecards` as a default if omitted)
- `ROLE_PREFIX` - The prefix to apply to any IAM roles created for CI/CD (`antiope-scorecards` as a default if omitted)
- `BUCKET_PREFIX` - The prefix to apply to the name of any bucket created for CI/CD (`antiope-scorecards` as a default if omitted)
- `RESOURCE_PREFIX` - The prefix to apply to other miscellaneous named resources for CI/CD (`antiope-scorecards` as a default if omitted)
- `STACK_PREFIX` - The prefix to apply to CloudFormation stacks for CI/CD and the deployed application (`antiope-scorecards` as a default if omitted)
- `CFT_TAG_Key` - Tags to apply to CI/CD cloudformation stacks. `CFT_TAG_MyKey=MyValue` will create the following tag: `MyKey=MyValue`.
Note to include a `-` in the key name you must use pass the CFT_TAG_key variable as a `make` variable (not an environment variable). e.g. make ci-nonprod CFT_TAG_key-with-dash=somevalue

App Config:

- `Domain` - The domain you want to use for this stage (like dev.domain.com)
- `CertArn` - The ACM certificate to be applied to the backend API
- `ApiDomain` - the domain to serve the backend API out of
- `Stage` - The name of the stage (keep this the same as the name of the file - `dev`, `staging`, or `prod`)

The following App Config properties are optional:

- `ResourcePrefix` - The prefix to apply to named resources (`antiope-scorecards` as a default if omitted)

### Notes

- The frontend CI/CD is hosted through Amplify Console. The Amplify Console is deployed through the `templates/main.yml` with the backend, within the `templates/frontend.yml` template. Checkout the `templates/README.md` for more information.
- The following buckets will be created for CI/CD
  - AWS CodePipeline CI Artifacts - To enable AWS CodePipeline to manage artifacts across stages and actions
    - `${BucketPrefix}-ci-artifacts-${NONPROD_ACCOUNT_ID}-us-east-1`
    - `${BucketPrefix}-ci-artifacts-${PROD_ACCOUNT_ID}-us-east-1`

  - AWS CloudFormation Artifacts - To store CloudFormation artifacs (nested templates, lambda code, etc)
    - `${BucketPrefix}-cfn-artifacts-${NONPROD_ACCOUNT_ID}-us-east-1`
    - `${BucketPrefix}-cfn-artifacts-${PROD_ACCOUNT_ID}-us-east-1`

  - Application Code and Config Upload - to trigger CodePipeline and Amplify Console off of
    - `${BucketPrefix}-upload-${NONPROD_ACCOUNT_ID}`
    - `${BucketPrefix}-upload-${PROD_ACCOUNT_ID}`
