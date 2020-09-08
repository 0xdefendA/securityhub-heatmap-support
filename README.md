# securityhub-heatmap-support
Supporting code, docs, issues, etc for the securityhub-heatmap container


## CDK
The cdk_deployment directory contains code to get a working deployment of the heatmap in a Fargate ECS cluster. The cluster will be created along with a load balancer and supporting vpcs. A TLS cert is not included, but you can either add to the CDK deployment, or add a TLS listener with an appropriate cert after deployment.

### Environment
The default environment/configuration variables are set initially in config.yml.

You can and should override these in the container environment, especially to set:

 - SERVER_NAME : dns name of the resulting server (i.e. heatmap.somewhere.com)
 - PREFERRED_URL_SCHEME: http by default, should set to https in a production setting
 - OIDC* (see below)
 - REGIONS: a list of regions you'd like to retrieve findings from
 - CACHE_EXPIRATION: 10 min by default, This determines the frequency by which the heatmap will refresh it's cache of all findings from security hub. Any updates within the heatmap are cached on update. If you expect frequent external updates to findings, set the expiration accordingly. (sec = seconds, min = minutes, hours=hours, days=days )
 - DB_FILENAME: cache file location (set if you would like it elsewhere, an EFS mount, etc)
 - AWS_DEFAULT_REGION: the region the hub will operate in by default for making calls to securityhub.


 ### OIDC
 By default the heatmap is authenticated through OIDC. You should issue a client ID and client Secret from your Identity Provider (IDP). You can pass the client secret either through an environment variable directly, or by passing a secrets manager secret name and that name will be retrieved at run time.

 - OIDC_PROVIDER_NAME: google by default, set to whatever name you'd like. Set to 'none' to disable OIDC if you are authenticating through some other means (alb, proxy, etc)
 - OIDC_ISSUER: the IDP issuer address "https://accounts.google.com" by default
 - OIDC_CLIENT_ID: set to the client ID you receive from your IDP
 - OIDC_CLIENT_SECRET_NAME: the name you use if you store the client secret in secrets manager
 - OIDC_CLIENT_SECRET: the raw secret if you prefer to pass it without using secrets manager
 - OIDC_SESSION_LIFETIME_HOURS: 7 hours by default, set as desired.

 ### Usage Instructions

 - Install and configure the AWS CLI. Please see https://docs.aws.amazon.com/cli/latest/userguide/installing.html for details.

 - Authenticate your Docker client to the heatmap registry:

```
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 717455710680.dkr.ecr.us-west-2.amazonaws.com
```

On successful login the following message will be seen :

    Login Succeeded

 - Now pull the docker image
```
docker pull 717455710680.dkr.ecr.us-west-2.amazonaws.com/defenda/securityhub-heatmap:latest
```

 - Start a single local instance of the container via the following:

```
docker run --rm -d -p 80:80 -v ${HOME}/.aws/:/root/.aws/:ro -e 'OIDC_PROVIDER_NAME=none' --name securityhub-heatmap 717455710680.dkr.ecr.us-west-2.amazonaws.com/defenda/securityhub-heatmap
```

- The above command publishes the container's port 80 to your localhost with NO AUTHENTICATION. This is suitable for local testing/integration only.   To access the web UI enter http://localhost/ in your browser.

- For troubleshooting you can access the local container logs via:

```
docker logs securityhub-heatmap
```

- To stop the local container:

```
docker container stop securityhub-heatmap
```

- For production implementation, please see the cdk_deployment which will deploy a fargate hosted instance of the container, configured with OIDC authentication