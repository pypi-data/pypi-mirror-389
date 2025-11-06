# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
方正证券量化数据API接口 
Created on 2020/06/20
@author: Tushare
@group : https://tushare.pro
"""

import pandas as pd
import json
from functools import partial
import requests
from .util.protobuf.funcs import protobuf_parse


class DataApi:

    __token = ''
    __http_url = 'http://datacubeapi.foundersc.com'

    def __init__(self, token, timeout=50):
        """
        Parameters
        ----------
        token: str
            API接口TOKEN，用于用户认证
        """
        self.__token = token
        self.__timeout = timeout

    def query(self, api_name, fields='', **kwargs):
        req_params = {
            'api_name': api_name,
            'token': self.__token,
            'params': kwargs,
            'fields': fields
        }

        res = requests.post(self.__http_url, json=req_params, timeout=self.__timeout, headers={
            'Connection': 'close',
            'Accept': 'application/x-protobuf'
        })
        if res.status_code != 200:
            raise Exception(res.content)
        if 'application/x-protobuf' in res.headers['content-type']:
            result = protobuf_parse(res.content)
            if result['code'] != 0:
                raise Exception(result['msg'])
            df = result['data']

        else:
            result = json.loads(res.text)
            if result['code'] != 0:
                raise Exception(result['msg'])
            data = result.get('data')
            if data:
                columns = data['fields']
                items = data['items']
                df = pd.DataFrame(items, columns=columns)
            else:
                df = pd.DataFrame()
        return df

    def __getattr__(self, name):
        return partial(self.query, name)
