# Microsoft Feature Management for Python

Feature Management is a library for enabling/disabling features at runtime. Developers can use feature flags in simple use cases like conditional statement to more advanced scenarios like conditionally adding routes.

## Getting started

### Prerequisites

* Python 3.7 or later is required to use this package.

### Install the package

Install the Python feature management client library for Python with [pip][pip]:

```bash
pip install microsoft-featuremanagement
```

## Usage

You can use feature flags from the Azure App Configuration service, a json file, or a dictionary.

### Use feature flags from Azure App Configuration

```python
from featuremanagement import FeatureManager
from azure.appconfiguration.provider import load
from azure.identity import DefaultAzureCredential
import os

endpoint = os.environ.get("APPCONFIGURATION_ENDPOINT_STRING")

# If no setting selector is set then feature flags with no label are loaded.
selects = {SettingSelector(key_filter=".appconfig.featureflag*")}

config = load(endpoint=endpoint, credential=DefaultAzureCredential(), selects=selects)

feature_manager = FeatureManager(config)

# Prints the value of the feature flag Alpha
print("Alpha is ", feature_manager.is_enabled("Alpha"))
```

### Use feature flags from a json file

A Json file with the following format can be used to load feature flags.

```json
{
    "feature_management": {
        "feature_flags": [
            {
                "id": "Alpha",
                "description": "",
                "enabled": "true",
                "conditions": {
                    "client_filters": []
                }
            }
        ]
    }
 }
```

Load feature flags from a json file.

```python
from featuremanagement import FeatureManager
import json
import os
import sys

script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))

f = open(script_directory + "/my_json_file.json", "r")

feature_flags = json.load(f)

feature_manager = FeatureManager(feature_flags)

# Returns the value of Alpha, based on the result of the feature filter
print("Alpha is ", feature_manager.is_enabled("Alpha"))
```

### Use feature flags from a dictionary

```python
from featuremanagement import FeatureManager

feature_flags = {
    "feature_management": {
        "feature_flags": [
            {
                "id": "Alpha",
                "description": "",
                "enabled": "true",
                "conditions": {
                    "client_filters": []
                }
            }
        ]
    }
}

feature_manager = FeatureManager(feature_flags)

# Is always true
print("Alpha is ", feature_manager.is_enabled("Alpha"))
```

## Key concepts

### FeatureManager

The `FeatureManager` is the main entry point for using feature flags. It is initialized with a dictionary of feature flags, and optional feature filters. The `FeatureManager` can then be used to check if a feature is enabled or disabled.

### Feature Flags

Feature Flags are objects that define how Feature Management enables/disables a feature. It contains an `id` and `enabled` property. The `id` is a string that uniquely identifies the feature flag. The `enabled` property is a boolean that indicates if the feature flag is enabled or disabled. The `conditions` object contains a property `client_filters` which is a list of `FeatureFilter` objects that are used to determine if the feature flag is enabled or disabled. The Feature Filters only run if the feature flag is enabled.

The full schema for a feature Flag can be found [here](https://github.com/Azure/AppConfiguration/blob/main/docs/FeatureManagement/FeatureFlag.v1.1.0.schema.json).

```javascript
{
    "id": "Alpha",
    "enabled": "true",
    "conditions": {
        "client_filters": [
            {
                "name": "MyFilter",
                "parameters": {
                    ...
                }
            }
        ]
    }
}
```

This object is passed into the `FeatureManager` when it is initialized.

### Feature Filters

Feature filters enable dynamic evaluation of feature flags. The Python feature management library includes two built-in filters:

- `Microsoft.TimeWindow` - Enables a feature flag based on a time window.
- `Microsoft.Targeting` - Enables a feature flag based on a list of users, groups, or rollout percentages.

#### Time Window Filter

The Time Window Filter enables a feature flag based on a time window. It has two parameters:

- `Start` - The start time of the time window.
- `End` - The end time of the time window.

```json
{
    "name": "Microsoft.TimeWindow",
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
  - `Name` - The name of the group.
  - `RolloutPercentage` - A percentage value that the feature flag is enabled for in the given group.
- `DefaultRolloutPercentage` - A percentage value that the feature flag is enabled for.
- `Exclusion` - An object that contains a list of users and groups that the feature flag is disabled for.
  - `Users` - A list of users that the feature flag is disabled for.
  - `Groups` - A list of groups that the feature flag is disabled for.

```json
{
    "name": "Microsoft.Targeting",
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

##### Using Targeting Feature Filter

You can provide the current user info through `kwargs` when calling `isEnabled`.

```python
# Returns true, because user1 is in the Users list
feature_manager.is_enabled("Beta", user="user1", groups=["group1"])

# Returns false, because group2 is in the Exclusion.Groups list
feature_manager.is_enabled("Beta", user="user1", groups=["group2"])

# Has a 50% chance of returning true, but will be conisistent for the same user
feature_manager.is_enabled("Beta", user="user4")
```

#### Custom Filters

You can also create your own feature filters by implementing the `FeatureFilter` interface.

```python
class MyCustomFilter(FeatureFilter):

    def evaluate(self, context, **kwargs):
        ...
        return True
```

They can then be passed into the `FeatureManager` when it is initialized. By default, the name of a feature filter is the name of the class. You can override this by setting a class attribute `alias` to the modified class name.

```python

feature_manager = FeatureManager(feature_flags, feature_filters={MyCustomFilter(), MyOtherFilter()})
```

The `evaluate` method is called when checking if a feature flag is enabled. The `context` parameter contains information about the feature filter from the `parameters` field of the feature filter. Any additional parameters can be passed in as keyword arguments when calling `is_enabled`.

```javascript
{
    "name": "CustomFilter",
    "parameters": {
        ...
    }
}
```

You can modify the name of a feature flag by using the `@FeatureFilter.alias` decorator. The alias overrides the name of the feature filter and needs to match the name of the feature filter in the feature flag json.

```python
@FeatureFilter.alias("AliasFilter")
class MyCustomFilter(FeatureFilter):
    ...
```

### Feature Variants

When new features are added to an application, there may come a time when a feature has multiple different proposed design options. A common solution for deciding on a design is some form of A/B testing, which involves providing a different version of the feature to different segments of the user base and choosing a version based on user interaction. In this library, this functionality is enabled by representing different configurations of a feature with variants.

Variants enable a feature flag to become more than a simple on/off flag. A variant represents a value of a feature flag that can be a string, a number, a boolean, or even a configuration object. A feature flag that declares variants should define under what circumstances each variant should be used, which is covered in greater detail in the [Allocating Variants](#allocating-variants) section.

```python
class Variant():

    @property
    def name(self):

    @property
    def configuration(self):
```

#### Getting Variants

For each feature, a variant can be retrieved using `FeatureManager`'s `get_variant` method. The method returns a `Variant` object that contains the name and configuration of the variant. Once a variant is retrieved, the configuration of a variant can be used directly as JSON from the variant's `configuration` property.

```python
feature_manager = FeatureManager(feature_flags)

variant = feature_manager.get_variant("FeatureU")

my_configuration = variant.configuration

variant = feature_manager.get_variant("FeatureV")

sub_configuration = variant.configuration["json_key"]
```

#### Defining Variants

Each variant has two properties: a name and a configuration. The name is used to refer to a specific variant, and the configuration is the value of that variant. The configuration can be set using either the `configuration_reference` or `configuration_value` properties. `configuration_reference` is a string that references a configuration, this configuration is a key inside of the configuration object passed into `FeatureManager`. `configuration_value` is an inline configuration that can be a string, number, boolean, or json object. If both are specified, `configuration_value` is used. If neither are specified, the returned variant's `configuration` property will be `None`.

A list of all possible variants is defined for each feature under the Variants property.

```json
{
    "feature_management": {
        "feature_flags": [
            {
                "id": "FeatureU",
                "variants": [
                    {
                        "name": "VariantA",
                        "configuration_reference": "config1"
                    },
                    {
                        "name": "VariantB",
                        "configuration_value": {
                            "name": "value"
                        }
                    }
                ]
            }
        ]
    }
}
```

#### Allocating Variants

The process of allocating a feature's variants is determined by the `allocation` property of the feature.

```json
"allocation": { 
    "default_when_enabled": "Small", 
    "default_when_disabled": "Small",  
    "user": [ 
        { 
            "variant": "Big", 
            "users": [ 
                "Marsha" 
            ] 
        } 
    ], 
    "group": [ 
        { 
            "variant": "Big", 
            "groups": [ 
                "Ring1" 
            ] 
        } 
    ],
    "percentile": [ 
        { 
            "variant": "Big", 
            "from": 0, 
            "to": 10 
        } 
    ], 
    "seed": "13973240" 
},
"variants": [
    { 
        "name": "Big", 
        "configuration_reference": "ShoppingCart:Big" 
    },  
    { 
        "name": "Small", 
        "configuration_value": "300px"
    } 
]
```

The `allocation` setting of a feature flag has the following properties:

| Property | Description |
| ---------------- | ---------------- |
| `default_when_disabled` | Specifies which variant should be used when a variant is requested while the feature is considered disabled. |
| `default_when_enabled` | Specifies which variant should be used when a variant is requested while the feature is considered enabled and no other variant was assigned to the user. |
| `user` | Specifies a variant and a list of users to whom that variant should be assigned. |
| `group` | Specifies a variant and a list of groups the current user has to be in for that variant to be assigned. |
| `percentile` | Specifies a variant and a percentage range the user's calculated percentage has to fit into for that variant to be assigned. |
| `seed` | The value which percentage calculations for `percentile` are based on. The percentage calculation for a specific user will be the same across all features if the same `seed` value is used. If no `seed` is specified, then a default seed is created based on the feature name. |

In the above example, if the feature is not enabled, the feature manager will assign the variant marked as `default_when_disabled` to the current user, which is `Small` in this case.

If the feature is enabled, the feature manager will check the `user`, `group`, and `percentile` allocations in that order to assign a variant. For this particular example, if the user being evaluated is named `Marsha`, in the group named `Ring1`, or the user happens to fall between the 0 and 10th percentile, then the specified variant is assigned to the user. In this case, all of these would return the `Big` variant. If none of these allocations match, the user is assigned the `default_when_enabled` variant, which is `Small`.

Allocation logic is similar to the [Microsoft.Targeting](#microsoft-targeting) feature filter, but there are some parameters that are present in targeting that aren't in allocation, and vice versa. The outcomes of targeting and allocation are not related.

### Overriding Enabled State with a Variant

You can use variants to override the enabled state of a feature flag. This gives variants an opportunity to extend the evaluation of a feature flag. If a caller is checking whether a flag that has variants is enabled, the feature manager will check if the variant assigned to the current user is set up to override the result. This is done using the optional variant property `status_override`. By default, this property is set to `None`, which means the variant doesn't affect whether the flag is considered enabled or disabled. Setting `status_override` to `Enabled` allows the variant, when chosen, to override a flag to be enabled. Setting `status_override` to `Disabled` provides the opposite functionality, therefore disabling the flag when the variant is chosen.

If you are using a feature flag with binary variants, the `status_override` property can be very helpful. It allows you to continue using `is_enabled` in your application, all while benefiting from the new features that come with variants, such as percentile allocation and seed.

```json
"allocation": {
    "percentile": [{
        "variant": "On",
        "from": 10,
        "to": 20
    }],
    "default_when_enabled":  "Off",
    "seed": "Enhanced-Feature-Group"
},
"variants": [
    { 
        "name": "On"
    },
    { 
        "name": "Off",
        "status_override": "Disabled"
    }    
],
"enabled_ror": [ 
    { 
        "name": "AlwaysOn" 
    } 
] 
```

In the above example, the feature is enabled by the `AlwaysOn` filter. If the current user is in the calculated percentile range of 10 to 20, then the `On` variant is returned. Otherwise, the `Off` variant is returned and because `status_override` is equal to `Disabled`, the feature will now be considered disabled.

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
