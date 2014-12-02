=========
kvwatcher
=========
watch kvs, generating file from template


install
=======
::

    docker pull

for python 3.4


usage
=====
::

    usage: kvwatcher [-h] [-c CONFIG] watch

    desc

    optional arguments:
      -h, --help            show this help message and exit
      -c CONFIG, --config CONFIG
                            configuration yml file (default
                            '/etc/kvwatcher/config.yml')

but this asumes executing as docker.

::

    docker run -d --priviledged -p 80:8080 -v /path/to/confdir:/etc/kvwatcher image

license
=======

undecided
