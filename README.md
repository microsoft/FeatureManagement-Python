# Microsoft Feature Management for Python

[![FeatureManagement](https://img.shields.io/pypi/v/FeatureManagement?label=FeatureManagement)](https://pypi.org/project/FeatureManagement/)

Feature management provides a way to develop and expose application functionality based on features. Many applications have special requirements when a new feature is developed such as when the feature should be enabled and under what conditions. This library provides a way to define these relationships, and also integrates into common Python code patterns to make exposing these features possible.

## Get Started

[Quickstart](https://learn.microsoft.com/azure/azure-app-configuration/quickstart-feature-flag-python): A quickstart guide is available to learn how to integrate feature flags from Azure App Configuration into your Python applications.

[API Reference](https://microsoft.github.io/FeatureManagement-Python/): This API reference details the API surface of the libraries contained within this repository.

## Examples

* [Python Application](https://github.com/microsoft/FeatureManagement-Python/blob/main/samples/feature_flag_sample.py)
* [Python Application with Feature Variants](https://github.com/microsoft/FeatureManagement-Python/blob/main/samples/feature_variant_sample.py)
* [Python Application with Azure App Configuration](https://github.com/microsoft/FeatureManagement-Python/blob/main/samples/feature_flag_with_azure_app_configuration_sample.py)
* [Django Application](https://github.com/Azure/AppConfiguration/tree/main/examples/Python/python-django-webapp-sample)
* [Flask Application](https://github.com/Azure/AppConfiguration/tree/main/examples/Python/python-flask-webapp-sample)

## Contributing

### Release documentation

The [release documentation workflow](https://github.com/microsoft/FeatureManagement-Python/actions/workflows/docs.yml)
builds the verified `v2.2.0` source, not the current `main` API.
The initial release is selected once through the workflow's `RELEASE_TAG` setting.
The builder resolves that tag's commit, derives its version, and checks that the imported package version agrees;
it contains no release-specific version or commit constants.
Pull requests and relevant changes merged into `main` build and validate the site without deploying it.
The downloadable `github-pages` artifact contains the complete site, including `/2.2.0/`, `/latest/`,
and redirects for existing `/html/` links.

To build locally on Windows, use a separate release checkout and virtual environment:

```powershell
git worktree add --detach ..\FeatureManagement-Python-2.2.0 v2.2.0
py -3.14 -m venv ..\FeatureManagement-Python-2.2.0\.venv
& ..\FeatureManagement-Python-2.2.0\.venv\Scripts\Activate.ps1
python -m pip install -r docs\requirements.txt ..\FeatureManagement-Python-2.2.0
python scripts\build_release_docs.py --source ..\FeatureManagement-Python-2.2.0 --tag v2.2.0
Start-Process docs\_build\site\index.html
```

Reuse an existing clean release checkout instead of adding it again.
The builder rejects the wrong commit or tracked release edits, validates local links and API anchors,
and replaces the local site only after a successful build. Generated pages are not committed.
Required API anchors come from methods declared by the tagged feature managers, not a version-independent API list.
Only stable release tags can become `/latest/`; prerelease and development tags are rejected.
Rendering fixes apply only during the build; the historical library source remains unchanged.
SDK documentation follows the [Azure SDK Python Design Guidelines](https://azure.github.io/azure-sdk/python_design.html).

Deployment is opt-in. After merging this workflow and configuring Pages to use **GitHub Actions**, allow `main`
in the `github-pages` environment. Run **Release documentation** manually from `main` and enable its `deploy` input.
No new secret is required, and PR builds never receive Pages deployment permissions.
Keep `gh-pages` unchanged as a fallback; rollback consists of restoring its `/docs` folder as the Pages source
and allowing `gh-pages` in the deployment environment.

The bootstrap site contains one configured release. Retaining multiple versions, validating older documentation
builds, and registration of future releases are separate follow-up work.

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
