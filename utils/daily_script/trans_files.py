import shlex
import paramiko
import sys
import argparse
from subprocess import PIPE, Popen

class SSHConnection(object):
    def __init__(self, host, username, password, port=22):
        """Initialize and setup connection"""
        self.sftp = None
        self.sftp_open = False
        
        # open SSH Transport stream
        self.transport = paramiko.Transport((host, port))
        
        self.transport.connect(username=username, password=password)
        
    def _openSFTPConnection(self):
        """
        Opens an SFTP connection if not already open
        """
        if not self.sftp_open:
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)
            self.sftp_open = True
    
    def get(self, remote_path, local_path=None):
        """
        Copies a file from the remote host to the local host.
        """
        self._openSFTPConnection()        
        self.sftp.get(remote_path, local_path)        
            
    def put(self, local_path, remote_path=None):
        """
        Copies a file from the local host to the remote host
        """
        self._openSFTPConnection()
        cbk, pbar = tqdmWrapViewBar(ascii=True, unit='b', unit_scale=True)
        self.sftp.put(local_path, remote_path, callback=cbk)
        
    def close(self):
        """
        Close SFTP connection and ssh connection
        """
        if self.sftp_open:
            self.sftp.close()
            self.sftp_open = False
        self.transport.close()
        


def run_command(command):
    process = Popen(shlex.split(command), stdout=PIPE)
    while True:
        output = process.stdout.readline().rstrip().decode('utf-8')
        if output == '' and process.poll() is not None:
            break
        print(output)
    rc = process.poll()
    return rc

def viewBar(a,b):
    res = a/int(b)*100
    sys.stdout.write('\rComplete precent: %.2f %%' % (res))
    sys.stdout.flush()
    
def tqdmWrapViewBar(*args, **kwargs):
    try:
        from tqdm import tqdm
    except ImportError:
        
        # tqdm not installed - construct and return dummy/basic versions
        class Foo():
            @classmethod
            def close(*c):
                pass
        return viewBar, Foo
    else:
        pbar = tqdm(*args, **kwargs)  # make a progressbar
        last = [0]  # last known iteration, start at 0
        def viewBar2(a, b):
            pbar.total = int(b)
            pbar.update(int(a - last[0]))  # update pbar with increment
            last[0] = a  # update last known iteration
        return viewBar2, pbar  # return callback, tqdmInstance

# host = "172.17.29.29"
# username = "yangkun"
# pw = "1"

parser = argparse.ArgumentParser('compress and trans file', add_help=False)
parser.add_argument("--host", "--h", default="10.145.181.52",  type=str, help="host ip")
parser.add_argument("--user", "--n", default="yangkun", type=str, help="ssh user")
parser.add_argument("--password", "--p", default="1", type=str, help="ssh password")
parser.add_argument("--path", type=str, help="Compression path", required=True)
parser.add_argument("--dist", type=str, help="dist remote", required=True)

pass_args = parser.parse_args()
host = pass_args.host
user= pass_args.user
password = pass_args.password
path = pass_args.path
dist = pass_args.dist


print('Current pass argument: {}'.format({'host': host, 'user': user, 'password': password, 'origin': path, 'drydist_run': dist}))

# origin = '/opt/dataset/gptj/6b/saved_results/best_model.pt'
# dst = '/home/yangkun/best_model.pt'

command_text = "sudo tar --exclude='.git' -zcvf {0}.tar.gz --absolute-names {1}".format(path.split("/")[-1], path)
print(command_text)
run_command(command_text)

# ssh = SSHConnection(host, user, password)
# ssh.put(path, dist)
# ssh.close()