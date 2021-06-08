
dev.run-lms:
	python scripts/generate_lms.py config/config.yaml --settings lms.envs.devstack_docker

dev.run-discovery:
	python scripts/generate_discovery.py config/config.yaml --settings course_discovery.settings.devstack

dev.run-ecommerce:
	python scripts/generate_ecommerce.py config/config.yaml --settings ecommerce.settings.devstack


run-lms:
	bash -c "source /edx/app/edxapp/venvs/edxapp/bin/activate && python scripts/generate_lms.py config/config.yaml --settings lms.envs.production"

run-discovery:
	bash -c "source /edx/app/discovery/venvs/discovery/bin/activate && python scripts/generate_discovery.py config/config.yaml --settings course_discovery.settings.production"

run-ecommerce:
	bash -c "source /edx/app/ecommerce/venvs/ecommerce/bin/activate && python scripts/generate_ecommerce.py config/config.yaml --settings ecommerce.settings.production"


run: run-lms run-discovery run-ecommerce
