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

In `/etc/nova/api-paste.ini`, add a path allow the filter to get back tenant id

    [composite:osapi_compute]
    use = call:nova.api.openstack.urlmap:urlmap_factory
    /: oscomputeversions
    ...
    ...
    /defaultauth: openstack_compute_api_v2

In `/etc/nova/api-paste.ini`, add default auth filter

    [composite:openstack_compute_api_v2]
    use = call:nova.api.auth:pipeline_factory
    noauth = faultwrap sizelimit noauth ratelimit cimi osapi_compute_app_v2
    keystone = faultwrap sizelimit defaultauth authtoken keystonecontext ratelimit cimi osapi_compute_app_v2
    keystone_nolimit = faultwrap sizelimit authtoken keystonecontext cimi osapi_compute_app_v2

And add the following section to the file:

    [filter:defaultauth]
    use = egg:defaultauth#defaultauth
    path = http://localhost:5000/v2.0/tokens
    user = <your userid>
    password = <your password>
    tenant = <your tenant>
    auth_path_id = /defaultauth
    sub_tenant_id = true (default)

Test and verify it works
========================

Get tenant id by issue the following command

    curl http://192.168.1.210:8774/defaultauth 

    This will return the tenant id

Use the tenant id from the above to access OpenStack artifacts:

    curl http://192.168.1.210:8774/v2/<tenant_id>/images

