import asyncio
import json
import logging
import os
import subprocess
import sys
import time
import traceback
import uuid
import shutil

import boto3
import wget
from TransportLayer.TransportLayer import TransportHelper

import helper

logger = logging.getLogger('HAProxy-service')


class Service:
    """

    """

    def __init__(self):
        """

        """
        self.boto3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_KEY'),
            aws_secret_access_key=os.getenv('AWS_SECRET')
        )

    @asyncio.coroutine
    def process_request(self, ha_proxy_message):
        """

        :param ha_proxy_message:
        :return:
        """
        ha_proxy_message = json.loads(ha_proxy_message["payload"])
        ha_proxy_message = ha_proxy_message["payload"]
        logger.info(ha_proxy_message)
        ssldomains_directory = '/etc/haproxy/'
        ssldomains_file = "ssldomains"
        ssldomains_full_path = ssldomains_directory + ssldomains_file
        is_data_to_written = True
        try:
            if str(ha_proxy_message['crtDomainName']) in open('/etc/haproxy/ssldomains').read():
                is_data_to_written = False

            with open(ssldomains_full_path, 'a+') as f:

                self.boto3_client.upload_file(
                    ssldomains_full_path,
                    os.getenv('BASE_BUCKET'),
                    "ssl/haproxy/%s" %ssldomains_file
                )

                crt_file_downloaded = wget.download(ha_proxy_message['crtFilePath'])
                key_file_downloaded = wget.download(ha_proxy_message['crtKeyFilePath'])
                ca_bundle_file_downloaded = wget.download(ha_proxy_message['crtCaBundlePath'])

                pem_base_file_name = "%s.pem"%(str(ha_proxy_message['crtDomainName']).replace(".","_"))
                pem_full_qualified_path = "/etc/ssl/certs/pems/%s"%pem_base_file_name

                cat_file_syntax = "awk '{print}' %s %s %s > %s" %(
                    str(crt_file_downloaded),
                    str(key_file_downloaded),
                    str(ca_bundle_file_downloaded),
                    pem_full_qualified_path
                )
                logger.info("Creating PEM file for [%s]"%str(ha_proxy_message['crtDomainName']))
                logger.debug(cat_file_syntax)

                os.system(cat_file_syntax)
                os.system("rm " + str(crt_file_downloaded))
                os.system("rm " + str(key_file_downloaded))
                os.system("rm " + str(ca_bundle_file_downloaded))

                logger.info("Created PEM File [%s]"%pem_full_qualified_path)
                s3_path = "ssl/certificates/domains/%s/%s" %(str(ha_proxy_message['brandId']), pem_base_file_name)

                logger.info("Uploading PEM file [ %s ]"%s3_path)
                self.boto3_client.upload_file(
                    "/etc/ssl/certs/pems/%s" %str(pem_base_file_name),
                    os.getenv('BASE_BUCKET'),
                    s3_path)

                time.sleep(2)
                pem_file_s3_path = "%s%s/%s"%(os.getenv("S3_BASE_PATH"),os.getenv("BASE_BUCKET"),s3_path)
                os.system("sudo chmod 700 " + str(pem_full_qualified_path))
                os.system("service haproxy reload")

                time.sleep(3)

                successful_ha_proxy_meta = {
                    "domainName": ha_proxy_message['crtDomainName'],
                    "haProxyRestarted": True,
                    "crtPemFilePath": pem_file_s3_path,
                    "haProxyIp": helper.get_private_ip(),
                    "brandCertificateId": ha_proxy_message["brandCertificateId"],
                    "haProxyGroupType": ha_proxy_message['crtDomainType']
                }

                publishing_id = str(uuid.uuid4())
                logger.debug(successful_ha_proxy_meta)
                logger.info("publishing to the topic " + str(publishing_id) + " ha proxy update topic "
                            + os.getenv("HAPROXYUPDATE_TOPIC"))
                if is_data_to_written:
                    data_to_write = str(ha_proxy_message['crtDomainName']) + "\n"
                    f.write(data_to_write)
                    f.close()
                logger.info("SSL Save [True] %s "%ha_proxy_message['crtDomainName'])
                yield from TransportHelper.publish(successful_ha_proxy_meta, "UPDATE", publishing_id,
                                                   os.getenv("HAPROXYUPDATE_TOPIC"))

        except Exception:
            ex_type, ex, tb = sys.exc_info()
            logger.exception("SSL Save [False] %s ErrorTrace: %s"%(ha_proxy_message['crtDomainName'],ex),exc_info=True)
            traceback.print_tb(tb)
            raise Exception(tb)

    @asyncio.coroutine
    def process_challenge_request(self, challenge_message):
        """

        :param challenge_message:
        :return:
        """
        challenge_message = json.loads(challenge_message["payload"])
        challenge_message = challenge_message["payload"]
        logger.info(challenge_message)
        try:
            challenge_file_downloaded = wget.download(challenge_message['challengeFilePath'])
            shutil.move(challenge_file_downloaded, "/.well-known/acme-challenge/%s" %challenge_file_downloaded)
            logger.info("SSL Challenge Upload [True] %s "%challenge_message['brandId'])
        except Exception:
            ex_type, ex, tb = sys.exc_info()
            logger.exception("SSL Challenge Upload [False] %s ErrorTrace: %s"%(challenge_message['brandId'],ex),exc_info=True)
            traceback.print_tb(tb)
            raise Exception(tb)

    @asyncio.coroutine
    def process_ssl_confirmation(self, ssl_confirmation_message):
        """

        :param ssl_confirmation_message:
        :return:
        """
        ssl_confirmation_message = json.loads(ssl_confirmation_message["payload"])
        ssl_confirmation_message = ssl_confirmation_message["payload"]
        logger.info(ssl_confirmation_message)
        ha_proxy_directory = '/etc/haproxy/'
        ssldomains_confirmation_file = "ssldomains_confirmed"
        ssldomains_confirmation_full_path = ha_proxy_directory + ssldomains_confirmation_file
        is_data_to_written = True
        try:
            if str(ssl_confirmation_message['domainName']) in open('/etc/haproxy/ssldomains').read():
                if str(ssl_confirmation_message['domainName']) in open('/etc/haproxy/ssldomains_confirmed').read():
                    is_data_to_written = False

                with open(ssldomains_confirmation_full_path, 'a+') as f:
                    if is_data_to_written:
                        data_to_write = str(ssl_confirmation_message['domainName']) + "\n"
                        f.write(data_to_write)
                        f.close()
                    os.system("service haproxy reload")
                    logger.debug("Reloaded HAProxy")
                logger.info("SSL Confirmation[True] %s "%str(ssl_confirmation_message['domainName']))
            else:
                logger.info("SSL Confirmation[False] %s [trying to confirm SSL before process save request]"%str(ssl_confirmation_message['domainName']))
        except Exception:
            ex_type, ex, tb = sys.exc_info()
            logger.exception(ex, exc_info=True)
            traceback.print_tb(tb)
            raise Exception(tb)
