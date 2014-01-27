'''
Created on Aug 1, 2013

@author: sean
'''
from binstar_client.utils import jencode, compute_hash
from binstar_client.requests_ext import stream_multipart
import requests
from binstar_client.errors import BinstarError
class BuildMixin(object):
    '''
    Add build functionality to binstar client
    '''
    
    def submit_for_build(self, username, package, fd, instructions,
                         platforms=None,
                         envs=None,
                         engines=None,
                         callback=None):

        url = '%s/build/%s/%s/stage' % (self.domain, username, package)
        data = jencode(platforms=platforms, envs=envs, engines=engines, 
                       instructions=instructions)
        
        res = self.session.post(url, data=data)
        self._check_response(res)
        obj = res.json()

        s3url = obj['s3_url']
        s3data = obj['s3form_data']
        
        
        _hexmd5, b64md5, size = compute_hash(fd)
        s3data['Content-Length'] = size
        s3data['Content-MD5'] = b64md5

        data_stream, headers = stream_multipart(s3data, files={'file':(obj['basename'], fd)},
                                                callback=callback)

        s3res = requests.post(s3url, data=data_stream, verify=True, timeout=10 * 60 * 60, headers=headers)

        if s3res.status_code != 201:
            raise BinstarError('Error uploading to s3', s3res.status_code)

        url = '%s/build/%s/%s/commit/%s' % (self.domain, username, package, obj['build_id'])
        res = self.session.post(url, verify=True)
        self._check_response(res, [201])
        return obj['build_no']

    def builds(self, username, package):
        url = '%s/build/%s/%s' % (self.domain, username, package)
        res = self.session.get(url)
        self._check_response(res)
        return res.json()
    
    def stop_build(self, username, package, build_id):
        url = '%s/build/%s/%s/stop/%s' % (self.domain, username, package, build_id)
        res = self.session.post(url)
        self._check_response(res, [201])
        return
    
    def tail_build(self, username, package, build_id, limit='', after=''):
        url = '%s/build/%s/%s/tail/%s' % (self.domain, username, package, build_id)
        res = self.session.get(url, params={'limit':limit, 'after': after})
        self._check_response(res, [200])
        return res.json()



