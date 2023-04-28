build-keystone-image:
	@python ./kolla/cmd/build.py --image-name-prefix DEV- -b ubuntu -d True

build-from-file:
	@python ./kolla/cmd/build.py --image-name-prefix DEV- -b ubuntu -d True


# for the installed kolla
true-build-keystone-image:
	@kolla-build -b ubuntu keystone


true-reinstall:
	@pip3 uninstall kolla -y
	@pip3 install .