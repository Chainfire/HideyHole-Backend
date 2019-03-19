GCLOUD_PROJECT:=$(shell gcloud config list project --format="value(core.project)")

.PHONY: all
all: deploy

.PHONY: create-cluster
create-cluster:
	gcloud container clusters create hideyhole \
		--scopes "https://www.googleapis.com/auth/userinfo.email","cloud-platform" \
		--num-nodes 4 --zone "us-central1-b"

.PHONY: create-bucket
create-bucket:
	gsutil mb gs://$(GCLOUD_PROJECT)
	gsutil defacl set public-read gs://$(GCLOUD_PROJECT)

.PHONY: build
build:
	docker build -t gcr.io/$(GCLOUD_PROJECT)/hideyhole .

.PHONY: push
push: build
	docker push gcr.io/$(GCLOUD_PROJECT)/hideyhole

.PHONY: deploy
deploy: push
	kubectl create -f ../hideyhole-backend-manifests/hideyhole.yaml
	kubectl expose deployment hideyhole --target-port=8080 --type=NodePort
	kubectl apply -f ../hideyhole-backend-manifests/ingress.yaml

.PHONY: update
update:
	kubectl patch deployment hideyhole -p "{\"spec\":{\"template\":{\"metadata\":{\"labels\":{\"date\":\"`date +'%s'`\"}}}}}"

.PHONY: delete
delete:
	kubectl delete rc hideyhole
	kubectl delete service hideyhole
	kubectl delete service hideyhole
	kubectl delete ingress hideyhole-ingress
	kubectl delete deployment hideyhole
