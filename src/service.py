# -*- coding: utf-8 -*-


class DataStoreWatchService(object):

    def __init__(self, config):
        u"""
        @type uri : str
        @type config : dict
        """
        import logging
        from queue import Queue
        from threading import Condition

        self.queue = Queue()

        self.logger = logging.getLogger(__name__)

        self.value_provider = ValueProvider(config["data_store"], self.queue)
        self.file_generator = FileGenerator(
            self.queue,
            config["template_file"],
            config["generating_dest"],
            config["reload_cmd"])

        self.condition = Condition()

    def start(self):

        with self.condition:
            self.value_provider.start()
            self.file_generator.start()

            self.condition.wait()

        self.logger.info("waiting queue all done")
        self.queue.join()
        self.logger.info("shutdown")

    def shutdown(self):
        self.logger.info("now terminating...")
        with self.condition:
            self.condition.notify_all()


class ValueProvider(object):

    def __init__(self, uri, queue):
        from .datasotre import get_client
        import logging

        self.logger = logging.getLogger(__name__)

        self.client = get_client(uri)
        self.queue = queue

    def _watch_data_store(self):
        from etcd import EtcdException

        while True:
            try:
                fetched_dict = self.client.wait_modification()
                self.queue.put(fetched_dict)
            except EtcdException as e:
                self.logger.error("error occurred from etcd until watching: %s" % e)

    def start(self):
        from threading import Thread
        from etcd import EtcdException
        import time

        def watch():
            try:
                self.logger.info("fetching existing values")
                self.queue.put(self.client.get_existing())

                self._watch_data_store()

            except EtcdException as e:
                self.logger.error("data store returns error: %s" % e)

            except Exception as e:
                self.logger.error(e)
                time.sleep(1)

        watching_thread = Thread(target=watch, daemon=True)
        watching_thread.start()

        return watching_thread


class FileGenerator(object):

    def __init__(self, queue, template_path, generating_dest, reload_cmd):
        import logging
        from .command import Command
        from os.path import dirname, basename
        from jinja2 import Environment, FileSystemLoader

        self.logger = logging.getLogger(__name__)
        self.queue = queue

        self.env = Environment(loader=FileSystemLoader(dirname(template_path)))
        self.template_file = basename(template_path)
        self.generating_dest = generating_dest

        self.reload_cmd = Command(reload_cmd)

    def _generate_template(self, vars_dict):
            from tempfile import mkstemp
            from os import fdopen
            from shutil import move
            from jinja2 import TemplateError

            template = self.env.get_template(self.template_file)

            self.logger.info("fetch object from queue: %s" % vars_dict)
            try:
                self.logger.info("processing template")
                rendered = template.render(**vars_dict)

                fd, name = mkstemp()
                self.logger.info("generating staging file: %s" % name)
                with fdopen(fd, "w") as stage_file:
                    stage_file.write(rendered)

                move(name, self.generating_dest)
                self.logger.info("generating file applied to %s" % self.generating_dest)

                ret_code, out, err = self.reload_cmd.execute()
                if ret_code == 0:
                    self.logger.info("reload command (%s) was executed" % self.reload_cmd.command)
                else:
                    self.logger.warn("reload command (%s) was failed [ret code: %d, out: %s, err: %s]"
                                     % (self.reload_cmd.command, ret_code, out, err))

            except TemplateError as e:
                self.logger.warn("template generating is failure: %s" % e)
            except Exception as e:
                self.logger.error(e)

            finally:
                self.queue.task_done()

    def start(self):
        from threading import Thread

        def gen():
            while True:
                self._generate_template(self.queue.get())

        template_generating_thread = Thread(target=gen, daemon=True)
        template_generating_thread.start()

        return template_generating_thread
