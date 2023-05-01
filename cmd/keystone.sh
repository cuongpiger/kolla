#!/bin/bash

local python_cmd=$(which python)
local pip_cmd=$(which pip)
local log_dirs=$HOME/kolla/logs
local project_name=keystone
local threads=1
local image_name_prefix=dev-
local base=ubuntu
local debug=True
local work_dir=$HOME/kolla/docker
local save_dependency=$HOME/kolla/graphs/$project_name/graph.dot

if [ ! -d $log_dirs/$project_name ]; then
  mkdir -p $log_dirs/$project_name
fi

if [ ! -d $work_dir ]; then
  mkdir -p $work_dir
fi

if [ ! -e $save_dependency ]; then
  mkdir -p $HOME/kolla/graphs/$project_name
  touch $save_dependency
fi

function dev_gen_graph() {
  log_proj=$log_dirs/$project_name
  $python_cmd ./kolla/cmd/build.py \
    --save-dependency $save_dependency \
    --work-dir $work_dir \
    --logs-dir $log_proj \
    --image-name-prefix $image_name_prefix \
    --threads $threads \
    --base $base \
    --debug $debug \
    $project_name
  dot -Tpng $save_dependency -o $HOME/kolla/graphs/$project_name/graph.png
}

function dev_run() {
  log_proj=$log_dirs/$project_name

  $python_cmd ./kolla/cmd/build.py \
    --work-dir $work_dir \
    --logs-dir $log_proj \
    --image-name-prefix $image_name_prefix \
    --threads $threads \
    --base $base \
    --debug $debug \
    $project_name
}

function reinstall_kolla() {
  $pip_cmd uninstall -y kolla
  $pip_cmd install .
}
