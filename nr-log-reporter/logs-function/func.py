import io
import os
import gzip
import json
import requests
import logging
from fdk import response

# NR Logs endpoint URL and token to call the API endpoint.
# This is defined in the func.yaml file or on the OCI Function Environment Settings
# EU: https://log-api.eu.newrelic.com/log/v1
# US: https://log-api.newrelic.com/log/v1
nr_log_endpoint = os.getenv('NR_LOG_ENDPOINT', 'https://log-api.newrelic.com/log/v1')

# NR API Key for authentication.
# This is defined in the func.yaml file or on the OCI Function Environment Settings
nr_api_key = os.getenv('NR_INGEST_KEY', 'not-configured')

# NR API Key for authentication.
# This is defined in the func.yaml file or on the OCI Function Environment Settings
forward_to_nr = os.getenv('FORWARD_TO_NR', 'True')


# Set all registered loggers to the configured log_level
logging_level = os.getenv('LOGGING_LEVEL', 'INFO')
loggers = [logging.getLogger()] + [logging.getLogger(name) for name in logging.root.manager.loggerDict]
[logger.setLevel(logging.getLevelName(logging_level)) for logger in loggers]

def handler(ctx, data: io.BytesIO=None):
    if forward_to_nr is False:
        logging.getLogger().debug("Log Reporting is disabled - nothing sent")
        return

    if nr_api_key == 'not-configured':
        logging.getLogger().error("No API Key Configured - nothing sent")
        return

    try:
        # parse payload from request
        logs = json.loads(data.getvalue())

        for item in logs:
            send_to_nr(item)

    except (Exception, ValueError) as ex:
        logging.getLogger().info(str(ex))
        return

def compress_payload(payload: dict):
    try:
        return gzip.compress(json.dumps(payload).encode('utf-8'))
    except Exception as ex:
        logging.getLogger().error("Failed to compress payload", extra={'Exception': ex})
        return payload


def send_to_nr(body: dict):
    headers = {'Content-Type': 'application/json', 'Api-Key': nr_api_key}

    compressed_payload = compress_payload(payload=body)

    try:
        if isinstance(compressed_payload, bytes):
            headers['Content-Type'] = 'application/gzip'
            headers['Content-Encoding'] = 'gzip'
            resp = requests.post(nr_log_endpoint, data=compressed_payload, headers=headers)
        else:
            resp = requests.post(nr_log_endpoint, json=compressed_payload, headers=headers)

        # Possible New Relic API Error Response Codes
        if resp.status_code != 202:
            match resp.status_code:
                case 400:
                    logging.getLogger().error("400 - Structure of the request is invalid.")
                case 403:
                    logging.getLogger().error("403 - Authentication failure.")
                case 408:
                    logging.getLogger().error("408 - The request took too long to reach the endpoint.")
                case 411:
                    logging.getLogger().error("411 - The Content-Length header wasn’t included.")
                case 413:
                    logging.getLogger().error("413 - The payload was too big. Payloads must be under 1MB (10^6 bytes).")
                case 429:
                    logging.getLogger().error("429 - The request rate quota has been exceeded.")
                case _:
                    logging.getLogger().error('%s - Server Error, please retry.', resp.status_code)
            raise Exception ('Error posting to New Relic: {}'.format(str(resp.status_code)))
    except Exception as ex:
        logging.getLogger().exception(ex)


def local_test_mode(filename):
    """
    This routine reads a local json log file, compresses the payload, and forwards to New Relic.
    :param filename: cloud events json file exported from OCI Logging UI or CLI.
    :return: None
    """

    logging.getLogger().info("local testing started")

    with open(filename, 'r') as f:
        data = f.read()
        logs = json.loads(data)

        for log in logs:
            print(log)
            logging.getLogger().debug(json.dumps(log, indent=4))
            send_to_nr(log)

    logging.getLogger().info("local testing completed")


"""
Local Debugging
"""
if __name__ == "__main__":
    local_test_mode('oci-logs-example.json')
