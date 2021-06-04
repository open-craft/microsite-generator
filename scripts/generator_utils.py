import json
import argparse


def common_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("ConfigFilePath", metavar='config_file_path', type=str, help="Configuration data file path.")
    return parser


def load_config(file_path):
    with open(file_path) as file:
        config = json.load(file)
    return Config(config)


def update_model(model, **kwargs):
    for attr, val in kwargs.items():
        setattr(model, attr, val)
    model.save()

class Config:

    def __init__(self, config):
        self.config = config

    def get_microsite_codes(self):
        return self.config['microsites'].keys()

    def get_main_domain(self):
        return self.config['main_domain']

    def get_microsite_config(self, code):
        return self.config['microsites'][code]

    def get_lms_domain(self, code):
        microsite_config = self.get_microsite_config(code)
        main_domain = self.get_main_domain()
        domain = microsite_config.get('domain')
        if domain:
            return domain
        else:
            return '{}.{}'.format(code.lower(), main_domain)

    def get_lms_url(self, code):
        return 'https://{}'.format(self.get_lms_domain(code))

    def get_studio_url(self, code):
        return 'https://studio.{}'.format(self.get_lms_domain(code))

    def get_discovery_domain(self, code):
        return 'discovery.{}'.format(self.get_lms_domain(code))

    def get_discovery_url(self, code):
        return 'https://{}'.format(self.get_discovery_domain(code))

    def get_ecommerce_domain(self, code):
        return 'ecommerce.{}'.format(self.get_lms_domain(code))

    def get_ecommerce_url(self, code):
        return 'https://{}'.format(self.get_ecommerce_domain(code))

    def get_name(self, code):
        return self.get_microsite_config(code)['name']