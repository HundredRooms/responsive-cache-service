SHELL := /bin/bash
include Makefile.variables
include Makefile.utils

build: requirements.txt
	docker-compose $(ymls) build


run:
	docker-compose $(ymls) up cachete.api


flake8:
	docker-compose $(test_ymls) run --rm cachete.api flake8 cache/
	docker-compose $(test_ymls) run --rm tensorflow flake8 cache/

tf_shell:
	docker-compose $(ymls) run --rm tensorflow ipython

init_env:
	$(MAKE) build
	$(MAKE) download_files files=regressor_agregate_1k.csv
	$(MAKE) adapt_input_file

train:
	$(MAKE) $(train-var)

hyperparameter-tuning:
	@echo "Job config:"
	@cat training/$(job-config)
	job=$${job:-$(job-prefix)$$( \
		num=$$(./dgcloud ml-engine jobs list | grep $(job-prefix) | sed 's/$(job-prefix)//' | sed 's/ .*//' | sort -g | tail -n 1); \
		if [ $$num ]; then echo $$(($$num + 1)); else echo 0; fi \
		)}; \
		./dgcloud ml-engine jobs submit training $$job \
		--module-name=cache.main \
		--package-path=cache \
		--job-dir=$(job-dir) \
		--config=$(job-config) \
		-- \
		--out_dir=$(output-path-cloud) \
		--train_file=$(file-train-cloud) \
		--test_file=$(file-test-cloud) \
		--train_steps=$(train-steps)

# Tensorboard
tensorboard:
	docker-compose $(ymls) run --rm tensorflow tensorboard --logdir=$(output-path)


tensorboard-cloud:
	$(eval export output-path)
	$(MAKE) tensorboard

# Jobs
job-logs:
	$(MAKE) job-func func="gcloud ml-engine jobs stream-logs"


job-describe:
	$(MAKE) job-func func="gcloud ml-engine jobs describe"


job-echo-last:
	$(MAKE) job-func func="echo"

# Models
upload_model:
	$(eval export-path = $(output-path)/export/Servo)
	$(eval local-export = $(export-path)/$(shell ls -1t training/$(export-path) | head -n 1))
	docker-compose $(ymls) run --rm tensorflow mv $(local-export) $(export-path)/$(folder)
	docker-compose $(ymls) run --rm tensorflow gsutil cp -r $(export-path)/$(folder) $(remote-export)


create-version:
	./dgcloud ml-engine versions create $(version) --model=$(model) --origin=$(remote-export)/$(folder) --runtime-version=1.0


create-model:
	./dgcloud ml-engine models create $(model-name) --regions=$(regions)
	$(MAKE) create-version model=$(model-name) version=v1 folder=$(folder)


adapt-and-train:
	$(eval export)
	$(MAKE) adapt-input-file
	$(MAKE) train
