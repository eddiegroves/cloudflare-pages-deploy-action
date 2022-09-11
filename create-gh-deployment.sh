#!/bin/bash
# [[file:README.org::create-gh-deployment.sh][create-gh-deployment.sh]]
# * Inputs
#
# |-------------------------+----------------------------------------------------------------------|
# | Environment variable    | Description                                                          |
# |-------------------------+----------------------------------------------------------------------|
# | INPUT_ENVIRONMENT       | The deployment target environment, e.g test, dev, qa, staging.       |
# | INPUT_GITHUB_REF        | The ref for the deploy. This can be a branch, tag, or SHA.           |
# | INPUT_GITHUB_REPOSITORY | The owner and repository name. For example, eddiegroves/hello-world. |
# | GITHUB_TOKEN            | A token to authenticate on behalf of the GitHub Action.              |
# |-------------------------+----------------------------------------------------------------------|
#
# * Outputs
#
# |----------------------+------------------------------------------|
# | GitHub outputs       | Description                              |
# |----------------------+------------------------------------------|
# | github-deployment-id | The created GitHub deployment identifier |
# |----------------------+------------------------------------------|

errors=""
declare -a inputs=("INPUT_ENVIRONMENT" "INPUT_GITHUB_REF" "INPUT_GITHUB_REPOSITORY" "GITHUB_TOKEN")

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

json_string=$( jq -n \
                 --arg environment "$INPUT_ENVIRONMENT" \
                 --arg github_ref "$INPUT_GITHUB_REF" \
                 '{ auto_merge: false, description: "Cloudflare Pages", environment: $environment, production_environment: (if $environment == "production" then true else false end), ref: $github_ref, required_contexts: []}')

curl --silent \
  -X POST \
  https://api.github.com/repos/$INPUT_GITHUB_REPOSITORY/deployments \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -d "$json_string" | jq '.id' | xargs -I {} echo "::set-output name=github-deployment-id::{}"
# create-gh-deployment.sh ends here
