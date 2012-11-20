# Copyright (c) 2012 OpenStack, LLC
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import webob.dec
import webob.exc
import json
from webob import Request, Response
from eventlet.green.httplib import HTTPConnection, HTTPSConnection
from urlparse import urlparse
import time

from nova import flags
from nova.openstack.common import cfg
from nova.openstack.common import log as logging
from nova import wsgi


LOG = logging.getLogger(__name__)


class DefaultAuth(wsgi.Middleware):
    """Add a auth token to WSGI environ."""

    def __init__(self, *args, **kwargs):
        print 'init', kwargs.get('user')
        self.auth_path = kwargs.get('path',
                                    'http://localhost:5000/v2.0/tokens')
        self.auth_user = kwargs.get('user', 'admin')
        self.auth_pass = kwargs.get('password', 'ps')
        self.auth_tenant = kwargs.get('tenant', 'admin')
        self.auth_path_obj = urlparse(self.auth_path)
        self.token = None
        self.token_timestamp = time.time()
        super(DefaultAuth, self).__init__(*args)

    @webob.dec.wsgify(RequestClass=wsgi.Request)
    def __call__(self, req):
        if req.headers.get('X-Auth-Token'): 
            # already has auth token
            pass
        else:
            if time.time() - self.token_timestamp >= 600000:
                self.token_timestamp = time.time()
                self.token = None

            self.access_resource(req)
        return self.application

    def access_resource(self, req):
        if self.token is None:
            if self.auth_path_obj.scheme == 'https':
                connection = HTTPSConnection
            else:
                connection = HTTPConnection

            body = {}
            body['auth'] = {'tenantName': self.auth_tenant}
            body['auth']['passwordCredentials'] = {'username': self.auth_user,
                                                   'password': self.auth_pass}
            body_str = json.dumps(body)

            headers = {}
            headers['ACCEPT'] = 'application/json'
            headers['CONTENT-TYPE'] = 'application/json'
            headers['CONTENT-LENGTH'] = len(body_str)
            conn = connection(self.auth_path_obj.hostname,
                              self.auth_path_obj.port)

            conn.request('POST', self.auth_path_obj.path, body_str, headers)
            res = conn.getresponse()

            if res.status == 200:
                res_obj = json.loads(res.read())
                self.token = res_obj['access']['token']['id']
            conn.close()

        req.headers['X_AUTH_TOKEN'] = self.token