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
        self.sub_tenant_id = kwargs.get('sub_tenant_id', True)
        if isinstance(self.sub_tenant_id, basestring):
            self.sub_tenant_id = self.sub_tenant_id.lower()
            if self.sub_tenant_id in ['true', 'yes']:
                self.sub_tenant_id = True
            else:
                self.sub_tenant_id = False
        self.auth_id = kwargs.get('auth_path_id', '/defaultauth')
        self.auth_path_obj = urlparse(self.auth_path)
        self.token = None
        self.tenant_id = None
        self.token_timestamp = time.time()
        super(DefaultAuth, self).__init__(*args)

    @webob.dec.wsgify(RequestClass=wsgi.Request)
    def __call__(self, req):
        if req.headers.get('X-Auth-Token'): 
            # already has auth token
            pass
        else:
            # We expire the token every 10 minutes
            if time.time() - self.token_timestamp >= 600000:
                self.token_timestamp = time.time()
                self.token = None

            self.access_resource(req)

        if req.path == self.auth_id:
            res = Response()
            res.status = 200
            res.headers['Content-Type'] = 'text/plain'
            res.body = str(self.tenant_id) + '\r\n'
            return res
        else:
            if self.sub_tenant_id:
                parts = req.environ.get('PATH_INFO').split('/')
                if len(parts) > 1 and self.tenant_id:
                    parts[1] = self.tenant_id
                    req.environ['PATH_INFO'] = '/'.join(parts)
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
                self.tenant_id = res_obj['access']['token']['tenant']['id']
            conn.close()

        req.headers['X_AUTH_TOKEN'] = self.token
