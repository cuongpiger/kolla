dev-build-keystone-image:
	@python ./kolla/cmd/build.py --image-name-prefix dev- --threads 1 --base ubuntu --debug True keystone

dev-generate-keystone-image:
	@python ./kolla/cmd/build.py --save-dependency ./graph/keystone.dot --image-name-prefix dev- --base ubuntu --debug True keystone

dev-reinstall:
	@pip3 uninstall kolla -y
	@pip3 install .

# for the installed kolla
build-keystone-image:
	@kolla-build --image-name-prefix dev- --base ubuntu keystone
