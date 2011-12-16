import boto
from boto.ec2 import regioninfo


class EC2Client():
    """A simple but incomplete EC2 Client"""
    def __init__(self, api_node_host):
        self.connection = self._get_ec2_connection(api_node_host)

    def get_instances(self):
        """Get a list of instances in the form:
        [(u'10.0.0.3', u'i-00000002 (Server 2)'),
        (u'10.0.0.4', u'i-00000003 (Server 3)')]
        """
        instances = self._get_instances_from_ec2()
        return self._format_running_instances(instances)

    def _get_ec2_connection(self, api_node_hostname):
        """ Connect to an EC2 instance """
        # TODO - these are the dashboard user's hardcoded keys
        access_key = 'ef81eccc-172c-4aad-810b-05278bbdbbf3'
        secret_key = 'b24b6b50-dee5-4ed7-9d2a-ba965cd4493c'
        return boto.connect_ec2(aws_access_key_id=access_key,
                                aws_secret_access_key=secret_key,
                                is_secure=False,
                                region=regioninfo.RegionInfo(None, 'nova',
                                                            api_node_hostname),
                                port=8773,
                                path='/services/Cloud')

    def _get_instances_from_ec2(self):
        """ Returns all instances """
        reservations = self.connection.get_all_instances()
        instances = []
        for reservation in reservations:
            for instance in reservation.instances:
                instances.append(instance)
        return instances

    def _format_running_instances(self, instances):
        return [(instance.private_dns_name, "%s (%s)" % (instance.id,
                                                         instance.displayName))
                for instance in instances
                if instance.state == u'running']


if __name__ == "__main__":
    e2c = EC2Client("localhost")
    print e2c.get_instances()
