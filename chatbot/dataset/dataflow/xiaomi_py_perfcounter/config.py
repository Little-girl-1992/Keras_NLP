#!/usr/bin/env python
# encoding: utf8

import socket

agent_cofing = dict(
    endpoint=socket.gethostname() or 'localhost',
    agent_uri='http://127.0.0.1:1988/v1/push',
    step=60
)


def set_agent_option(k, v):
    agent_cofing[k] = v
