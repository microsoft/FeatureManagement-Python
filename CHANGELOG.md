# Release History

## 2.0.0b3 (11/14/2024)

* Fixes a bug where no allocation reason is set if a user is allocated to exactly 100.
* Fixes a bug where VariantAssignmentPercentage wasn't correct for default when enabled.

## 2.0.0b2 (10/11/2024)

* Adds VariantAssignmentPercentage, DefaultWhenEnabled, and AllocationId to telemetry.
* Allocation seed value is now None by default, and only defaults to `allocation\n<feature.id>` when assigning variants.

## 2.0.0b1 (09/10/2024)

* Adds support for Feature Variants.
* Adds support for Telemetry.

## 1.0.0 (06/26/2024)

Updated version to 1.0.0.

## 1.0.0b1 (05/22/2024)

New Feature Management library.

Provides the ability to manage feature flags in a project. Enables:

* Loading of feature flags from a file, see: https://github.com/Azure/AppConfiguration/blob/main/docs/FeatureManagement/FeatureManagement.v2.0.0.schema.json
* Loading of feature flags from Azure App Configuration.
* Checking if a feature is enabled.
* Default feature filters: TimeWindowFilter, TargetingFilter.
* Custom feature filters.
