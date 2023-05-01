#!/bin/bash

local python_cmd=$(which python)
local log_dirs=$HOME/kolla/logs
local project_name=keystone

if [ ! -d $log_dirs/$project_name ]; then
  mkdir -p $log_dirs/$project_name
fi

function run_dev() {
  log_proj=$log_dirs/$project_name
  threads=1
  image_name_prefix=dev-
  base=ubuntu
  debug=True

  $python_cmd ./kolla/cmd/build.py \
    --logs-dir $log_proj \
    --image-name-prefix $image_name_prefix \
    --threads $threads \
    --base $base \
    --debug $debug \
    $project_name
}
