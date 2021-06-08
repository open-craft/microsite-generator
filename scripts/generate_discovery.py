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
        context = config.get_context(code)
        site = {
            'domain': context['discovery_domain'],
            'name': context['discovery_domain']
        }
        logger.info('Creating site for {} - {}'.format(code, site))
        site, _ = Site.objects.get_or_create(domain=site['domain'], defaults=site)
        sites[code] = site
    return sites


def create_partner(config, sites):
    from course_discovery.apps.core.models import Partner

    for code in config.get_microsite_codes():
        context = config.get_context(code)
        partner = {
            'name': code,
            'site': sites[code],
            'short_code': code,
            'courses_api_url': '{}/api/courses/v1/'.format(context['lms_url']),
            'ecommerce_api_url': '{}/api/v2/'.format(context['ecommerce_url']),
            'organizations_api_url': '{}/api/organizations/v0/'.format(context['lms_url']),
            'lms_url': context['lms_url'],
            'lms_admin_url': '{}/admin'.format(context['lms_url']),
            'studio_url': context['studio_url']
        }
        partner = config.apply_overrides(code, 'discovery', Partner, partner)
        logger.info('Creating partner for {} - {}'.format(code, partner))
        p, created = Partner.objects.get_or_create(site=partner['site'], defaults=partner)
        if not created:
            update_model(p, **partner)


def run(config_file_path, settings_module):

    sys.path.append('/edx/app/discovery/discovery')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

    import django
    django.setup()

    config = load_config(config_file_path)

    sites = create_sites(config)
    create_partner(config, sites)


if __name__ == '__main__':
    parser = common_args()
    cli_args = parser.parse_args()
    run(cli_args.ConfigFilePath, cli_args.settings)
