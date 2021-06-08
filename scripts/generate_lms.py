from collections import defaultdict
import sys
import os
import logging
from generator_utils import load_config, common_args, update_model


logger = logging.getLogger(__name__)


def create_organizations(config):
    from common.djangoapps.util.organizations_helpers import add_organization

    for code in config.get_organization_codes():
        org = {
            'short_name': code,
            'name': config.get_organization_name(code)
        }
        logger.info('Creating Organization for {} - {}'.format(code, org))
        add_organization(org)


def create_sites(config):
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
    from openedx.core.djangoapps.site_configuration.models import SiteConfiguration

    for code in config.get_microsite_codes():
        context = config.get_context(code)
        site_configuration = {
            'site': sites[code],
            'enabled': True,
            'site_values': {
                'PLATFORM_NAME': context['name'],
                'Platform_name': context['name'],
                'LMS_ROOT_URL': context['lms_url'],
                'LMS_BASE': context['lms_url'],
                'ECOMMERCE_PUBLIC_URL_ROOT': context['ecommerce_url'],
                'COURSE_CATALOG_API_URL': context['discovery_api_url'],
            }
        }
        site_configuration = config.apply_overrides(code, 'lms', SiteConfiguration, site_configuration)
        logger.info('Creating SiteConfiguration for {} - {}'.format(code, site_configuration))
        sc, created = SiteConfiguration.objects.get_or_create(site=site_configuration['site'], defaults=site_configuration)
        if not created:
            update_model(sc, **site_configuration)

def run(config_file_path, settings_module):

    sys.path.append('/edx/app/edxapp/edx-platform')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)  # for production use lms.envs.production

    import django
    django.setup()

    config = load_config(config_file_path)

    create_organizations(config)
    sites = create_sites(config)
    create_site_configurations(config, sites)


if __name__ == '__main__':
    parser = common_args()
    cli_args = parser.parse_args()
    run(cli_args.ConfigFilePath, cli_args.settings)
