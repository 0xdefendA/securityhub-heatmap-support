# Securityhub Heatmap Support
Supporting code, docs, issues, etc for the securityhub heatmap container available in the [AWS Marketplace](https://aws.amazon.com/marketplace/pp/B08HPXMT8J)


## CDK
The cdk_deployment directory contains code to get a working deployment of the heatmap in a Fargate ECS cluster. The cluster will be created along with a load balancer and supporting vpcs. A TLS cert is not included, but you can either add to the CDK deployment, or add a TLS listener with an appropriate cert after deployment.

The heatmap_policy.json doc is the IAM policy used by the CDK deployment and includes everything the heatmap will need in order to operate. You can use this as a kickstarter if you plan to deploy via some other means (terraform, cloudformation, etc)

### Environment
The default environment/configuration variables are set initially in config.yml inside the container. A copy of the default config.yml is included in this repo if you'd like a reference.

Every variable can be overridden via the container Environment. You can and should override these in your production container environment, especially to set:

 - SERVER_NAME : dns name of the resulting server (i.e. heatmap.somewhere.com)
 - PREFERRED_URL_SCHEME: http by default, should set to https in a production setting
 - DEBUG: True by default, set to False if you'd like less logging/messages
 - OIDC* (see below)
 - REGIONS: a list of regions you'd like to retrieve findings from. If more than one, separate with commas i.e. us-west-1,us-east-1
 - CACHE_EXPIRATION: 10 min by default, This determines the frequency by which the heatmap will refresh it's cache of all findings from security hub. Any updates within the heatmap are cached on update. If you expect frequent external updates to findings, set the expiration accordingly. (sec = seconds, min = minutes, hours=hours, days=days )
 - DB_FILENAME: cache file location (set if you would like it elsewhere, an EFS mount, etc)
 - AWS_DEFAULT_REGION: us-west-2 by default. The region the hub will operate in by default for making calls to securityhub.

### OIDC
By default the heatmap is authenticated through OIDC. You should issue a client ID and client Secret from your Identity Provider (IDP). You can pass the client secret either through an environment variable directly, or by passing a secrets manager secret name and the value stored under that name will be retrieved at run time.

 - OIDC_PROVIDER_NAME: google by default, set to whatever name you'd like. Set to 'none' to disable OIDC if you are authenticating through some other means (alb, proxy, etc) ahead of the container
 - OIDC_ISSUER: the IDP issuer address "https://accounts.google.com" by default
 - OIDC_CLIENT_ID: set to the client ID you receive from your IDP
 - OIDC_CLIENT_SECRET_NAME: the name you use if you store the client secret in secrets manager
 - OIDC_CLIENT_SECRET: the raw secret if you prefer to pass it without using secrets manager
 - OIDC_SESSION_LIFETIME_HOURS: 7 hours by default, set as desired.


In your IDP OIDC configuration, be sure to allow an endpoint matching your deployment DNS as an option for the redirect URI:

 - https://heatmap.yourcompany.com/redirect_uri

### CDK Deployment
To deploy the container via CDK, first ensure you have a [valid subscription via the marketplace](https://aws.amazon.com/marketplace/pp/B08HPXMT8J).

Clone this repo and install the CDK toolkit (if you don't already have it):

  - npm install -g aws-cdk
  - npm update -g aws-cdk (if you just need to update it)

You will want to [update the environment variables for the container in the task definition to match your desired end state](https://github.com/0xdefendA/securityhub-heatmap-support/blob/master/cdk_deployment/deployment_app.py#L64).

The project uses Pipenv [which you can install via these instructions](https://pipenv.pypa.io/en/latest/#install-pipenv-today) if you don't have it yet. Then enter the environment and deploy:

 - pipenv shell
 - pipenv install
 - cdk deploy

 At the end of the cloudformation deployment you should see a load balancer output like so:

 ```bash
 Outputs:
HeatmapStack.heatmapserviceLoadBalancerDNS9E9928C6 = Heatm-heatm-1IPDGJZ1A85NL-dc68bcf73c814362.elb.us-west-2.amazonaws.com
```

You can use that as an ANAME record for whatever DNS address you've given to your heatmap installation.




 ### Local Usage Instructions
 To take the container for a spin locally without deploying to AWS:

 - Install and configure the AWS CLI. Please see https://docs.aws.amazon.com/cli/latest/userguide/installing.html for details.

 - Authenticate your Docker client to the heatmap registry:

```
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 117940112483.dkr.ecr.us-east-1.amazonaws.com
```

On successful login the following message will be seen :

    Login Succeeded

 - Now pull the docker image
```
docker pull 117940112483.dkr.ecr.us-east-1.amazonaws.com/7884b327-1a1a-4f59-8d04-0a6edfc28697/cg-1674965903/securityhub-heatmap
```

 - Start a single local instance of the container via the following:

```
docker run --rm -p 80:80 -v ${HOME}/.aws/:/app/.aws/:ro -e 'OIDC_PROVIDER_NAME=none' -e 'BASIC_AUTH_USERNAME=heatmap' -e 'BASIC_AUTH_PASSWORD=set_this_to_a_long_passphrase' --name securityhub-heatmap 117940112483.dkr.ecr.us-east-1.amazonaws.com/7884b327-1a1a-4f59-8d04-0a6edfc28697/cg-2662330872/securityhub-heatmap
```

- The above command publishes the container's port 80 to your localhost, disables OIDC authentication and enables BASIC AUTHENTICATION for the specified username and password. This is suitable for local testing/integration only.   To access the web UI enter http://localhost/ in your browser.

- For troubleshooting you can access the local container logs via:

```
docker logs securityhub-heatmap
```

- To stop the local container:

```
docker container stop securityhub-heatmap
```

- For production implementation, please see the cdk_deployment which will deploy a fargate hosted instance of the container, configured with OIDC authentication