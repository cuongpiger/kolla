import contextlib
import logging
import json
import shutil
import sys
import threading
import time
from typing import List, Union
from queue import Queue
from oslo_config.cfg import ConfigOpts
from kolla.common import config as common_config
from kolla.common.utils import get_docker_squash_version, make_a_logger
from kolla.image.kolla_worker import KollaWorker
from kolla.image.tasks import BuildTask
from kolla.image.utils import LOG
from kolla.image.utils import Status
from oslo_config import cfg

LOG = make_a_logger(__name__)


@contextlib.contextmanager
def join_many(threads):
    try:
        yield
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        try:
            LOG.info('Waiting for daemon threads exit. Push Ctrl + c again to force exit')
            for t in threads:
                if t.is_alive():
                    LOG.debug('Waiting thread %s to exit', t.name)
                    # NOTE(Jeffrey4l): Python Bug: When join without timeout,
                    # KeyboardInterrupt is never sent.
                    t.join(0xffff)
                LOG.debug('Thread %s exits', t.name)
        except KeyboardInterrupt:
            LOG.warning('Force exits')


class WorkerThread(threading.Thread):
    """
    Thread that executes tasks until the queue provides a tombstone.
    """

    #: Object to be put on worker queues to get them to die.
    tombstone = object()

    def __init__(self, conf: ConfigOpts, queue: 'Queue[Union[BuildTask, object]]'):
        super(WorkerThread, self).__init__()
        self.queue: Queue[Union[BuildTask, object]] = queue
        self.conf: ConfigOpts = conf
        self.should_stop: bool = False

    def run(self):
        while not self.should_stop:
            task: Union[BuildTask, object] = self.queue.get()
            LOG.debug(f"the type of task is {type(task)}")
            if task is self.tombstone:
                # Ensure any other threads also get the tombstone.
                self.queue.put(task)  # type: object
                break

            try:
                # the task now is `BuildTask`
                for attempt in range(self.conf.retries + 1):
                    if self.should_stop:
                        break
                    LOG.info("Attempt number: %s to run task: %s ", attempt + 1, task.name)
                    try:
                        task.run()  # start to build the image
                        if task.success:
                            break
                    except (Exception,):
                        LOG.exception('Unhandled error when running %s', task.name)
                    # try again...
                    task.reset()
                if task.success and not self.should_stop:
                    for next_task in task.followups:
                        LOG.info('Added next task %s to queue',
                                 next_task.name)
                        self.queue.put(next_task)
            finally:
                self.queue.task_done()


def run_build():
    """
    Build OpenStack component container images.
    """

    # Read and parse the config from CLI, /etc/kolla/kolla-build.conf and defaults
    conf: cfg.ConfigOpts = cfg.ConfigOpts()  # init the configuration variable
    common_config.parse(conf, sys.argv[1:], prog='kolla-build')

    # Check debug mode is turn on
    if conf.debug:
        LOG.setLevel(logging.DEBUG)

    # Check if docker-squash is used
    if conf.squash:
        squash_version: str = get_docker_squash_version()
        LOG.info('Image squash is enabled and "docker-squash" version is %s', squash_version)

    kolla = KollaWorker(conf)
    kolla.setup_working_dir()
    kolla.find_dockerfiles()
    kolla.create_dockerfiles()
    kolla.build_image_list()
    kolla.find_parents()
    kolla.filter_images()

    # Only generate the Dockerfile for the images, then exit
    if conf.template_only:
        for image in kolla.images:
            if image.status == Status.MATCHED:
                continue

            # Delete all the unnecessary directory, files, and so on
            shutil.rmtree(image.path)

        LOG.info('Dockerfiles are generated in %s', kolla.working_dir)
        return

    # We set the atime and mtime to 0 epoch to preserve allow the Docker cache
    # to work like we want. A different size or hash will still force a rebuild
    kolla.set_time()

    # Using Graphviz to build `*.dot` file
    if conf.save_dependency:
        kolla.save_dependency(conf.save_dependency)
        LOG.info('Docker images dependency are saved in %s', conf.save_dependency)
        return

    # List all the images without building
    if conf.list_images:
        kolla.list_images()
        return

    # List all image that matched the filter
    if conf.list_dependencies:
        kolla.list_dependencies()
        return

    push_queue: Queue[Union[BuildTask, object]] = Queue()
    build_queue: Queue[Union[BuildTask, object]] = kolla.build_queue(push_queue)
    workers: List[WorkerThread] = []

    with join_many(workers):
        try:
            for x in range(conf.threads):
                worker = WorkerThread(conf, build_queue)
                worker.daemon = True
                worker.start()
                workers.append(worker)

            for x in range(conf.push_threads):
                worker = WorkerThread(conf, push_queue)
                worker.daemon = True
                worker.start()
                workers.append(worker)

            # sleep until build_queue is empty
            while build_queue.unfinished_tasks or push_queue.unfinished_tasks:
                time.sleep(3)

            # ensure all threads exited happily
            push_queue.put(WorkerThread.tombstone)
            build_queue.put(WorkerThread.tombstone)
        except KeyboardInterrupt:
            # when user press Ctrl + c, we should stop all the threads
            for w in workers:
                w.should_stop = True  # mark this worker should stop safely
            push_queue.put(WorkerThread.tombstone)  # signal to stop the push queue
            build_queue.put(WorkerThread.tombstone)  # signal to stop the build queue
            raise

    if conf.summary:
        results = kolla.summary()
        if conf.format == 'json':
            print(json.dumps(results))
    kolla.cleanup()
    return kolla.get_image_statuses()
