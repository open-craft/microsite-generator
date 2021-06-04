from collections import defaultdict
import sys
import os
import logging
from generator_utils import load_config, common_args, update_model


logger = logging.getLogger(__name__)


def create_sites(config):
    from django.contrib.sites.models import Site

    sites = {}
    for code in config.get_microsite_codes():
        site = {
            'domain': config.get_discovery_domain(code),
            'name': config.get_discovery_domain(code)
        }
        logger.info('Creating site for {} - {}'.format(code, site))
        site, _ = Site.objects.get_or_create(domain=site['domain'], defaults=site)
        sites[code] = site
    return sites


def create_partner(config, sites):
    from course_discovery.apps.core.models import Partner

    for code in config.get_microsite_codes():
        partner = {
            'name': code,
            'site': sites[code],
            'short_code': code,
            'courses_api_url': '{}/api/courses/v1/'.format(config.get_lms_url(code)),
            'ecommerce_api_url': '{}/api/v2/'.format(config.get_ecommerce_url(code)),
            'organizations_api_url': '{}/api/organizations/v0/'.format(config.get_lms_url(code)),
            'lms_url': config.get_lms_url(code),
            'lms_admin_url': '{}/admin'.format(config.get_lms_url(code)),
            'studio_url': config.get_studio_url(code)
        }
        logger.info('Creating partner for {} - {}'.format(code, partner))
        p, created = Partner.objects.get_or_create(site=partner['site'], defaults=partner)
        if not created:
            update_model(p, **partner)


def run(config_file_path):

    sys.path.append('/edx/app/discovery/discovery')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'course_discovery.settings.devstack')  # for production use lms.envs.production

    import django
    django.setup()

    config = load_config(config_file_path)

    sites = create_sites(config)
    create_partner(config, sites)


if __name__ == '__main__':
    parser = common_args()
    cli_args = parser.parse_args()
    run(cli_args.ConfigFilePath)
