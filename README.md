- Build Keystone image command:
  ```bash=
  kolla-build --base <linux_distro> [--debug] --namespace <docker_user_name> --profile keystone
  ```
    * **Notation**:
      * <linux_distro>: `centos`, `ubuntu`,...
      * <docker_user_name>: container registry username, ex: `docker.io/manhcuong8499`
      