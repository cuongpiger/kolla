#!/bin/bash

# Bootstrap and exit if KOLLA_BOOTSTRAP variable is set. This catches all cases
# of the KOLLA_BOOTSTRAP variable being set, including empty.
if [[ "${!KOLLA_BOOTSTRAP[@]}" ]]; then
    qinling-db-manage upgrade head
    exit 0
fi

. /usr/local/bin/kolla_httpd_setup
