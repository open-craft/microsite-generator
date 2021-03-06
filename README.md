# microsite-generator

Generates MicroSites for an edX installation.

# Installation


- **Local Devstack**: Clone this repo in `src` directory
- **Production**: Clone this repo in the home directory of an appserver
```
git clone https://github.com/open-craft/microsite-generator.git
```

# Usage

- Copy `config/sample.yaml` to `config/config.yaml`.
- Edit `config/config.yaml` to match your needs. `config/sample.yaml` is a good starting point to check, which things usually needs to be configured.
- Check `Makefile` for available commands.
```
make help

help:     Show help.

run:  Generate microsite configuration for all services
run-lms:  Generate microsite configuration in LMS
run-discovery:  Generate microsite configuration in Discovery
run-ecommerce:   Generate microsite configuration in eCommerce

dev.run-lms:     Devstack - Generate microsite configuration in LMS
dev.run-discovery:   Devstack - Generate microsite configuration in Discovery
dev.run-ecommerce:   Devstack - Generate microsite configuration in eCommerce
```

**Note**: If you are using a docker devstack, you should use ``dev.*`` variants. And only run these commands in correct service containers. For example `dev.run-lms` in `LMS` container only.
# Structure of config file

`config/config.yaml` file contains following features -

- `main_domain`: The base domain. Each microsite will be set as subdomain of this domain.
- `oauth`: OAuth applications in LMS
    - `ecommerce_sso_client`: eCommerce SSO Client name, defaults to `custom-sites-ecommerce-sso`. It is intentionally a different one than the one found by default in an Open edX installation, since the default one resets on every deployment. But we need to have redirect URIs for dynamic custom sites. Generator will create this client autometically if not found.
- `site_for_each_organization`: Set this to `true` if each organization will have a microsite. Then the script will automatically copy `organizations` as `microsites`.
- `organizations`: A dictionary containing organization related info
    ```yaml
    organizations:
        short_code:
            name: Name of the organization
    ```
- `microsites`: A dictionary containing microsite related info -
    ```yaml
    microsites:
        sub_domain:
            name: Name of the microsite
            context_overrides: {}
            overrides: {}
    ```

### Overrides
To override values of fields in microsite configuration, we have the following options -

#### Context Override

Context is a dictionary that gets generated for each microsite. It contains -

```python
context = {
    'name': microsite['name'],
    'code': code,
    'main_domain': self.main_domain,
    'lms_domain': lms_domain,
    'lms_url': 'https://{}'.format(lms_domain),

    'discovery_domain': discovery_domain,
    'discovery_url': 'https://{}'.format(discovery_domain),
    'discovery_api_url': 'https://{}/api/v1/'.format(discovery_domain),

    'ecommerce_domain': ecommerce_domain,
    'ecommerce_url': 'https://{}'.format(ecommerce_domain),

    'studio_domain': studio_domain,
    'studio_url': 'https://{}'.format(studio_domain)
}
```

This items can be overriden for a specific site by setting `context_override` in specific microsite in `microsites`. For example, lets override `ecommerce_domain` of `example` site -

```yaml
microsites:
    example:
        context_overrides:
            ecommerce_domain: ecommerce-site.domain

```

#### Overrides

We might also want to set some custom value for some site configuration. `overrides` helps us do that. The structure of `overrides` -
```
microsites:
    subdomain:
       overrides:
            service:
                model_path:
                    field_name: value
```

Let's say we want to set `arabic_platform_name` for some site -

```yaml
microsites:
    example:
       overrides:
            lms:
                openedx.core.djangoapps.site_configuration.models.SiteConfiguration:
                    site_values:
                        arabic_platform_name: Some arabic string
```

### Global overrides
So far we've seen site specific overrides. We can have override for all site using global overrides. Global overrides are exactly same as site overrides, just the `subdomain` is marked as `$`. For example -
```yaml
microsites:
    $:
       overrides:
            lms:
                openedx.core.djangoapps.site_configuration.models.SiteConfiguration:
                    site_values:
                        arabic_platform_name: Some arabic string
```

All overrides under `$` site will be applied to all microsites.
