# Microsoft Feature Management for Python

[![FeatureManagement](https://img.shields.io/pypi/v/FeatureManagement?label=FeatureManagement)](https://pypi.org/project/FeatureManagement/)

Feature management provides a way to develop and expose application functionality based on features. Many applications have special requirements when a new feature is developed such as when the feature should be enabled and under what conditions. This library provides a way to define these relationships, and also integrates into common Python code patterns to make exposing these features possible.

## Get Started

[Quickstart](https://learn.microsoft.com/azure/azure-app-configuration/quickstart-feature-flag-python): A quickstart guide is available to learn how to integrate feature flags from Azure App Configuration into your Python applications.

[API Reference](https://microsoft.github.io/FeatureManagement-Python/): This API reference details the API surface of the libraries contained within this repository.

## Examples

* [Python Application](https://github.com/microsoft/FeatureManagement-Python/blob/main/samples/feature_flag_sample.py)
* [Python Application with Azure App Configuration](https://github.com/microsoft/FeatureManagement-Python/blob/main/samples/feature_flag_with_azure_app_configuration_sample.py)
* [Django Application](https://github.com/Azure/AppConfiguration/tree/main/examples/Python/python-django-webapp-sample)
* [Flask Application](https://github.com/Azure/AppConfiguration/tree/main/examples/Python/python-flask-webapp-sample)

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
"enabled_for": [ 
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
