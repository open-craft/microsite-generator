from collections import defaultdict
import sys
import os
import logging
from const import LMS_ROOT_DIR
from generator_utils import load_config, common_args, update_model, deep_merge, write_generated_values


logger = logging.getLogger(__name__)


def create_organizations(config):
    """
    Create Organizations in LMS.

    Args:
        config (Config)
    """
    from common.djangoapps.util.organizations_helpers import add_organization

    for code in config.get_organization_codes():
        org = {
            'short_name': code,
            'name': config.get_organization_name(code)
        }
        logger.info('Creating Organization for {} - {}'.format(code, org))
        add_organization(org)


def create_sites(config):
    """
    Create custom sites in LMS.

    Args:
        config (Config)
    Returns:
        sites (dict): A mapping of custom site code and site instance
    """
    from django.contrib.sites.models import Site

    sites = {}
    for code in config.get_microsite_codes():
        context = config.get_context(code)
        site = {
            'domain': context['lms_domain'],
            'name': context['lms_domain']
        }
        site = config.apply_overrides(code, 'lms', Site, site)
        logger.info('Creating site for {} - {}'.format(code, site))
        site, _ = Site.objects.get_or_create(domain=site['domain'], defaults=site)
        sites[code] = site
    return sites


def create_site_configurations(config, sites):
    """
    Create SiteConfiguration for each custom sites in LMS.

    Args:
        config (Config)
        sites (dict)
    """
    from openedx.core.djangoapps.site_configuration.models import SiteConfiguration

    for code in config.get_microsite_codes():
        context = config.get_context(code)
        site_configuration = {
            'site': sites[code],
            'enabled': True,
            'site_values': {
                'PLATFORM_NAME': context['name'],
                'Platform_name': context['name'],
                'SITE_NAME': context['lms_domain'],
                'LMS_ROOT_URL': context['lms_url'],
                'LMS_BASE': context['lms_url'],
                'PREVIEW_LMS_BASE': 'preview.{}'.format(context['lms_domain']),
                'ECOMMERCE_PUBLIC_URL_ROOT': context['ecommerce_url'],
                'COURSE_CATALOG_API_URL': context['discovery_api_url'],
            }
        }
        site_configuration = config.apply_overrides(code, 'lms', SiteConfiguration, site_configuration)
        logger.info('Creating SiteConfiguration for {} - {}'.format(code, site_configuration))
        site_config_obj, created = SiteConfiguration.objects.get_or_create(site=site_configuration['site'], defaults=site_configuration)
        if not created:
            # while regenerating, we want to keep whatever value has been edited from django admin intact!
            site_values = deep_merge(
                site_config_obj.site_values, site_configuration['site_values']
            )
            site_configuration['site_values'] = site_values
            update_model(site_config_obj, **site_configuration)


def add_ecommerce_redirect_urls(config):
    """
    Add eCommerce Oauth redirect url for each custom sites in LMS.

    Args:
        config (Config)
    """
    from oauth2_provider.models import Application
    from django.contrib.auth import get_user_model

    redirect_uris = []
    for code in config.get_microsite_codes():
        context = config.get_context(code)
        redirect_uris.append('{}/complete/edx-oauth2/'.format(context['ecommerce_url']))

    ecommerce_app, created = Application.objects.get_or_create(name=config.oauth['ecommerce_sso_client'])

    if created:
        ecommerce_app.client_type = 'confidential'
        ecommerce_app.authorization_grant_type = 'authorization-code'
        ecommerce_app.user = get_user_model().objects.get(username='ecommerce_worker')
        ecommerce_app.skip_authorization = True
        ecommerce_app.save()

    if ecommerce_app.redirect_uris:
        redirect_uris += ecommerce_app.redirect_uris.split()

    redirect_uris_str = ' '.join(set(redirect_uris))
    logger.info('Adding ecommerce to redirect url {}'.format(redirect_uris_str))
    ecommerce_app.redirect_uris = redirect_uris_str
    ecommerce_app.save()


def share_sso_credentials(config):
    """
    Writes OAuth client credentials in the shared generated config file.
    """
    from oauth2_provider.models import Application

    ecommerce_sso = Application.objects.get(name=config.oauth['ecommerce_sso_client'])

    write_generated_values({
        'SOCIAL_AUTH_EDX_OAUTH2_KEY': ecommerce_sso.client_id,
        'SOCIAL_AUTH_EDX_OAUTH2_SECRET': ecommerce_sso.client_secret,
    })


def run(config_file_path, settings_module):
    """
    Given a configuration file path and django settings module,
    load eCommerce service django app and generate custom sites.

    Args:
        config_file_path (str)
        settings_module (str)
    """
    sys.path.append(LMS_ROOT_DIR)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)  # for production use lms.envs.production

    import django
    django.setup()

    config = load_config(config_file_path)

    create_organizations(config)
    sites = create_sites(config)
    create_site_configurations(config, sites)
    add_ecommerce_redirect_urls(config)
    share_sso_credentials(config)


if __name__ == '__main__':
    parser = common_args()
    cli_args = parser.parse_args()
    run(cli_args.ConfigFilePath, cli_args.settings)
