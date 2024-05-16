#!/usr/bin/python3
from fabric.api import *
from datetime import datetime
from os import path

# Define the list of host servers
env.hosts = ['18.209.20.255', '34.73.76.135']
# Define the user for SSH connection
env.user = 'ubuntu'
# Define the path to the SSH private key
env.key_filename = '~/.ssh/id_rsa'

def do_pack():
    """Function to compress directory into a .tgz archive"""
    # Get current time
    now = datetime.now()
    now = now.strftime('%Y%m%d%H%M%S')
    archive_path = 'versions/web_static_' + now + '.tgz'

    # Create archive
    local('mkdir -p versions/')
    result = local('tar -cvzf {} web_static/'.format(archive_path))

    # Check if archiving was successful
    if result.succeeded:
        return archive_path
    return None

def do_deploy(archive_path):
    """Deploy web files to server"""
    try:
        if not (path.exists(archive_path)):
            return False

        # upload archive
        put(archive_path, '/tmp/')

        # create target dir
        timestamp = archive_path[-18:-4]
        run('sudo mkdir -p /data/web_static/releases/web_static_{}/'.format(timestamp))

        # uncompress archive and delete .tgz
        run('sudo tar -xzf /tmp/web_static_{}.tgz -C /data/web_static/releases/web_static_{}/'.format(timestamp, timestamp))

        # remove archive
        run('sudo rm /tmp/web_static_{}.tgz'.format(timestamp))

        # move contents into host web_static
        run('sudo mv /data/web_static/releases/web_static_{}/web_static/* /data/web_static/releases/web_static_{}/'.format(timestamp, timestamp))

        # remove extraneous web_static dir
        run('sudo rm -rf /data/web_static/releases/web_static_{}/web_static'.format(timestamp))

        # delete pre-existing sym link
        run('sudo rm -rf /data/web_static/current')

        # re-establish symbolic link
        run('sudo ln -s /data/web_static/releases/web_static_{}/ /data/web_static/current'.format(timestamp))
    except:
        return False

    # return True on success
    return True

def do_clean(number=0):
    """Clean up old deployments"""
    number = int(number)
    if number < 1:
        number = 1

    # Delete old archives locally
    with lcd('versions'):
        local('ls -1t | tail -n +{} | xargs -I {{}} rm -- {{}}'.format(number + 1))

    # Delete old archives on remote servers
    with cd('/data/web_static/releases'):
        run('ls -1t | tail -n +{} | xargs -I {{}} sudo rm -rf -- {{}}'.format(number + 1))

def deploy():
    """Deploy web static"""
    return do_deploy(do_pack())
