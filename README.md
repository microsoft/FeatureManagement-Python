# Feature Management client library for Python

Feature Management is a library for enabling/disabling features at runtime. Developers can use feature flags in simple use cases like conditional statement to more advanced scenarios like conditionally adding routes.

## Getting started

### Install the package

Install the Azure Feature Management client library for Python with [pip][pip]:

```bash
pip install microsoft-feature-management
```

### Prerequisites

* Python 3.7 or later is required to use this package.

## Examples

You can use feature flags from the Azure App Configuration service, a json file, or a dictionary.

#### Use feature flags from Azure App Configuration

```python
from microsoft.feature.management import FeatureManager
from azure.appconfiguration.provider import load
from azure.identity import DefaultAzureCredential
import os

endpoint = os.environ.get("APPCONFIGURATION_ENDPOINT_STRING")

selects = {SettingSelector(key_filter=".appconfig.featureflag*")}

config = load(endpoint=endpoint, credential=DefaultAzureCredential(), selects=selects)

feature_manager = FeatureManager(config)

# Is always true
print("Alpha is ", feature_manager.is_enabled("Alpha"))
```

NOTE: If no setting selector is set then feature flags with no label are loaded.

### Use feature flags from a json file

```python
from microsoft.feature.management import FeatureManager
import json
import os
import sys

script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))

f = open(script_directory + "/my_json_file.json", "r")

feature_flags = json.load(f)

feature_manager = FeatureManager(feature_flags)

# Is always true
print("Alpha is ", feature_manager.is_enabled("Alpha"))
```

### Use feature flags from a dictionary

```python
from microsoft.feature.management import FeatureManager

feature_flags = {
    "FeatureFlags": [
        {"id": "Alpha", "enabled": "true"},
    ]
}

feature_manager = FeatureManager(feature_flags)

# Is always true
print("Alpha is ", feature_manager.is_enabled("Alpha"))
```

## Key concepts

### FeatureManager

The `FeatureManager` is the main entry point for using feature flags. It is initialized with a dictionary of feature flags, and optional feature filters. The `FeatureManager` can then be used to check if a feature is enabled or disabled.

### Feature Flags

Feature Flags are objects that define how Feature Management enables/disables a feature. It contains an `id` and `enabled` property. The `id` is a string that uniquely identifies the feature flag. The `enabled` property is a boolean that indicates if the feature flag is enabled or disabled. The `conditions` object contains a property `client_filters` which is a list of `FeatureFilter` objects that are used to determine if the feature flag is enabled or disabled.

```json
{
    "id": "Alpha",
    "enabled": "true",
    "conditions": {
        "client_filters": [
            {
                "name": "MyFilter",
                "parameters": {
                    ...
                },
            }
        ]
    },
}
```

This object is passed into the `FeatureManager` when it is initialized.

### Feature Filters

A `FeatureFilter` is a class that can be used to enable/disable feature flags. Two built-in feature filters are provided:

- `Microsoft.TimeWindowFilter` - Enables a feature flag based on a time window.
- `Microsoft.TargetingFilter` - Enables a feature flag based on a list of users, groups, or rollout percentages.

#### Time Window Filter

The Time Window Filter enables a feature flag based on a time window. It has two parameters:

- `Start` - The start time of the time window.
- `End` - The end time of the time window.

```json
{
    "name": "Microsoft.TimeWindowFilter",
    "parameters": {
        "Start": "2020-01-01T00:00:00Z",
        "End": "2020-12-31T00:00:00Z"
    }
}
```

Both parameters are optional, but at least one is required. The time window filter is enabled after the start time and before the end time. If the start time is not specified, it is enabled immediately. If the end time is not specified, it will remain enabled after the start time.

#### Targeting Filter

Targeting is a feature management strategy that enables developers to progressively roll out new features to their user base. The strategy is built on the concept of targeting a set of users known as the target audience. An audience is made up of specific users, groups, excluded users/groups, and a designated percentage of the entire user base. The groups that are included in the audience can be broken down further into percentages of their total members.

The following steps demonstrate an example of a progressive rollout for a new 'Beta' feature:

1. Individual users Jeff and Alicia are granted access to the Beta
1. Another user, Mark, asks to opt-in and is included.
1. Twenty percent of a group known as "Ring1" users are included in the Beta.
1. The number of "Ring1" users included in the beta is bumped up to 100 percent.
1. Five percent of the user base is included in the beta.
1. The rollout percentage is bumped up to 100 percent and the feature is completely rolled out.

This strategy for rolling out a feature is built in to the library through the included Microsoft.Targeting feature filter.

##### Defining a Targeting Feature Filter

The Targeting Filter provides the capability to enable a feature for a target audience. The filter parameters include an `Audience` object which describes users, groups, excluded users/groups, and a default percentage of the user base that should have access to the feature. The `Audience` object contains the following fields:

- `Users` - A list of users that the feature flag is enabled for.
- `Groups` - A list of groups that the feature flag is enabled for and a rollout percentage for each group.
- `DefaultRolloutPercentage` - A percentage value that the feature flag is enabled for.
- `Exclusion` - An object that contains a list of users and groups that the feature flag is disabled for.

```json
{
    "name": "Microsoft.TargetingFilter",
    "parameters": {
        "Audience": {
            "Users": ["user1", "user2"],
            "Groups": [
                {
                    "Name": "group1",
                    "RolloutPercentage": 100
                }
            ],
            "DefaultRolloutPercentage": 50,
            "Exclusion": {
                "Users": ["user3"],
                "Groups": ["group2"]
            }
        }
    }
}
```

The `Users` field is a list of strings that represent the users that the feature flag is enabled for. The `Groups` field is a list of objects that represent the groups that the feature flag is enabled for. The `Name` field is a string that represents the name of the group. The `RolloutPercentage` field is a number between 0 and 100 that represents the percentage of users in the group that the feature flag is enabled for. The `DefaultRolloutPercentage` field is a number between 0 and 100 that represents the percentage of users that the feature flag is enabled for if they are not in any of the groups. The `Exclusions` field is an object that contains a list of users and groups that the feature flag is disabled for. The `Users` field is a list of strings that represent the users that the feature flag is disabled for. The `Groups` field is a list of strings that represent the groups that the feature flag is disabled for.

#### Custom Filters

You can also create your own feature filters by implementing the `FeatureFilter` interface.

```python
class CustomFilter(FeatureFilter):
    def evaluate(self, context, **kwargs):
        ...
        return True
```

The `evaluate` method is called when checking if a feature flag is enabled. The `context` parameter contains information about the feature filter from the `parameters` field of the feature filter. Any additional parameters can be passed in as keyword arguments when calling `is_enabled`.

You can then pass your custom filter into the `FeatureManager` when it is initialized.

```json
{
    "name": "MyCustomFilter",
    "parameters": {
        ...
    }
}
```

`parameters` takes any additional parameters that are needed for the feature filter as a dictionary. These parameters are passed into the `evaluate` method.

## Troubleshooting

## Next steps

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
