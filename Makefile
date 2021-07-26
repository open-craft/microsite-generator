
help:    ## Show help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'


run: ## Generate microsite configuration for all services
run: run-lms run-discovery run-ecommerce

run-lms: ## Generate microsite configuration in LMS
	bash -c "source /edx/app/edxapp/edxapp_env && python scripts/generate_lms.py config/config.yaml --settings lms.envs.production"

run-discovery: ## Generate microsite configuration in Discovery
	bash -c "source /edx/app/discovery/discovery_env && python scripts/generate_discovery.py config/config.yaml --settings course_discovery.settings.production"

run-ecommerce:  ## Generate microsite configuration in eCommerce. Must be run after `run-lms`
	bash -c "source /edx/app/ecommerce/ecommerce_env && python scripts/generate_ecommerce.py config/config.yaml --settings ecommerce.settings.production"


dev.run-lms:    ## Devstack - Generate microsite configuration in LMS
	python scripts/generate_lms.py config/config.yaml --settings lms.envs.devstack_docker

dev.run-discovery:  ## Devstack - Generate microsite configuration in Discovery
	python scripts/generate_discovery.py config/config.yaml --settings course_discovery.settings.devstack

dev.run-ecommerce:  ## Devstack - Generate microsite configuration in eCommerce
	python scripts/generate_ecommerce.py config/config.yaml --settings ecommerce.settings.devstack
