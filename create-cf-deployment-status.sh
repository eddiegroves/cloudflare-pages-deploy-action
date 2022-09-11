#!/bin/bash
# [[file:README.org::create-cf-deployment-status.sh][create-cf-deployment-status.sh]]
# * Input
#
# |-------------------------------+-----------------------------------------------------------------|
# | Environment variable          | Description                                                     |
# |-------------------------------+-----------------------------------------------------------------|
# | CLOUDFLARE_ACCOUNT_ID         | Used by Wranlger to identify the Cloudflare Pages account.      |
# | CLOUDFLARE_API_TOKEN          | Used by Wranlger to authenticate to Cloudflare API.             |
# | INPUT_CLOUDFLARE_PROJECT_NAME | The name of the Cloudflare Pages project you want to deploy to. |
# | INPUT_ENVIRONMENT             | The deployment target environment, e.g test, dev, qa, staging.  |
# | INPUT_PUBLISH_DIRECTORY       | The directory of static files to upload.                        |
# | INPUT_COMMIT_HASH             | The SHA to attach to this deployment.                           |
# | INPUT_MESSAGE                 | The commit message to attach to this deployment.                |
# |-------------------------------+-----------------------------------------------------------------|
#
# * Output
#
# No outputs are created.

errors=""
declare -a inputs=("CLOUDFLARE_ACCOUNT_ID" "CLOUDFLARE_API_TOKEN" "INPUT_CLOUDFLARE_PROJECT_NAME" "INPUT_ENVIRONMENT" "INPUT_PUBLISH_DIRECTORY" "INPUT_COMMIT_HASH" "INPUT_MESSAGE")

for input_name in "${inputs[@]}"
do
    if [ -z ${!input_name+x} ]; then
       errors="${errors}environment variable $input_name is required\n"
    fi
done

if [ ! -z "${errors}" ]; then
    printf "$errors"
    exit 1
fi

npx wrangler@2.0.29 pages publish $INPUT_PUBLISH_DIRECTORY \
--project-name=$INPUT_CLOUDFLARE_PROJECT_NAME \
--branch=$INPUT_ENVIRONMENT \
--commit-hash=$INPUT_COMMIT_HASH \
--commit-message="$INPUT_MESSAGE"
# create-cf-deployment-status.sh ends here
