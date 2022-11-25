REGISTRY=localhost:35000
REGISTRY_K8S=k3d-main-registry.localhost:5000
PROJECT=hideyhole
NAMESPACE=hideyhole
DEPLOYMENT=hideyhole
CONTAINER=hideyhole-app
IMAGE=hideyhole

SHORT_SHA:=$(shell git rev-parse --short HEAD)

.PHONY: all
all: deploy

.PHONY: build
build:
	docker build -t $(REGISTRY)/$(PROJECT)/$(IMAGE):$(SHORT_SHA) .

.PHONY: push
push: build
	docker push $(REGISTRY)/$(PROJECT)/$(IMAGE):$(SHORT_SHA)

.PHONY: deploy
deploy: push
	kubectl apply -f manifests/k3d/deployment.yaml
	kubectl apply -f manifests/k3d/service.yaml
	kubectl apply -f manifests/k3d/ingress.yaml
	kubectl set image -n $(NAMESPACE) deployment/$(PROJECT) $(CONTAINER)=$(REGISTRY_K8S)/$(PROJECT)/$(IMAGE):$(SHORT_SHA)

#to be ported
#.PHONY: delete
#delete:
#	kubectl delete rc hideyhole
#	kubectl delete service hideyhole
#	kubectl delete service hideyhole
#	kubectl delete ingress hideyhole-ingress
#	kubectl delete deployment hideyhole
#	gsutil rb gs://$(GCLOUD_PROJECT)
