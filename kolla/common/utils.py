# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import subprocess  # nosec
import sys
from typing import Optional
from oslo_config.cfg import ConfigOpts

_LOGGER_FORMAT = "[%(levelname)5s][%(asctime)s] %(name)s.%(funcName)s:%(lineno)s --- %(message)s"


class _CustomFormatter(logging.Formatter):
    _debug_clr = "\033[32m"
    _info_clr = "\033[34m"
    _yellow = "\x1b[33;20m"
    _red = "\x1b[31;20m"
    _bold_red = "\x1b[31;1m"
    _reset = "\x1b[0m"
    _format = _LOGGER_FORMAT

    FORMATS = {
        logging.DEBUG: _debug_clr + _format + _reset,
        logging.INFO: _info_clr + _format + _reset,
        logging.WARNING: _yellow + _format + _reset,
        logging.ERROR: _red + _format + _reset,
        logging.CRITICAL: _bold_red + _format + _reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def make_a_logger(image_name: Optional[str] = None, conf: Optional[ConfigOpts] = None):
    if not image_name:
        raise ValueError("image_name is required")

    log = logging.getLogger(image_name)
    if conf is not None and conf.debug:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    if not log.handlers:
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(_CustomFormatter())
        # NOTE(hrw): quiet mode matters only on console
        if conf is not None and conf.quiet:
            stream_handler.setLevel(logging.CRITICAL)
        else:
            stream_handler.setLevel(loglevel)
        log.addHandler(stream_handler)
        log.propagate = False

        if conf is not None and conf.logs_dir and image_name:
            filename = os.path.join(conf.logs_dir, "%s.log" % image_name)
            handler = logging.FileHandler(filename, delay=True)
            # NOTE(hrw): logfile will be INFO or DEBUG
            handler.setLevel(loglevel)
            handler.setFormatter(_CustomFormatter())
            log.addHandler(handler)

    # NOTE(hrw): needs to be high, handlers have own levels
    log.setLevel(logging.DEBUG)
    return log


LOG = make_a_logger(__name__)


def get_docker_squash_version() -> str:
    try:
        stdout = subprocess.check_output(['docker-squash', '--version'], stderr=subprocess.STDOUT)
        return str(stdout.split()[0], 'utf-8')
    except OSError as ex:
        if ex.errno == 2:
            LOG.error(('"docker-squash" command is not found.'
                       ' try to install it by "pip install docker-squash"'))
        raise


def squash(old_image, new_image,
           from_layer=None,
           cleanup=False,
           tmp_dir=None):
    cmds = ['docker-squash', '--tag', new_image, old_image]
    if cleanup:
        cmds += ['--cleanup']
    if from_layer:
        cmds += ['--from-layer', from_layer]
    if tmp_dir:
        cmds += ['--tmp-dir', tmp_dir]
    try:
        subprocess.check_output(cmds, stderr=subprocess.STDOUT)  # nosec
    except subprocess.CalledProcessError as ex:
        LOG.exception('Get error during squashing image: %s',
                      ex.output)
        raise
