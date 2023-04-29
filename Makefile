build-keystone-image:
	@python ./kolla/cmd/build.py --image-name-prefix DEV- --base ubuntu --debug True

build-from-file:
	@python ./kolla/cmd/build.py --image-name-prefix DEV- --base ubuntu --debug True


# for the installed kolla
true-build-keystone-image:
	@kolla-build --base ubuntu keystone


true-reinstall:
	@pip3 uninstall kolla -y
	@pip3 install .