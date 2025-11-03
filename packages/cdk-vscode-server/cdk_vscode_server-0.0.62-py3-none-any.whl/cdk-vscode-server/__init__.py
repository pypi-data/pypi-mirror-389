r'''
![Source](https://img.shields.io/github/stars/MV-Consulting/cdk-vscode-server?logo=github&label=GitHub%20Stars)
[![Build Status](https://github.com/MV-Consulting/cdk-vscode-server/actions/workflows/build.yml/badge.svg)](https://github.com/MV-Consulting/cdk-vscode-server/actions/workflows/build.yml)
[![ESLint Code Formatting](https://img.shields.io/badge/code_style-eslint-brightgreen.svg)](https://eslint.org)
[![Latest release](https://img.shields.io/github/release/MV-Consulting/cdk-vscode-server.svg)](https://github.com/MV-Consulting/cdk-vscode-server/releases)
![GitHub](https://img.shields.io/github/license/MV-Consulting/cdk-vscode-server)
[![npm](https://img.shields.io/npm/dt/@mavogel/cdk-vscode-server?label=npm&color=orange)](https://www.npmjs.com/package/@mavogel/cdk-vscode-server)
[![typescript](https://img.shields.io/badge/jsii-typescript-blueviolet.svg)](https://www.npmjs.com/package/@mavogel/cdk-vscode-server)

# cdk-vscode-server

Running your dev IDE vscode on AWS for development and workshop purposes.

> [!Note]
> This construct is designed for workshop purposes and does not fulfill all security and authentication best practices.

![EXPERIMENTAL](https://img.shields.io/badge/stability-experimantal-orange?style=for-the-badge)**<br>This is an early version of the package. The API will change while I
we implement new features. Therefore make sure you use an exact version in your `package.json` before it reaches 1.0.0.**

## Table of Contents

* [Features](#features)
* [Usage](#usage)

  * [Standard](#Standard)
  * [Custom Domain Configuration](#custom-domain-configuration)
* [Solution Design](#solution-design)
* [Inspiration](#inspiration)

## Features

* ⚡ **Quick Setup**: Spin up and configure your [vscode](https://code.visualstudio.com/) server in under 10 minutes in your AWS account
* 📏 **Best Practice Setup**: Set up with [projen](https://projen.io/) and a [single configuration file](./.projenrc.ts) to keep your changes centralized.
* 🤹‍♂️ **Pre-installed packages**: Besides the [vscode](https://code.visualstudio.com/) server, other tools and software packages such as `git`, `docker`, `awscli` `nodejs` and `python` are pre-installed on the EC2 instance.
* 🌐 **Custom Domain Support**: Use your own domain name with automatic ACM certificate creation and Route53 DNS configuration, or bring your existing certificate.
* 💰 **Auto-Stop**: Automatically stop EC2 instances after inactivity with Elastic IP retention - save up to 75% on costs for development environments
* 🏗️ **Extensibility**: Pass in properties to the construct, which start with `additional*`. They allow you to extend the configuration to your needs. There are more to come...

## Usage

Actually we supported 2 modes:

### Standard

The following steps get you started:

1. Create a new `awscdk-app` via

```bash
npx projen new awscdk-app-ts --package-manager=npm
```

1. Add `@mavogel/cdk-vscode-server` as a dependency to your project in the `.projenrc.ts` file
2. Run `npx projen` to install it
3. Add the following to the `src/main.ts` file:

```python
import { App, Stack, StackProps } from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import {
  LinuxArchitectureType,
  LinuxFlavorType,
  VSCodeServer
} from '@mavogel/cdk-vscode-server';

export class MyStack extends Stack {
  constructor(scope: Construct, id: string, props: StackProps = {}) {
    super(scope, id, props);

    new VSCodeServer(this, 'vscode', {
      // for example (or simply use the defaults by not setting the properties)
      instanceVolumeSize: 8,
      instanceClass: ec2.InstanceClass.M7G,
      instanceSize: ec2.InstanceSize.LARGE,
      instanceOperatingSystem: LinuxFlavorType.UBUNTU_22,
      instanceCpuArchitecture: LinuxArchitectureType.ARM,

      // 👇🏽 or if you want to give the InstanceRole more permissions
      additionalInstanceRolePolicies: [
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: [
            'codebuild:*',
          ],
          resources: [
            `arn:aws:codebuild:*:${Stack.of(this).account}:*/*`,
          ],
        }),
      ]

      // and more... 💡
    });
  }
}

const env = {
  account: '123456789912',
  region: 'eu-central-1',
};

const app = new App();
new MyStack(app, 'vscode-server', { env });
app.synth();
```

and deploy it

```bash
npx projen build
npx projen deploy
```

with the output

```console
✨  Deployment time: 509.87s

Outputs:
dev.vscodedomainName6729AA39 = https://d1foo65bar4baz.cloudfront.net/?folder=/Workshop
dev.vscodepassword64FBCA12 = foobarbaz
```

See the [examples](./examples) folder for more inspiration.

### Custom Domain Configuration

You can configure your VS Code Server with a custom domain name instead of using the default CloudFront domain. The construct supports three different configuration options:

#### Option 1: Auto-create Certificate with DNS Validation

```python
new VSCodeServer(this, 'vscode', {
  domainName: 'vscode.example.com',
  hostedZoneId: 'Z123EXAMPLE456',  // optional - will auto-discover if not provided
  autoCreateCertificate: true,
});
```

This will:

* Create an ACM certificate in us-east-1 (required for CloudFront)
* Validate the certificate using DNS validation
* Create a Route53 A record pointing to the CloudFront distribution
* Configure the CloudFront distribution with the custom domain

#### Option 2: Use Existing Certificate

```python
new VSCodeServer(this, 'vscode', {
  domainName: 'vscode.example.com',
  hostedZoneId: 'Z123EXAMPLE456',
  certificateArn: 'arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012',
});
```

**Requirements:**

* Certificate must be in us-east-1 region
* Certificate must be validated and ready to use
* Certificate must include the domain name

#### Option 3: Default (No Custom Domain)

```python
new VSCodeServer(this, 'vscode', {
  // No domain configuration - uses CloudFront default domain
});
```

For complete examples, see [examples/custom-domain/main.ts](./examples/custom-domain/main.ts).

1. Then open the domain name in your favorite browser and you'd see the following login screen:
   ![vscode-server-ui-login](docs/img/vscode-server-ui-login-min.png)
2. After entering the password, you are logged into VSCode and can start coding :tada:

![vscode-server-ui](docs/img/vscode-server-ui-min.png)

> [!Important]
> There are issues with copy pasting into the VSCode terminal within the Firefox browser (2025-01-12)

### Auto-Stop Configuration

Save up to 75% on costs by automatically stopping EC2 instances when idle:

```python
new VSCodeServer(this, 'vscode', {
  enableAutoStop: true,              // Enable auto-stop feature
  idleTimeoutMinutes: 30,            // Stop after 30 minutes of no activity (default)
  idleCheckIntervalMinutes: 5,       // Check for idle activity every 5 minutes (default)
});
```

**How it works:**

1. **Idle Detection**: Monitors CloudFront request metrics at configured intervals (default: every 5 minutes)
2. **Auto-Stop**: Stops the EC2 instance after the configured idle timeout when no requests are detected
3. **Static IP**: Allocates an Elastic IP to maintain a consistent public IP address across stop/start cycles
4. **Manual Resume**: Users can manually start the instance via AWS Console or CLI when needed

**Cost Savings Example:**

* **Without auto-stop**: m7g.xlarge running 24/7 = ~$120/month
* **With auto-stop** (8 hours/day, 5 days/week): ~$30/month
* **Savings**: ~$90/month (75% reduction)

**Additional costs:**

* Elastic IP (allocated): ~$3.65/month
* Lambda function (IdleMonitor): ~$0.10/month
* EventBridge rule: Negligible
* **Net savings**: ~$86/month per instance

**Architecture Components:**

* Elastic IP for consistent public addressing
* EventBridge rule triggering idle monitoring at configured intervals
* IdleMonitor Lambda function checking CloudWatch metrics for request activity
* CloudWatch metrics from CloudFront distribution

**Integration Testing:**

The stop-on-idle functionality includes comprehensive integration tests (`integ-tests/integ.stop-on-idle.ts`) that verify the complete workflow:

1. **Phase 1 - Verify Auto-Stop**: Waits for the instance to automatically stop after the configured idle timeout
2. **Phase 2 - Disable IdleMonitor**: Disables the EventBridge rule to prevent the instance from being stopped again during testing
3. **Phase 3 - Start Instance**: Starts the stopped instance and waits for it to reach the running state
4. **Phase 4 - Verify Login**: Confirms that VS Code Server is accessible through CloudFront after the instance has been restarted

This 4-phase test ensures that:

* Idle detection works correctly based on CloudWatch metrics
* Instance stops automatically when no activity is detected
* Instance can be successfully restarted after being stopped
* VS Code Server remains accessible after stop/start cycles
* Elastic IP maintains connectivity across state changes

Run integration tests with:

```bash
npm run integ-test
```

## Solution Design

<details>
  <summary>... if you're curious about click here for the details</summary>

![vscode-server-solution-design](docs/img/vscode-server.drawio-min.png)

</details>

## Inspiration

This project was created based on the following inspiration

* [vscode-on-ec2-for-prototyping](https://github.com/aws-samples/vscode-on-ec2-for-prototyping): as baseline, which unfortunately was outdated
* [aws-terraform-dev-container](https://github.com/awslabs/aws-terraform-dev-container): as baseline for terraform, but unfortunately also outdated
* [java-on-aws-workshop-ide-only.yaml](https://github.com/aws-samples/java-on-aws/blob/main/labs/unicorn-store/infrastructure/cfn/java-on-aws-workshop-ide-only.yaml): an already synthesized cloudformation stack, which used mostly python as the custom resources
* [fleet-workshop-team-stack-self.json](https://static.us-east-1.prod.workshops.aws/public/cc4aa67e-5b7a-4df1-abf7-c42502899a25/assets/fleet-workshop-team-stack-self.json): also an already synthesized cloudformation stack, which did much more as I currently implemented here.
* [eks-workshop-vscode-cfn.yaml](https://github.com/aws-samples/eks-workshop-v2/blob/main/lab/cfn/eks-workshop-vscode-cfn.yaml): another great baseline

## 🚀 Unlock the Full Potential of Your AWS Cloud Infrastructure

Hi, I’m Manuel, an AWS expert passionate about empowering businesses with **scalable, resilient, and cost-optimized cloud solutions**. With **MV Consulting**, I specialize in crafting **tailored AWS architectures** and **DevOps-driven workflows** that not only meet your current needs but grow with you.

---


### 🌟 Why Work With Me?

✔️ **Tailored AWS Solutions:** Every business is unique, so I design custom solutions that fit your goals and challenges.
✔️ **Well-Architected Designs:** From scalability to security, my solutions align with AWS Well-Architected Framework.
✔️ **Cloud-Native Focus:** I specialize in modern, cloud-native systems that embrace the full potential of AWS.
✔️ **Business-Driven Tech:** Technology should serve your business, not the other way around.

---


### 🛠 What I Bring to the Table

🔑 **12x AWS Certifications**
I’m **AWS Certified Solutions Architect and DevOps – Professional** and hold numerous additional certifications, so you can trust I’ll bring industry best practices to your projects. Feel free to explose by [badges](https://www.credly.com/users/manuel-vogel)

⚙️ **Infrastructure as Code (IaC)**
With deep expertise in **AWS CDK** and **Terraform**, I ensure your infrastructure is automated, maintainable, and scalable.

📦 **DevOps Expertise**
From CI/CD pipelines with **GitHub Actions** and **GitLab CI** to container orchestration **Kubernetes** and others, I deliver workflows that are smooth and efficient.

🌐 **Hands-On Experience**
With over **7 years of AWS experience** and a decade in the tech world, I’ve delivered solutions for companies large and small. My open-source contributions showcase my commitment to transparency and innovation. Feel free to explore my [GitHub profile](https://github.com/mavogel)

---


### 💼 Let’s Build Something Great Together

I know that choosing the right partner is critical to your success. When you work with me, you’re not just contracting an engineer – you’re gaining a trusted advisor and hands-on expert who cares about your business as much as you do.

✔️ **Direct Collaboration**: No middlemen or red tape – you work with me directly.
✔️ **Transparent Process**: Expect open communication, clear timelines, and visible results.
✔️ **Real Value**: My solutions focus on delivering measurable impact for your business.

<a href="https://tinyurl.com/mvc-15min"><img alt="Schedule your call" src="https://img.shields.io/badge/schedule%20your%20call-success.svg?style=for-the-badge"/></a>

---


## 🙌 Acknowledgements

Big shoutout to the amazing team behind [Projen](https://github.com/projen/projen)!
Their groundbreaking work simplifies cloud infrastructure projects and inspires us every day. 💡

## Author

[Manuel Vogel](https://manuel-vogel.de/about/)

[![](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/manuel-vogel)
[![](https://img.shields.io/badge/GitHub-2b3137?style=for-the-badge&logo=github&logoColor=white)](https://github.com/mavogel)
'''
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

import abc
import builtins
import datetime
import enum
import typing

import jsii
import publication
import typing_extensions

import typeguard
from importlib.metadata import version as _metadata_package_version
TYPEGUARD_MAJOR_VERSION = int(_metadata_package_version('typeguard').split('.')[0])

def check_type(argname: str, value: object, expected_type: typing.Any) -> typing.Any:
    if TYPEGUARD_MAJOR_VERSION <= 2:
        return typeguard.check_type(argname=argname, value=value, expected_type=expected_type) # type:ignore
    else:
        if isinstance(value, jsii._reference_map.InterfaceDynamicProxy): # pyright: ignore [reportAttributeAccessIssue]
           pass
        else:
            if TYPEGUARD_MAJOR_VERSION == 3:
                typeguard.config.collection_check_strategy = typeguard.CollectionCheckStrategy.ALL_ITEMS # type:ignore
                typeguard.check_type(value=value, expected_type=expected_type) # type:ignore
            else:
                typeguard.check_type(value=value, expected_type=expected_type, collection_check_strategy=typeguard.CollectionCheckStrategy.ALL_ITEMS) # type:ignore

from ._jsii import *

import aws_cdk.aws_apigateway as _aws_cdk_aws_apigateway_ceddda9d
import aws_cdk.aws_cloudfront as _aws_cdk_aws_cloudfront_ceddda9d
import aws_cdk.aws_dynamodb as _aws_cdk_aws_dynamodb_ceddda9d
import aws_cdk.aws_ec2 as _aws_cdk_aws_ec2_ceddda9d
import aws_cdk.aws_events as _aws_cdk_aws_events_ceddda9d
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_lambda as _aws_cdk_aws_lambda_ceddda9d
import constructs as _constructs_77d1e7e8


class IdleMonitor(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@mavogel/cdk-vscode-server.IdleMonitor",
):
    '''(experimental) Construct that monitors CloudFront request metrics and stops the EC2 instance when idle.

    :stability: experimental
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        distribution: _aws_cdk_aws_cloudfront_ceddda9d.IDistribution,
        idle_timeout_minutes: jsii.Number,
        instance: _aws_cdk_aws_ec2_ceddda9d.IInstance,
        check_interval_minutes: typing.Optional[jsii.Number] = None,
        skip_status_checks: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param distribution: (experimental) The CloudFront distribution to monitor for activity.
        :param idle_timeout_minutes: (experimental) Number of minutes of inactivity before stopping the instance.
        :param instance: (experimental) The EC2 instance to monitor.
        :param check_interval_minutes: (experimental) How often to check for idle activity (in minutes). Default: 5 - Check every 5 minutes
        :param skip_status_checks: (experimental) Skip instance status checks before stopping When true, IdleMonitor will stop idle instances even if status checks haven't passed This is useful for integration tests where status check initialization time exceeds test timeout limits. WARNING: For testing only - in production, you should wait for status checks to pass before stopping instances Default: false

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__20b577827aba935251db87d8d64ce79318aa5807c34b891715e4a171e2ae5b04)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = IdleMonitorProps(
            distribution=distribution,
            idle_timeout_minutes=idle_timeout_minutes,
            instance=instance,
            check_interval_minutes=check_interval_minutes,
            skip_status_checks=skip_status_checks,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="function")
    def function(self) -> _aws_cdk_aws_lambda_ceddda9d.Function:
        '''(experimental) The Lambda function that performs idle monitoring.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_lambda_ceddda9d.Function, jsii.get(self, "function"))

    @builtins.property
    @jsii.member(jsii_name="scheduleRule")
    def schedule_rule(self) -> _aws_cdk_aws_events_ceddda9d.Rule:
        '''(experimental) The EventBridge rule that triggers idle monitoring checks.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_events_ceddda9d.Rule, jsii.get(self, "scheduleRule"))


@jsii.data_type(
    jsii_type="@mavogel/cdk-vscode-server.IdleMonitorProps",
    jsii_struct_bases=[],
    name_mapping={
        "distribution": "distribution",
        "idle_timeout_minutes": "idleTimeoutMinutes",
        "instance": "instance",
        "check_interval_minutes": "checkIntervalMinutes",
        "skip_status_checks": "skipStatusChecks",
    },
)
class IdleMonitorProps:
    def __init__(
        self,
        *,
        distribution: _aws_cdk_aws_cloudfront_ceddda9d.IDistribution,
        idle_timeout_minutes: jsii.Number,
        instance: _aws_cdk_aws_ec2_ceddda9d.IInstance,
        check_interval_minutes: typing.Optional[jsii.Number] = None,
        skip_status_checks: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''(experimental) Props for IdleMonitor construct.

        :param distribution: (experimental) The CloudFront distribution to monitor for activity.
        :param idle_timeout_minutes: (experimental) Number of minutes of inactivity before stopping the instance.
        :param instance: (experimental) The EC2 instance to monitor.
        :param check_interval_minutes: (experimental) How often to check for idle activity (in minutes). Default: 5 - Check every 5 minutes
        :param skip_status_checks: (experimental) Skip instance status checks before stopping When true, IdleMonitor will stop idle instances even if status checks haven't passed This is useful for integration tests where status check initialization time exceeds test timeout limits. WARNING: For testing only - in production, you should wait for status checks to pass before stopping instances Default: false

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dbe3d723d712645d045480dfd02714e4231593f8cb83f7d7c54a22b69d7930d9)
            check_type(argname="argument distribution", value=distribution, expected_type=type_hints["distribution"])
            check_type(argname="argument idle_timeout_minutes", value=idle_timeout_minutes, expected_type=type_hints["idle_timeout_minutes"])
            check_type(argname="argument instance", value=instance, expected_type=type_hints["instance"])
            check_type(argname="argument check_interval_minutes", value=check_interval_minutes, expected_type=type_hints["check_interval_minutes"])
            check_type(argname="argument skip_status_checks", value=skip_status_checks, expected_type=type_hints["skip_status_checks"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "distribution": distribution,
            "idle_timeout_minutes": idle_timeout_minutes,
            "instance": instance,
        }
        if check_interval_minutes is not None:
            self._values["check_interval_minutes"] = check_interval_minutes
        if skip_status_checks is not None:
            self._values["skip_status_checks"] = skip_status_checks

    @builtins.property
    def distribution(self) -> _aws_cdk_aws_cloudfront_ceddda9d.IDistribution:
        '''(experimental) The CloudFront distribution to monitor for activity.

        :stability: experimental
        '''
        result = self._values.get("distribution")
        assert result is not None, "Required property 'distribution' is missing"
        return typing.cast(_aws_cdk_aws_cloudfront_ceddda9d.IDistribution, result)

    @builtins.property
    def idle_timeout_minutes(self) -> jsii.Number:
        '''(experimental) Number of minutes of inactivity before stopping the instance.

        :stability: experimental
        '''
        result = self._values.get("idle_timeout_minutes")
        assert result is not None, "Required property 'idle_timeout_minutes' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def instance(self) -> _aws_cdk_aws_ec2_ceddda9d.IInstance:
        '''(experimental) The EC2 instance to monitor.

        :stability: experimental
        '''
        result = self._values.get("instance")
        assert result is not None, "Required property 'instance' is missing"
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.IInstance, result)

    @builtins.property
    def check_interval_minutes(self) -> typing.Optional[jsii.Number]:
        '''(experimental) How often to check for idle activity (in minutes).

        :default: 5 - Check every 5 minutes

        :stability: experimental
        '''
        result = self._values.get("check_interval_minutes")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def skip_status_checks(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Skip instance status checks before stopping When true, IdleMonitor will stop idle instances even if status checks haven't passed This is useful for integration tests where status check initialization time exceeds test timeout limits.

        WARNING: For testing only - in production, you should wait for status checks
        to pass before stopping instances

        :default: false

        :stability: experimental
        '''
        result = self._values.get("skip_status_checks")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "IdleMonitorProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.enum(jsii_type="@mavogel/cdk-vscode-server.LinuxArchitectureType")
class LinuxArchitectureType(enum.Enum):
    '''(experimental) The architecture of the cpu you want to run vscode server on.

    :stability: experimental
    '''

    ARM = "ARM"
    '''(experimental) ARM architecture.

    :stability: experimental
    '''
    AMD64 = "AMD64"
    '''(experimental) AMD64 architecture.

    :stability: experimental
    '''


@jsii.enum(jsii_type="@mavogel/cdk-vscode-server.LinuxFlavorType")
class LinuxFlavorType(enum.Enum):
    '''(experimental) The flavor of linux you want to run vscode server on.

    :stability: experimental
    '''

    UBUNTU_22 = "UBUNTU_22"
    '''(experimental) Ubuntu 22.

    :stability: experimental
    '''
    UBUNTU_24 = "UBUNTU_24"
    '''(experimental) Ubuntu 24.

    :stability: experimental
    '''
    AMAZON_LINUX_2023 = "AMAZON_LINUX_2023"
    '''(experimental) Amazon Linux 2023.

    :stability: experimental
    '''


class StatusCheckApi(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@mavogel/cdk-vscode-server.StatusCheckApi",
):
    '''(experimental) API Gateway endpoint for checking instance status, used by resume page for polling.

    :stability: experimental
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        instance: _aws_cdk_aws_ec2_ceddda9d.IInstance,
        state_table: _aws_cdk_aws_dynamodb_ceddda9d.ITable,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param instance: (experimental) The EC2 instance to check status for.
        :param state_table: (experimental) DynamoDB table for tracking instance state.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e7d6ff0408a4ed7de894609afb3872f4c204f0a40f6d03c29beea21657930c48)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = StatusCheckApiProps(instance=instance, state_table=state_table)

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="api")
    def api(self) -> _aws_cdk_aws_apigateway_ceddda9d.RestApi:
        '''(experimental) The API Gateway REST API.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_apigateway_ceddda9d.RestApi, jsii.get(self, "api"))

    @builtins.property
    @jsii.member(jsii_name="apiUrl")
    def api_url(self) -> builtins.str:
        '''(experimental) The URL of the status check API endpoint.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "apiUrl"))

    @builtins.property
    @jsii.member(jsii_name="function")
    def function(self) -> _aws_cdk_aws_lambda_ceddda9d.Function:
        '''(experimental) The Lambda function that handles status check requests.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_lambda_ceddda9d.Function, jsii.get(self, "function"))


@jsii.data_type(
    jsii_type="@mavogel/cdk-vscode-server.StatusCheckApiProps",
    jsii_struct_bases=[],
    name_mapping={"instance": "instance", "state_table": "stateTable"},
)
class StatusCheckApiProps:
    def __init__(
        self,
        *,
        instance: _aws_cdk_aws_ec2_ceddda9d.IInstance,
        state_table: _aws_cdk_aws_dynamodb_ceddda9d.ITable,
    ) -> None:
        '''(experimental) Props for StatusCheckApi construct.

        :param instance: (experimental) The EC2 instance to check status for.
        :param state_table: (experimental) DynamoDB table for tracking instance state.

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c79670a668f6fc2cfc6b40dad4ca1ee32a52c96f10f70d5cce6051bc058610f4)
            check_type(argname="argument instance", value=instance, expected_type=type_hints["instance"])
            check_type(argname="argument state_table", value=state_table, expected_type=type_hints["state_table"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "instance": instance,
            "state_table": state_table,
        }

    @builtins.property
    def instance(self) -> _aws_cdk_aws_ec2_ceddda9d.IInstance:
        '''(experimental) The EC2 instance to check status for.

        :stability: experimental
        '''
        result = self._values.get("instance")
        assert result is not None, "Required property 'instance' is missing"
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.IInstance, result)

    @builtins.property
    def state_table(self) -> _aws_cdk_aws_dynamodb_ceddda9d.ITable:
        '''(experimental) DynamoDB table for tracking instance state.

        :stability: experimental
        '''
        result = self._values.get("state_table")
        assert result is not None, "Required property 'state_table' is missing"
        return typing.cast(_aws_cdk_aws_dynamodb_ceddda9d.ITable, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "StatusCheckApiProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class VSCodeServer(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@mavogel/cdk-vscode-server.VSCodeServer",
):
    '''(experimental) VSCodeServer - spin it up in under 10 minutes.

    :stability: experimental
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        additional_instance_role_policies: typing.Optional[typing.Sequence[_aws_cdk_aws_iam_ceddda9d.PolicyStatement]] = None,
        additional_tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        auto_create_certificate: typing.Optional[builtins.bool] = None,
        certificate_arn: typing.Optional[builtins.str] = None,
        dev_server_base_path: typing.Optional[builtins.str] = None,
        dev_server_port: typing.Optional[jsii.Number] = None,
        domain_name: typing.Optional[builtins.str] = None,
        enable_auto_stop: typing.Optional[builtins.bool] = None,
        home_folder: typing.Optional[builtins.str] = None,
        hosted_zone_id: typing.Optional[builtins.str] = None,
        idle_check_interval_minutes: typing.Optional[jsii.Number] = None,
        idle_timeout_minutes: typing.Optional[jsii.Number] = None,
        instance_class: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.InstanceClass] = None,
        instance_cpu_architecture: typing.Optional[LinuxArchitectureType] = None,
        instance_name: typing.Optional[builtins.str] = None,
        instance_operating_system: typing.Optional[LinuxFlavorType] = None,
        instance_size: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.InstanceSize] = None,
        instance_volume_size: typing.Optional[jsii.Number] = None,
        skip_status_checks: typing.Optional[builtins.bool] = None,
        vscode_password: typing.Optional[builtins.str] = None,
        vscode_user: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param additional_instance_role_policies: (experimental) Additional instance role policies. Default: - []
        :param additional_tags: (experimental) Additional tags to add to the instance. Default: - {}
        :param auto_create_certificate: (experimental) Auto-create ACM certificate with DNS validation in us-east-1 region Requires hostedZoneId to be provided for DNS validation Cannot be used together with certificateArn Certificate will automatically be created in us-east-1 as required by CloudFront. Default: false
        :param certificate_arn: (experimental) ARN of existing ACM certificate for the domain Certificate must be in us-east-1 region for CloudFront Cannot be used together with autoCreateCertificate. Default: - auto-create certificate if autoCreateCertificate is true
        :param dev_server_base_path: (experimental) Base path for the application to be added to Nginx sites-available list. Default: - app
        :param dev_server_port: (experimental) Port for the DevServer. Default: - 8081
        :param domain_name: (experimental) Custom domain name for the VS Code server When provided, creates a CloudFront distribution with this domain name and sets up Route53 A record pointing to the distribution. Default: - uses CloudFront default domain
        :param enable_auto_stop: (experimental) Enable automatic instance stop when idle Monitors CloudFront metrics and stops the EC2 instance after specified idle time. Default: false
        :param home_folder: (experimental) Folder to open in VS Code server. Default: - /Workshop
        :param hosted_zone_id: (experimental) Route53 hosted zone ID for the domain Required when using autoCreateCertificate If not provided, will attempt to lookup hosted zone from domain name. Default: - auto-discover from domain name
        :param idle_check_interval_minutes: (experimental) How often to check for idle activity (in minutes) Only applies when enableAutoStop is true. Default: 5 - Check every 5 minutes
        :param idle_timeout_minutes: (experimental) Minutes of inactivity before stopping the instance Only applies when enableAutoStop is true. Default: 30
        :param instance_class: (experimental) VSCode Server EC2 instance class. Default: - m7g
        :param instance_cpu_architecture: (experimental) VSCode Server EC2 cpu architecture for the operating system. Default: - arm
        :param instance_name: (experimental) VSCode Server EC2 instance name. Default: - VSCodeServer
        :param instance_operating_system: (experimental) VSCode Server EC2 operating system. Default: - Ubuntu-22
        :param instance_size: (experimental) VSCode Server EC2 instance size. Default: - xlarge
        :param instance_volume_size: (experimental) VSCode Server EC2 instance volume size in GB. Default: - 40
        :param skip_status_checks: (experimental) Skip instance status checks in IdleMonitor When true, IdleMonitor will stop idle instances even if status checks haven't passed This is useful for integration tests where status check initialization time exceeds the test timeout limits. WARNING: For testing only - in production, you should wait for status checks to pass before stopping instances to avoid stopping unhealthy instances Default: false
        :param vscode_password: (experimental) Password for VSCode Server. Default: - empty and will then be generated
        :param vscode_user: (experimental) UserName for VSCode Server. Default: - participant

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__13d98894e731d8d5e45fa4088dfd79af04a4cb66cead591188c4ba44d922873c)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = VSCodeServerProps(
            additional_instance_role_policies=additional_instance_role_policies,
            additional_tags=additional_tags,
            auto_create_certificate=auto_create_certificate,
            certificate_arn=certificate_arn,
            dev_server_base_path=dev_server_base_path,
            dev_server_port=dev_server_port,
            domain_name=domain_name,
            enable_auto_stop=enable_auto_stop,
            home_folder=home_folder,
            hosted_zone_id=hosted_zone_id,
            idle_check_interval_minutes=idle_check_interval_minutes,
            idle_timeout_minutes=idle_timeout_minutes,
            instance_class=instance_class,
            instance_cpu_architecture=instance_cpu_architecture,
            instance_name=instance_name,
            instance_operating_system=instance_operating_system,
            instance_size=instance_size,
            instance_volume_size=instance_volume_size,
            skip_status_checks=skip_status_checks,
            vscode_password=vscode_password,
            vscode_user=vscode_user,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property
    @jsii.member(jsii_name="domainName")
    def domain_name(self) -> builtins.str:
        '''(experimental) The name of the domain the server is reachable.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "domainName"))

    @builtins.property
    @jsii.member(jsii_name="instance")
    def instance(self) -> _aws_cdk_aws_ec2_ceddda9d.IInstance:
        '''(experimental) The EC2 instance running VS Code Server.

        :stability: experimental
        '''
        return typing.cast(_aws_cdk_aws_ec2_ceddda9d.IInstance, jsii.get(self, "instance"))

    @builtins.property
    @jsii.member(jsii_name="password")
    def password(self) -> builtins.str:
        '''(experimental) The password to login to the server.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "password"))

    @builtins.property
    @jsii.member(jsii_name="idleMonitor")
    def idle_monitor(self) -> typing.Optional[IdleMonitor]:
        '''(experimental) The IdleMonitor construct (only present if enableAutoStop is true).

        :stability: experimental
        '''
        return typing.cast(typing.Optional[IdleMonitor], jsii.get(self, "idleMonitor"))


@jsii.data_type(
    jsii_type="@mavogel/cdk-vscode-server.VSCodeServerProps",
    jsii_struct_bases=[],
    name_mapping={
        "additional_instance_role_policies": "additionalInstanceRolePolicies",
        "additional_tags": "additionalTags",
        "auto_create_certificate": "autoCreateCertificate",
        "certificate_arn": "certificateArn",
        "dev_server_base_path": "devServerBasePath",
        "dev_server_port": "devServerPort",
        "domain_name": "domainName",
        "enable_auto_stop": "enableAutoStop",
        "home_folder": "homeFolder",
        "hosted_zone_id": "hostedZoneId",
        "idle_check_interval_minutes": "idleCheckIntervalMinutes",
        "idle_timeout_minutes": "idleTimeoutMinutes",
        "instance_class": "instanceClass",
        "instance_cpu_architecture": "instanceCpuArchitecture",
        "instance_name": "instanceName",
        "instance_operating_system": "instanceOperatingSystem",
        "instance_size": "instanceSize",
        "instance_volume_size": "instanceVolumeSize",
        "skip_status_checks": "skipStatusChecks",
        "vscode_password": "vscodePassword",
        "vscode_user": "vscodeUser",
    },
)
class VSCodeServerProps:
    def __init__(
        self,
        *,
        additional_instance_role_policies: typing.Optional[typing.Sequence[_aws_cdk_aws_iam_ceddda9d.PolicyStatement]] = None,
        additional_tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        auto_create_certificate: typing.Optional[builtins.bool] = None,
        certificate_arn: typing.Optional[builtins.str] = None,
        dev_server_base_path: typing.Optional[builtins.str] = None,
        dev_server_port: typing.Optional[jsii.Number] = None,
        domain_name: typing.Optional[builtins.str] = None,
        enable_auto_stop: typing.Optional[builtins.bool] = None,
        home_folder: typing.Optional[builtins.str] = None,
        hosted_zone_id: typing.Optional[builtins.str] = None,
        idle_check_interval_minutes: typing.Optional[jsii.Number] = None,
        idle_timeout_minutes: typing.Optional[jsii.Number] = None,
        instance_class: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.InstanceClass] = None,
        instance_cpu_architecture: typing.Optional[LinuxArchitectureType] = None,
        instance_name: typing.Optional[builtins.str] = None,
        instance_operating_system: typing.Optional[LinuxFlavorType] = None,
        instance_size: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.InstanceSize] = None,
        instance_volume_size: typing.Optional[jsii.Number] = None,
        skip_status_checks: typing.Optional[builtins.bool] = None,
        vscode_password: typing.Optional[builtins.str] = None,
        vscode_user: typing.Optional[builtins.str] = None,
    ) -> None:
        '''(experimental) Properties for the VSCodeServer construct.

        :param additional_instance_role_policies: (experimental) Additional instance role policies. Default: - []
        :param additional_tags: (experimental) Additional tags to add to the instance. Default: - {}
        :param auto_create_certificate: (experimental) Auto-create ACM certificate with DNS validation in us-east-1 region Requires hostedZoneId to be provided for DNS validation Cannot be used together with certificateArn Certificate will automatically be created in us-east-1 as required by CloudFront. Default: false
        :param certificate_arn: (experimental) ARN of existing ACM certificate for the domain Certificate must be in us-east-1 region for CloudFront Cannot be used together with autoCreateCertificate. Default: - auto-create certificate if autoCreateCertificate is true
        :param dev_server_base_path: (experimental) Base path for the application to be added to Nginx sites-available list. Default: - app
        :param dev_server_port: (experimental) Port for the DevServer. Default: - 8081
        :param domain_name: (experimental) Custom domain name for the VS Code server When provided, creates a CloudFront distribution with this domain name and sets up Route53 A record pointing to the distribution. Default: - uses CloudFront default domain
        :param enable_auto_stop: (experimental) Enable automatic instance stop when idle Monitors CloudFront metrics and stops the EC2 instance after specified idle time. Default: false
        :param home_folder: (experimental) Folder to open in VS Code server. Default: - /Workshop
        :param hosted_zone_id: (experimental) Route53 hosted zone ID for the domain Required when using autoCreateCertificate If not provided, will attempt to lookup hosted zone from domain name. Default: - auto-discover from domain name
        :param idle_check_interval_minutes: (experimental) How often to check for idle activity (in minutes) Only applies when enableAutoStop is true. Default: 5 - Check every 5 minutes
        :param idle_timeout_minutes: (experimental) Minutes of inactivity before stopping the instance Only applies when enableAutoStop is true. Default: 30
        :param instance_class: (experimental) VSCode Server EC2 instance class. Default: - m7g
        :param instance_cpu_architecture: (experimental) VSCode Server EC2 cpu architecture for the operating system. Default: - arm
        :param instance_name: (experimental) VSCode Server EC2 instance name. Default: - VSCodeServer
        :param instance_operating_system: (experimental) VSCode Server EC2 operating system. Default: - Ubuntu-22
        :param instance_size: (experimental) VSCode Server EC2 instance size. Default: - xlarge
        :param instance_volume_size: (experimental) VSCode Server EC2 instance volume size in GB. Default: - 40
        :param skip_status_checks: (experimental) Skip instance status checks in IdleMonitor When true, IdleMonitor will stop idle instances even if status checks haven't passed This is useful for integration tests where status check initialization time exceeds the test timeout limits. WARNING: For testing only - in production, you should wait for status checks to pass before stopping instances to avoid stopping unhealthy instances Default: false
        :param vscode_password: (experimental) Password for VSCode Server. Default: - empty and will then be generated
        :param vscode_user: (experimental) UserName for VSCode Server. Default: - participant

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2e462747a4e6316ff07a1ca12065fecb7b143031e2052b9b3ed692a4d9a458c7)
            check_type(argname="argument additional_instance_role_policies", value=additional_instance_role_policies, expected_type=type_hints["additional_instance_role_policies"])
            check_type(argname="argument additional_tags", value=additional_tags, expected_type=type_hints["additional_tags"])
            check_type(argname="argument auto_create_certificate", value=auto_create_certificate, expected_type=type_hints["auto_create_certificate"])
            check_type(argname="argument certificate_arn", value=certificate_arn, expected_type=type_hints["certificate_arn"])
            check_type(argname="argument dev_server_base_path", value=dev_server_base_path, expected_type=type_hints["dev_server_base_path"])
            check_type(argname="argument dev_server_port", value=dev_server_port, expected_type=type_hints["dev_server_port"])
            check_type(argname="argument domain_name", value=domain_name, expected_type=type_hints["domain_name"])
            check_type(argname="argument enable_auto_stop", value=enable_auto_stop, expected_type=type_hints["enable_auto_stop"])
            check_type(argname="argument home_folder", value=home_folder, expected_type=type_hints["home_folder"])
            check_type(argname="argument hosted_zone_id", value=hosted_zone_id, expected_type=type_hints["hosted_zone_id"])
            check_type(argname="argument idle_check_interval_minutes", value=idle_check_interval_minutes, expected_type=type_hints["idle_check_interval_minutes"])
            check_type(argname="argument idle_timeout_minutes", value=idle_timeout_minutes, expected_type=type_hints["idle_timeout_minutes"])
            check_type(argname="argument instance_class", value=instance_class, expected_type=type_hints["instance_class"])
            check_type(argname="argument instance_cpu_architecture", value=instance_cpu_architecture, expected_type=type_hints["instance_cpu_architecture"])
            check_type(argname="argument instance_name", value=instance_name, expected_type=type_hints["instance_name"])
            check_type(argname="argument instance_operating_system", value=instance_operating_system, expected_type=type_hints["instance_operating_system"])
            check_type(argname="argument instance_size", value=instance_size, expected_type=type_hints["instance_size"])
            check_type(argname="argument instance_volume_size", value=instance_volume_size, expected_type=type_hints["instance_volume_size"])
            check_type(argname="argument skip_status_checks", value=skip_status_checks, expected_type=type_hints["skip_status_checks"])
            check_type(argname="argument vscode_password", value=vscode_password, expected_type=type_hints["vscode_password"])
            check_type(argname="argument vscode_user", value=vscode_user, expected_type=type_hints["vscode_user"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if additional_instance_role_policies is not None:
            self._values["additional_instance_role_policies"] = additional_instance_role_policies
        if additional_tags is not None:
            self._values["additional_tags"] = additional_tags
        if auto_create_certificate is not None:
            self._values["auto_create_certificate"] = auto_create_certificate
        if certificate_arn is not None:
            self._values["certificate_arn"] = certificate_arn
        if dev_server_base_path is not None:
            self._values["dev_server_base_path"] = dev_server_base_path
        if dev_server_port is not None:
            self._values["dev_server_port"] = dev_server_port
        if domain_name is not None:
            self._values["domain_name"] = domain_name
        if enable_auto_stop is not None:
            self._values["enable_auto_stop"] = enable_auto_stop
        if home_folder is not None:
            self._values["home_folder"] = home_folder
        if hosted_zone_id is not None:
            self._values["hosted_zone_id"] = hosted_zone_id
        if idle_check_interval_minutes is not None:
            self._values["idle_check_interval_minutes"] = idle_check_interval_minutes
        if idle_timeout_minutes is not None:
            self._values["idle_timeout_minutes"] = idle_timeout_minutes
        if instance_class is not None:
            self._values["instance_class"] = instance_class
        if instance_cpu_architecture is not None:
            self._values["instance_cpu_architecture"] = instance_cpu_architecture
        if instance_name is not None:
            self._values["instance_name"] = instance_name
        if instance_operating_system is not None:
            self._values["instance_operating_system"] = instance_operating_system
        if instance_size is not None:
            self._values["instance_size"] = instance_size
        if instance_volume_size is not None:
            self._values["instance_volume_size"] = instance_volume_size
        if skip_status_checks is not None:
            self._values["skip_status_checks"] = skip_status_checks
        if vscode_password is not None:
            self._values["vscode_password"] = vscode_password
        if vscode_user is not None:
            self._values["vscode_user"] = vscode_user

    @builtins.property
    def additional_instance_role_policies(
        self,
    ) -> typing.Optional[typing.List[_aws_cdk_aws_iam_ceddda9d.PolicyStatement]]:
        '''(experimental) Additional instance role policies.

        :default: - []

        :stability: experimental
        '''
        result = self._values.get("additional_instance_role_policies")
        return typing.cast(typing.Optional[typing.List[_aws_cdk_aws_iam_ceddda9d.PolicyStatement]], result)

    @builtins.property
    def additional_tags(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''(experimental) Additional tags to add to the instance.

        :default: - {}

        :stability: experimental
        '''
        result = self._values.get("additional_tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def auto_create_certificate(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Auto-create ACM certificate with DNS validation in us-east-1 region Requires hostedZoneId to be provided for DNS validation Cannot be used together with certificateArn Certificate will automatically be created in us-east-1 as required by CloudFront.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("auto_create_certificate")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def certificate_arn(self) -> typing.Optional[builtins.str]:
        '''(experimental) ARN of existing ACM certificate for the domain Certificate must be in us-east-1 region for CloudFront Cannot be used together with autoCreateCertificate.

        :default: - auto-create certificate if autoCreateCertificate is true

        :stability: experimental
        '''
        result = self._values.get("certificate_arn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def dev_server_base_path(self) -> typing.Optional[builtins.str]:
        '''(experimental) Base path for the application to be added to Nginx sites-available list.

        :default: - app

        :stability: experimental
        '''
        result = self._values.get("dev_server_base_path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def dev_server_port(self) -> typing.Optional[jsii.Number]:
        '''(experimental) Port for the DevServer.

        :default: - 8081

        :stability: experimental
        '''
        result = self._values.get("dev_server_port")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def domain_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) Custom domain name for the VS Code server When provided, creates a CloudFront distribution with this domain name and sets up Route53 A record pointing to the distribution.

        :default: - uses CloudFront default domain

        :stability: experimental
        '''
        result = self._values.get("domain_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def enable_auto_stop(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Enable automatic instance stop when idle Monitors CloudFront metrics and stops the EC2 instance after specified idle time.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("enable_auto_stop")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def home_folder(self) -> typing.Optional[builtins.str]:
        '''(experimental) Folder to open in VS Code server.

        :default: - /Workshop

        :stability: experimental
        '''
        result = self._values.get("home_folder")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def hosted_zone_id(self) -> typing.Optional[builtins.str]:
        '''(experimental) Route53 hosted zone ID for the domain Required when using autoCreateCertificate If not provided, will attempt to lookup hosted zone from domain name.

        :default: - auto-discover from domain name

        :stability: experimental
        '''
        result = self._values.get("hosted_zone_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def idle_check_interval_minutes(self) -> typing.Optional[jsii.Number]:
        '''(experimental) How often to check for idle activity (in minutes) Only applies when enableAutoStop is true.

        :default: 5 - Check every 5 minutes

        :stability: experimental
        '''
        result = self._values.get("idle_check_interval_minutes")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def idle_timeout_minutes(self) -> typing.Optional[jsii.Number]:
        '''(experimental) Minutes of inactivity before stopping the instance Only applies when enableAutoStop is true.

        :default: 30

        :stability: experimental
        '''
        result = self._values.get("idle_timeout_minutes")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def instance_class(
        self,
    ) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.InstanceClass]:
        '''(experimental) VSCode Server EC2 instance class.

        :default: - m7g

        :stability: experimental
        '''
        result = self._values.get("instance_class")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.InstanceClass], result)

    @builtins.property
    def instance_cpu_architecture(self) -> typing.Optional[LinuxArchitectureType]:
        '''(experimental) VSCode Server EC2 cpu architecture for the operating system.

        :default: - arm

        :stability: experimental
        '''
        result = self._values.get("instance_cpu_architecture")
        return typing.cast(typing.Optional[LinuxArchitectureType], result)

    @builtins.property
    def instance_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) VSCode Server EC2 instance name.

        :default: - VSCodeServer

        :stability: experimental
        '''
        result = self._values.get("instance_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def instance_operating_system(self) -> typing.Optional[LinuxFlavorType]:
        '''(experimental) VSCode Server EC2 operating system.

        :default: - Ubuntu-22

        :stability: experimental
        '''
        result = self._values.get("instance_operating_system")
        return typing.cast(typing.Optional[LinuxFlavorType], result)

    @builtins.property
    def instance_size(self) -> typing.Optional[_aws_cdk_aws_ec2_ceddda9d.InstanceSize]:
        '''(experimental) VSCode Server EC2 instance size.

        :default: - xlarge

        :stability: experimental
        '''
        result = self._values.get("instance_size")
        return typing.cast(typing.Optional[_aws_cdk_aws_ec2_ceddda9d.InstanceSize], result)

    @builtins.property
    def instance_volume_size(self) -> typing.Optional[jsii.Number]:
        '''(experimental) VSCode Server EC2 instance volume size in GB.

        :default: - 40

        :stability: experimental
        '''
        result = self._values.get("instance_volume_size")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def skip_status_checks(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Skip instance status checks in IdleMonitor When true, IdleMonitor will stop idle instances even if status checks haven't passed This is useful for integration tests where status check initialization time exceeds the test timeout limits.

        WARNING: For testing only - in production, you should wait for status checks
        to pass before stopping instances to avoid stopping unhealthy instances

        :default: false

        :stability: experimental
        '''
        result = self._values.get("skip_status_checks")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def vscode_password(self) -> typing.Optional[builtins.str]:
        '''(experimental) Password for VSCode Server.

        :default: - empty and will then be generated

        :stability: experimental
        '''
        result = self._values.get("vscode_password")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def vscode_user(self) -> typing.Optional[builtins.str]:
        '''(experimental) UserName for VSCode Server.

        :default: - participant

        :stability: experimental
        '''
        result = self._values.get("vscode_user")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VSCodeServerProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "IdleMonitor",
    "IdleMonitorProps",
    "LinuxArchitectureType",
    "LinuxFlavorType",
    "StatusCheckApi",
    "StatusCheckApiProps",
    "VSCodeServer",
    "VSCodeServerProps",
]

publication.publish()

def _typecheckingstub__20b577827aba935251db87d8d64ce79318aa5807c34b891715e4a171e2ae5b04(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    distribution: _aws_cdk_aws_cloudfront_ceddda9d.IDistribution,
    idle_timeout_minutes: jsii.Number,
    instance: _aws_cdk_aws_ec2_ceddda9d.IInstance,
    check_interval_minutes: typing.Optional[jsii.Number] = None,
    skip_status_checks: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dbe3d723d712645d045480dfd02714e4231593f8cb83f7d7c54a22b69d7930d9(
    *,
    distribution: _aws_cdk_aws_cloudfront_ceddda9d.IDistribution,
    idle_timeout_minutes: jsii.Number,
    instance: _aws_cdk_aws_ec2_ceddda9d.IInstance,
    check_interval_minutes: typing.Optional[jsii.Number] = None,
    skip_status_checks: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e7d6ff0408a4ed7de894609afb3872f4c204f0a40f6d03c29beea21657930c48(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    instance: _aws_cdk_aws_ec2_ceddda9d.IInstance,
    state_table: _aws_cdk_aws_dynamodb_ceddda9d.ITable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c79670a668f6fc2cfc6b40dad4ca1ee32a52c96f10f70d5cce6051bc058610f4(
    *,
    instance: _aws_cdk_aws_ec2_ceddda9d.IInstance,
    state_table: _aws_cdk_aws_dynamodb_ceddda9d.ITable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__13d98894e731d8d5e45fa4088dfd79af04a4cb66cead591188c4ba44d922873c(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    additional_instance_role_policies: typing.Optional[typing.Sequence[_aws_cdk_aws_iam_ceddda9d.PolicyStatement]] = None,
    additional_tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    auto_create_certificate: typing.Optional[builtins.bool] = None,
    certificate_arn: typing.Optional[builtins.str] = None,
    dev_server_base_path: typing.Optional[builtins.str] = None,
    dev_server_port: typing.Optional[jsii.Number] = None,
    domain_name: typing.Optional[builtins.str] = None,
    enable_auto_stop: typing.Optional[builtins.bool] = None,
    home_folder: typing.Optional[builtins.str] = None,
    hosted_zone_id: typing.Optional[builtins.str] = None,
    idle_check_interval_minutes: typing.Optional[jsii.Number] = None,
    idle_timeout_minutes: typing.Optional[jsii.Number] = None,
    instance_class: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.InstanceClass] = None,
    instance_cpu_architecture: typing.Optional[LinuxArchitectureType] = None,
    instance_name: typing.Optional[builtins.str] = None,
    instance_operating_system: typing.Optional[LinuxFlavorType] = None,
    instance_size: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.InstanceSize] = None,
    instance_volume_size: typing.Optional[jsii.Number] = None,
    skip_status_checks: typing.Optional[builtins.bool] = None,
    vscode_password: typing.Optional[builtins.str] = None,
    vscode_user: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2e462747a4e6316ff07a1ca12065fecb7b143031e2052b9b3ed692a4d9a458c7(
    *,
    additional_instance_role_policies: typing.Optional[typing.Sequence[_aws_cdk_aws_iam_ceddda9d.PolicyStatement]] = None,
    additional_tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    auto_create_certificate: typing.Optional[builtins.bool] = None,
    certificate_arn: typing.Optional[builtins.str] = None,
    dev_server_base_path: typing.Optional[builtins.str] = None,
    dev_server_port: typing.Optional[jsii.Number] = None,
    domain_name: typing.Optional[builtins.str] = None,
    enable_auto_stop: typing.Optional[builtins.bool] = None,
    home_folder: typing.Optional[builtins.str] = None,
    hosted_zone_id: typing.Optional[builtins.str] = None,
    idle_check_interval_minutes: typing.Optional[jsii.Number] = None,
    idle_timeout_minutes: typing.Optional[jsii.Number] = None,
    instance_class: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.InstanceClass] = None,
    instance_cpu_architecture: typing.Optional[LinuxArchitectureType] = None,
    instance_name: typing.Optional[builtins.str] = None,
    instance_operating_system: typing.Optional[LinuxFlavorType] = None,
    instance_size: typing.Optional[_aws_cdk_aws_ec2_ceddda9d.InstanceSize] = None,
    instance_volume_size: typing.Optional[jsii.Number] = None,
    skip_status_checks: typing.Optional[builtins.bool] = None,
    vscode_password: typing.Optional[builtins.str] = None,
    vscode_user: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
