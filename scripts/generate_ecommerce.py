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
            'domain': context['ecommerce_domain'],
            'name': context['ecommerce_domain']
        }
        logger.info('Creating site for {} - {}'.format(code, site))
        site, _ = Site.objects.get_or_create(domain=site['domain'], defaults=site)
        sites[code] = site
    return sites


def create_partner(config, sites):
    from ecommerce.extensions.partner.models import Partner

    partners = {}
    for code in config.get_microsite_codes():
        partner = {
            'name': code,
            'default_site': sites[code],
            'short_code': code,
        }
        logger.info('Creating partner for {} - {}'.format(code, partner))
        p, created = Partner.objects.get_or_create(short_code=code, defaults=partner)
        if not created:
            update_model(p, **partner)
        partners[code] = p
    return partners


def create_site_configuration(config, sites, partners):
    from ecommerce.core.models import SiteConfiguration

    for code in config.get_microsite_codes():
        context = config.get_context(code)

        site_config = {
            'site': sites[code],
            'partner': partners[code],
            'lms_url_root': context['lms_url'],
            'discovery_api_url': context['discovery_api_url'],
            'oauth_settings': {
                'SOCIAL_AUTH_EDX_OAUTH2_URL_ROOT': context['lms_url'],
                'SOCIAL_AUTH_EDX_OAUTH2_ISSUERS': [
                    context['lms_url']
                ],
                'SOCIAL_AUTH_EDX_OAUTH2_LOGOUT_URL': '{}/logout'.format(context['lms_url'])
            }
        }

        site_config = config.apply_overrides(code, 'ecommerce', SiteConfiguration, site_config)
        sc, created = SiteConfiguration.objects.get_or_create(partner=partners[code], defaults=site_config)
        if not created:
            update_model(sc, **site_config)


def run(config_file_path, settings_module):

    sys.path.append('/edx/app/ecommerce/ecommerce')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)  # for production use lms.envs.production

    import django
    django.setup()

    config = load_config(config_file_path)

    sites = create_sites(config)
    partners = create_partner(config, sites)
    create_site_configuration(config, sites, partners)


if __name__ == '__main__':
    parser = common_args()
    cli_args = parser.parse_args()
    run(cli_args.ConfigFilePath, cli_args.settings)
