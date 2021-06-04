from collections import defaultdict
import sys
import os
import logging
from generator_utils import load_config, common_args


logger = logging.getLogger(__name__)


def create_organizations(config):
    from common.djangoapps.util.organizations_helpers import add_organization

    for code in config.get_microsite_codes():
        org = {
            'short_name': code,
            'name': config.get_name(code)
        }
        logger.info('Creating Organization for {} - {}'.format(code, org))
        add_organization(org)


def create_sites(config):
    from django.contrib.sites.models import Site

    sites = {}
    for code in config.get_microsite_codes():
        site = {
            'domain': config.get_lms_domain(code),
            'name': config.get_lms_domain(code)
        }
        logger.info('Creating site for {} - {}'.format(code, site))
        site, _ = Site.objects.get_or_create(domain=site['domain'], defaults=site)
        sites[code] = site
    return sites

def create_site_configurations(config, sites):
    from openedx.core.djangoapps.site_configuration.models import SiteConfiguration

    for code in config.get_microsite_codes():
        site_configuration = {
            'site': sites[code],
            'enabled': True,
            'site_values': {
                'PLATFORM_NAME': config.get_name(code),
                'Platform_name': config.get_name(code),
                'LMS_ROOT_URL': config.get_lms_url(code),
                'LMS_BASE': config.get_lms_url(code),
                'ECOMMERCE_PUBLIC_URL_ROOT': config.get_ecommerce_url(code),
                'Course_org_filter': code,
                'COURSE_CATALOG_API_URL': config.get_discovery_url(code),
            }
        }
        logger.info('Creating SiteConfiguration for {} - {}'.format(code, site_configuration))
        sc, created = SiteConfiguration.objects.get_or_create(site=site_configuration['site'], defaults=site_configuration)
        if not created:
            sc.save()

def run(config_file_path):

    sys.path.append('/edx/app/edxapp/edx-platform')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.envs.devstack_docker')  # for production use lms.envs.production

    import django
    django.setup()

    config = load_config(config_file_path)

    create_organizations(config)
    sites = create_sites(config)
    create_site_configurations(config, sites)


if __name__ == '__main__':
    parser = common_args()
    cli_args = parser.parse_args()
    run(cli_args.ConfigFilePath)
