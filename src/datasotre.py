# -*- coding: utf-8 -*-
from etcd import EtcdResult, Client


def get_client(uri):
    u"""
    @param uri : uri
    @type  uri : str
    @rtype DataStoreClient
    """

    if uri.startswith("etcd://"):
        return EtcdClient(uri.replace("etcd://", ""))
    else:
        raise Exception("unsupported data store")


class DataStoreClient(object):

    def get_existing(self):
        raise NotImplementedError

    def wait_modification(self):
        raise NotImplementedError


class _EtcdClientExt(Client):

    def __init__(self, host='127.0.0.1', port=4001, read_timeout=60, allow_redirect=True, protocol='http', cert=None,
                 ca_cert=None, allow_reconnect=False):
        super(_EtcdClientExt, self).__init__(host, port, read_timeout, allow_redirect, protocol, cert, ca_cert,
                                             allow_reconnect)

    def watch(self, key, index=None, timeout=None, **kwargs):
        """
        Blocks until a new event has been received, starting at index 'index'

        Args:
            key (str):  Key.

            index (int): Index to start from.

            timeout (int):  max seconds to wait for a read.

        Returns:
            client.EtcdResult

        Raises:
            KeyValue:  If the key doesn't exists.

            urllib3.exceptions.TimeoutError: If timeout is reached.

        >>> print client.watch('/key').value
        'value'

        """
        if index:
            return self.read(key, wait=True, waitIndex=index, timeout=timeout, **kwargs)
        else:
            return self.read(key, wait=True, timeout=timeout, **kwargs)

    def eternal_watch(self, key, index=None, **kwargs):
        """
        Generator that will yield changes from a key.
        Note that this method will block forever until an event is generated.

        Args:
            key (str):  Key to subcribe to.
            index (int):  Index from where the changes will be received.

        Yields:
            client.EtcdResult

        >>> for event in client.eternal_watch('/subcription_key'):
        ...     print event.value
        ...
        value1
        value2

        """
        local_index = index
        while True:
            response = self.watch(key, index=local_index, timeout=0, **kwargs)
            if local_index is not None:
                local_index += 1
            yield response


class EtcdClient(DataStoreClient):

    def __init__(self, uri):
        u"""
        @type uri str
        """
        import logging
        super(EtcdClient, self).__init__()

        self.logger = logging.getLogger(__name__)

        _a = uri.split(":", 1)
        if len(_a) == 2:
            self.host = _a[0]

            _b = _a[1].split("/", 1)
            self.port = int(_b[0])
            service = "/"+_b[1] if len(_b) == 2 else "/"
        else:
            _b = _a[0].split("/", 1)
            self.host = _b[0]
            self.port = 4001
            service = "/"+_b[1] if len(_b) == 2 else "/"

        self.service = service[:-1] if service.endswith("/") else service
        self.underlying = _EtcdClientExt(host=self.host, port=self.port)

    def get_existing(self):
        response = self.underlying.read(self.service, recursive=True)
        return self._to_dict(response)

    def wait_modification(self):

        for _ in self.underlying.eternal_watch(self.service, recursive=True):
            return self._to_dict(self.underlying.read(self.service, recursive=True))

    def _to_dict(self, response):
        u"""
        @type response: EtcdResult
        """

        def worker(paths, value):
            head = paths[0]
            tail = paths[1:]
            if not tail:
                return {head: value}
            else:
                return {head: worker(tail, value)}

        values = {}
        for n in response.leaves:
            if self.service != "/":
                dir_name = self.service[self.service.rfind("/"):]
                striped = n.key[n.key.find(dir_name):]
            else:
                striped = n.key
            values.update({striped: n.value})

        dicts = []
        for p, v in values.items():
            dicts.append(worker(p.split("/")[1:], v))

        def merge(d1, d2):
            u"""
            @type d1: dict
            @type d2: dict
            """
            for d2k, d2v in d2.items():
                if d2k not in d1:
                    d1.update(d2)
                else:
                    d1v = d1[d2k]
                    if isinstance(d1v, dict) and isinstance(d2v, dict):
                        merge(d1v, d2v)
                    else:
                        d1[d2k] = d2v

        merged = {}
        for d in dicts:
            merge(merged, d)

        return merged
