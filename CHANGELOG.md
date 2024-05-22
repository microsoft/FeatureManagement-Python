# Release History

## 1.0.0b1 (05/22/2024)

New Feature Management library.

Provides the ability to manage feature flags in a project. Enables:

* Loading of feature flags from a file, see: https://github.com/Azure/AppConfiguration/blob/main/docs/FeatureManagement/FeatureManagement.v2.0.0.schema.json
* Loading of feature flags from Azure App Configuration.
* Checking if a feature is enabled.
* Default feature filters: TimeWindowFilter, TargetingFilter.
* Custom feature filters.
