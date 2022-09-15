# [[file:README.org::poll-deployment-status.py][poll-deployment-status.py]]
# * Inputs
#
# |-------------------------------+----------+----------------------------------------------------------------------|
# | Environment variable          | Required | Description                                                          |
# |-------------------------------+----------+----------------------------------------------------------------------|
# | INPUT_COMMIT_HASH             | Yes      | The SHA to attach to this deployment.                                |
# | INPUT_GITHUB_DEPLOYMENT_ID    | Yes      | The GitHub deployment identifier for this deployment.                |
# | INPUT_GITHUB_REPOSITORY       | Yes      | The owner and repository name. For example, eddiegroves/hello-world. |
# | INPUT_CLOUDFLARE_PROJECT_NAME | Yes      | The name of the Cloudflare Pages project you want to deploy to.      |
# | GITHUB_TOKEN                  | Yes      | A token to authenticate on behalf of the GitHub Action.              |
# | CLOUDFLARE_ACCOUNT_ID         | Yes      | Used by Wrangler to identify the Cloudflare Pages account.           |
# | CLOUDFLARE_API_TOKEN          | Yes      | Used by Wrangler to authenticate to Cloudflare API.                  |
# |-------------------------------+----------+----------------------------------------------------------------------|
#
# * Outputs
# |--------------------------------+-----------------------------------------------------|
# | GitHub outputs                 | Description                                         |
# |--------------------------------+-----------------------------------------------------|
# | cloudflare-pages-deployment-id | The created Cloudflare Pages deployment identifier. |
# | cloudflare-pages-url           | The URL where Cloudflare Pages was deployed to.     |
# |--------------------------------+-----------------------------------------------------|

import http.client
import json
import subprocess
import os
from time import sleep
from typing import Literal

commit_hash = os.environ["INPUT_COMMIT_HASH"]
github_deployment_id = os.environ["INPUT_GITHUB_DEPLOYMENT_ID"]
github_repository = os.environ["INPUT_GITHUB_REPOSITORY"]
cloudflare_project_name = os.environ["INPUT_CLOUDFLARE_PROJECT_NAME"]
github_token = os.environ["GITHUB_TOKEN"]
cloudflare_api_token = os.environ["CLOUDFLARE_API_TOKEN"]
cloudflare_account_id = os.environ["CLOUDFLARE_ACCOUNT_ID"]


def create_github_deployment_status(
    description: str,
    environment: str,
    state: Literal[
        "error", "failure", "inactive", "in_progress", "queued", "pending", "success"
    ],
    log_url: str = None,
    environment_url: str = None,
):
    payload = {"description": description, "environment": environment, "state": state}

    if log_url:
        payload["log_url"] = log_url

    if environment_url:
        payload["environment_url"] = environment_url

    headers = {
        "User-Agent": "eddiegroves/action/cloudflare-deploy",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
    }

    githubApi = http.client.HTTPSConnection("api.github.com")
    githubApi.request(
        "POST",
        f"/repos/{github_repository}/deployments/{github_deployment_id}/statuses",
        json.dumps(payload),
        headers,
    )


def list_cloudflare_deployments():
    headers = {
        "User-Agent": "eddiegroves/action/cloudflare-deploy",
        "Accept": "application/json",
        "Authorization": f"Bearer {cloudflare_api_token}",
    }

    cloudflareApi = http.client.HTTPSConnection("api.cloudflare.com")
    cloudflareApi.request(
        "GET",
        f"/client/v4/accounts/{cloudflare_account_id}/pages/projects/{cloudflare_project_name}/deployments",
        "",
        headers,
    )

    res = cloudflareApi.getresponse()
    data = res.read().decode("utf-8")

    p = subprocess.run(
        [
            "jq",
            "-r",
            "--arg",
            "commit",
            commit_hash,
            ".result[] | select(.deployment_trigger.metadata.commit_hash == $commit) | { id, project_name, environment,  url: (.aliases[0] // .url), stage: .latest_stage.name, status: .latest_stage.status }",
        ],
        input=data,
        capture_output=True,
        text=True,
        check=False,
    )

    return json.loads(p.stdout)


count = 0
while count < 60:
    deployment = list_cloudflare_deployments()

    if deployment["status"] == "failed":
        print("😢 sad face")
        create_github_deployment_status(
            description="Cloudflare Pages deployment failed.",
            environment="production",
            state="failure",
            log_url=f"https://dash.cloudflare.com?to=/:account/pages/view/{cloudflare_project_name}/{deployment['id']}",
        )
        exit(1)

    if deployment["stage"] == "deploy" and deployment["status"] == "success":
        print("🤗 happy face")
        create_github_deployment_status(
            description="Cloudflare Pages deployment success.",
            environment="production",
            state="success",
            log_url=f"https://dash.cloudflare.com?to=/:account/pages/view/{cloudflare_project_name}/{deployment['id']}",
            environment_url=deployment["url"],
        )

        print(f"::set-output name=cloudflare-pages-deployment-id::{deployment['id']}")
        print(f"::set-output name=cloudflare-pages-url::{deployment['url']}")
        exit(0)

    print(f"🧐 {deployment['stage']} {deployment['status']}")
    create_github_deployment_status(
        description="Cloudflare Pages deployment in progress.",
        environment="production",
        state="in_progress",
        log_url=f"https://dash.cloudflare.com?to=/:account/pages/view/{cloudflare_project_name}/{deployment['id']}",
    )
    sleep(5)
    count = count + 1

print("😭 super sad")
create_github_deployment_status(
    description="Cloudflare Pages deployment status unknown.",
    environment="production",
    state="error",
)
exit(1)
# poll-deployment-status.py ends here
