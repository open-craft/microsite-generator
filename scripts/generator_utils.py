import yaml
import os
from argparse import ArgumentParser
from const import GENERATED_SHARED_CONFIG_FILE


def common_args() -> ArgumentParser:
    """
    Common argument parser for each script
    """
    parser = ArgumentParser()
    parser.add_argument("ConfigFilePath", metavar='config_file_path', type=str, help="Configuration data file path.")
    parser.add_argument("--settings", type=str, required=False, help="Settings module")
    return parser


def update_model(model, **kwargs):
    """
    Helper function for updaing a django model
    Args:
        model: Django Model
        kwargs: Keyword args for each field values
    """
    for attr, val in kwargs.items():
        setattr(model, attr, val)
    model.save()


def deep_merge(source, destination):
    """
    helper function to merge two dictionaries
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            deep_merge(value, node)
        else:
            destination[key] = value

    return destination


class Config:
    """
    Configuration generation helper class
    """

    microsites = {}

    organizations = {}

    # main domain to work with
    main_domain = None

    # LMS OAuth clients
    oauth = {
        'ecommerce_sso_client': 'custom-sites-ecommerce-sso',
        'ecommerce_backend_service_client': 'ecommerce-backend-service',
    }

    # stores global override values
    global_overrides = {
        'overrides': {},
        'context_overrides': {},
    }

    def __init__(self, config):
        """
        Initialize Config class
        """
        self._config = config
        self.organizations = config['organizations']
        self.main_domain = config['main_domain']

        self.oauth = config.get(
            'oauth',
            self.oauth
        )

        self._extract_microsites(config)
        self._extract_overrides(config)

    def _extract_overrides(self, config):
        """
        A helper method to prepare self.overrides from given config.
        """
        if config['microsites']:
            for key, val in config['microsites'].items():
                 # $ is a special key and used for global overrides
                if key == '$':
                    self.global_overrides.update(val)
                    continue

                # if site specifc override provided, add them to self.microsites
                if val.get('overrides'):
                    self.microsites[key]['overrides'] = deep_merge(
                        self.microsites[key]['overrides'],
                        val['overrides']
                    )

                # if site specifc context override provided, add them to self.microsites
                if val.get('context_overrides'):
                    self.microsites[key]['context_overrides'] = deep_merge(
                        self.microsites[key]['context_overrides'],
                        val['context_overrides']
                    )

    def _extract_microsites(self, config):
        """
        A helper method to prepare self.microsites from given config.
        """
        # if there will be a site for each organization
        if config.get('site_for_each_organization', False):
            for key, val in config['organizations'].items():
                self.microsites[key] = {
                    'name': val['name'],
                    'overrides': {
                        'lms': {
                            'openedx.core.djangoapps.site_configuration.models.SiteConfiguration': {
                                'site_values': {
                                    'course_org_filter': key
                                }
                            }
                        }
                    },
                    'context_overrides': {},
                }
        else:
            # otherwise microsites can be given seperately from organizations
            for key, val in config['microsites'].items():
                # $ is a special key and used for global overrides
                if key == '$':
                    continue

                self.microsites[key] = {
                    'name': val['name'],
                    'overrides': {},
                    'context_overrides': {},
                }

    def get_microsite_codes(self):
        """
        Get list of microsite codes
        """
        return self.microsites.keys()

    def get_organization_codes(self):
        """
        Get list of organization codes
        """
        return self.organizations.keys()

    def get_organization_name(self, code):
        """
        Given an organization code, returns its name
        """
        return self.organizations[code]['name']

    def get_context(self, code):
        """
        Prepares and returns a dictionary with usefull values for generating
        microsite configurations.
        """
        microsite = self.microsites[code]
        lms_domain = '{}.{}'.format(code.lower(), self.main_domain)
        discovery_domain = 'discovery.{}'.format(lms_domain)
        ecommerce_domain = 'ecommerce.{}'.format(lms_domain)
        studio_domain = 'studio.{}'.format(lms_domain)

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

        # apply global context overrides
        context.update(self.global_overrides['context_overrides'])

        # apply site specific context overrides
        context.update(microsite['context_overrides'])

        return context

    def apply_overrides(self, code, service, model_class, data):
        """
        Overrides existing value with global or site-specific value.

        Args:
            code (str): microsite code
            service (str): service key
            model_class (Model): django model
            data (dict): data dictionary that will be used to update the model
        """
        microsite = self.microsites[code]
        global_overrides = self.global_overrides['overrides']
        site_overrides = microsite['overrides']

        model_path = '{}.{}'.format(model_class.__module__, model_class.__name__)

        # if global override exists, apply them
        if service in global_overrides and model_path in global_overrides[service]:
            data = deep_merge(data, global_overrides[service][model_path])

        # if site specific override exists, apply them
        if service in site_overrides and model_path in site_overrides[service]:
            data = deep_merge(data, site_overrides[service][model_path])

        return data


def load_config(file_path) -> Config:
    """
    Helper function to load configuration yaml file
    """
    with open(file_path) as file:
        config = yaml.load(file)
    return Config(config)


def write_generated_values(data = {}):
    """
    Write new config value to the generated config file.
    """
    values = load_generated_values()
    values.update(data)
    with open(GENERATED_SHARED_CONFIG_FILE, 'w') as file:
        yaml.dump(values, file)


def load_generated_values():
    """
    Read config value from the generated config file.
    """
    values = {}
    if os.path.exists(GENERATED_SHARED_CONFIG_FILE):
        with open(GENERATED_SHARED_CONFIG_FILE) as file:
            values = yaml.load(file)
    return values
