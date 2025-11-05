# -*- coding: utf-8 -*-
import json
from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models


class SMS:
    def __init__(self, access_key_id, access_key_secret):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret

    def create_client(self):
        """
        使用AK&SK初始化账号Client
        @param access_key_id:
        @param access_key_secret:
        @return: Client
        @throws Exception
        """
        config = open_api_models.Config(
            # 您的AccessKey ID,
            access_key_id=self.access_key_id,
            # 您的AccessKey Secret,
            access_key_secret=self.access_key_secret
        )
        # 访问的域名
        config.endpoint = f'dysmsapi.aliyuncs.com'
        return Dysmsapi20170525Client(config)

    def send(self, template_code, template_param, sign_name, phone):
        """
        发送短信
        :param template_code: 短信模板ID
        :param template_param_json: 短信模板变量字典
        :param sign_name: 短信签名
        :param phone: 手机号码
        :return:
        """
        client = self.create_client()
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
            sign_name=sign_name,
            template_code=template_code,
            phone_numbers=phone,
            template_param=json.dumps(template_param)
        )
        resp = client.send_sms(send_sms_request)
        resp_dict = resp.to_map()

        return resp_dict


def send(access_key_id, access_key_secret, template_code, template_param, sign_name, phone):
    """
    发送短信
    :return:
    """
    # 使用阿里云发送短信
    s1 = SMS(access_key_id, access_key_secret)
    r = s1.send(template_code, template_param, sign_name, phone)
    return r


if __name__ == '__main__':
    pass
