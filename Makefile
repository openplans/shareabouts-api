.PHONY: test-env test test-clean build gcp-push gcp-restart gcp-deploy

# Build the container image
build:
	podman build -t shareabouts-api -f Containerfile .

# Push image to GCP Container Registry
# Requires: PROJECT_ID, ENVIRONMENT_NAME environment variables
gcp-push:
	@if [ -z "$(PROJECT_ID)" ]; then echo "Error: PROJECT_ID is not set"; exit 1; fi
	@if [ -z "$(ENVIRONMENT_NAME)" ]; then echo "Error: ENVIRONMENT_NAME is not set"; exit 1; fi
	podman tag shareabouts-api gcr.io/$(PROJECT_ID)/shareabouts-api:latest-$(ENVIRONMENT_NAME)
	podman push gcr.io/$(PROJECT_ID)/shareabouts-api:latest-$(ENVIRONMENT_NAME)

# Restart the Cloud Run service with the latest image
# Requires: PROJECT_ID, ENVIRONMENT_NAME, SERVICE_NAME, REGION environment variables
gcp-restart:
	@if [ -z "$(PROJECT_ID)" ]; then echo "Error: PROJECT_ID is not set"; exit 1; fi
	@if [ -z "$(ENVIRONMENT_NAME)" ]; then echo "Error: ENVIRONMENT_NAME is not set"; exit 1; fi
	@if [ -z "$(SERVICE_NAME)" ]; then echo "Error: SERVICE_NAME is not set"; exit 1; fi
	@if [ -z "$(REGION)" ]; then echo "Error: REGION is not set"; exit 1; fi
	gcloud run services update $(SERVICE_NAME)-$(ENVIRONMENT_NAME) \
		--region $(REGION) \
		--image gcr.io/$(PROJECT_ID)/shareabouts-api:latest-$(ENVIRONMENT_NAME)

# Full deployment: build, push, and restart
gcp-deploy: build gcp-push gcp-restart

# Stub .env file
test-env:
	cp .env.template .env

# Run tests in a clean container environment
test: test-env test-clean
	podman-compose run --rm test

# Just clean up containers
test-clean:
	podman-compose down --remove-orphans 2>/dev/null || true
