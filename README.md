Default Auth for OpenStack's Nova
--------------------------

A Python egg that create a auth token for request to OpenStack

Setup
=====

1. Install [Openstack Nova](http://wiki.openstack.org/InstallInstructions/Nova)
2. Grab the default auth implementation from github:
     `git clone http://github.com/osaddon/defaultauth`
3. Install this python egg: `sudo python setup.py install`
4. Configure default auth to work with Nova:

In `/etc/nova/api-paste.ini`, add default auth filter

    [composite:openstack_compute_api_v2]
    use = call:nova.api.auth:pipeline_factory
    noauth = faultwrap sizelimit noauth ratelimit cimi osapi_compute_app_v2
    keystone = faultwrap sizelimit defaultauth authtoken keystonecontext ratelimit cimi osapi_compute_app_v2
    keystone_nolimit = faultwrap sizelimit authtoken keystonecontext cimi osapi_compute_app_v2

And add the following section to the file:

    [filter:defaultauth]
    use = egg:defaultauth#defaultauthapp
    path = http://localhost:5000/v2.0/tokens
    user = <your userid>
    password = <your password>
    tenant = <your tenant>

Running tests
=============
