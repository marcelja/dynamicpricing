from.PricewarsBaseApi import PricewarsBaseApi


class KafkaApi(PricewarsBaseApi):
    def __init__(self, host='http://vm-mpws2016hp1-05.eaalab.hpi.uni-potsdam.de:8001', debug=False):
        PricewarsBaseApi.__init__(self, host=host, debug=debug)

    def _request_data_export(self, topic):
        r = self.request('get', 'export/data/{:s}'.format(topic))
        if r and (r.status_code < 100 or r.status_code >= 300 or not r.json()):
            return None
        url = r.json()['url']
        return url

    def download_csv_for_topic(self, topic, local_filename):
        url = self._request_data_export(topic)
        r = self.request('get', url, stream=True)
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024): 
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    #f.flush() commented by recommendation from J.F.Sebastian
        return True

    def request_csv_export_for_topic(self, topic):
        url = self._request_data_export(topic)
        if not url:
            return ''
        return '{:s}/{:s}'.format(self.host, url)
