from pygtail import Pygtail
import json, re, os, time, logging
from typing import TextIO
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler


# [TODO] make it robust (for restart)

# CHAT GPT for parsing. Please check again
log_patterns = [
    # 1. Client connection
    (r'(?P<postfix_id>[A-Z0-9]+): client=(?P<client_host>[\w\.-]+)\[(?P<client_ip>[\d\.]+)\]',
     "client_connection"),

    # 2. Subject header
    (r'(?P<postfix_id>[A-Z0-9]+): header Subject: (?P<subject>.+)',
     "header_subject"),

    # 3. Message ID
    (r'(?P<postfix_id>[A-Z0-9]+): message-id=<(?P<message_id>[^>]+)>',
     "message_id"),

    # 4. Message queued
    (r'(?P<postfix_id>[A-Z0-9]+): from=<(?P<from>[^>]+)>, size=(?P<size>\d+), nrcpt=(?P<nrcpt>\d+) \((?P<status>[^)]+)\)',
     "queue_message"),

    # 5. Delivery status
    (r'(?P<postfix_id>[A-Z0-9]+): to=<(?P<to>[^>]+)>, relay=(?P<relay>[^,]+), delay=(?P<delay>[\d\.]+), delays=(?P<delays>[^,]+), dsn=(?P<dsn>[\d\.]+), status=(?P<status>\w+) \((?P<status_message>.+)\)',
     "delivery_status"),

    # 6. Message removed
    (r'(?P<postfix_id>[A-Z0-9]+): removed',
     "message_removed"),
]

log_line_regex = re.compile(r'^(?P<timestamp>[A-Z][a-z]{2} \d{1,2} \d{2}:\d{2}:\d{2}) (?P<host>[\w\-\.]+) (?P<service>[\w\/\[\]\-]+): (?P<content>.+)$')

def parse_log_line(line):
    match = log_line_regex.match(line)
    if not match:
        return {"type": "unrecognized", "raw": line}

    base_info = match.groupdict()
    content = base_info.pop("content")

    for pattern, log_type in log_patterns:
        sub_match = re.match(pattern, content)
        if sub_match:
            data = {**base_info, **sub_match.groupdict(), "type": log_type}
            return data

    return {**base_info, "type": "unknown", "raw_content": content}

DB_EXAMPLE = {}

# the next 4 functions are necessary to handle processing and giving to DB
def process_subject(postfix_id, content):
    subject = content['subject']
    DB_EXAMPLE[postfix_id]["subject"] = subject

def process_message_id(postfix_id, content):
    message_id = content['message_id']
    DB_EXAMPLE[postfix_id]["message_id"] = message_id

def process_status(postfix_id, content):
    status = content['status']
    to_address = content["to"]
    relay = content["relay"]
    status_message = content["status_message"]
    timestamp = content["timestamp"]
    DB_EXAMPLE[postfix_id]["status"] = status
    DB_EXAMPLE[postfix_id]["to"] = to_address
    DB_EXAMPLE[postfix_id]["relay"] = relay
    DB_EXAMPLE[postfix_id]["status_message"] = status_message
    DB_EXAMPLE[postfix_id]["timestamp"] = timestamp

def process_queue_message(postfix_id, content):
    from_address = content["from"]
    email_size = content["size"]
    DB_EXAMPLE[postfix_id]["from"] = from_address
    DB_EXAMPLE[postfix_id]["size"] = email_size

def write_log(output_logger: logging.Logger, content):
    output_logger.info(json.dumps(content))
    # file_handler.write(json.dumps(content) + "\n")
    

def process_log_line(line:str, output_logger: logging.Logger):
    parsed_log = parse_log_line(line)
    log_type = parsed_log["type"]
    if log_type in ["client_connection", "message_removed"]:
        return
    
    postfix_id = parsed_log["postfix_id"]
    postfix_hostname = parsed_log["host"]
    
    if postfix_id not in DB_EXAMPLE:
        DB_EXAMPLE[postfix_id] = {
            "postfix_id": postfix_id,
            "postfix_hostname": postfix_hostname,
            "subject": "",
            "message_id": "",
            "status": "",
            "from": "",
            "to": "",
            "relay": "",
            "size": 0,
            "timestamp": ""
        }
    if log_type == "header_subject":
        process_subject(postfix_id, parsed_log)
    elif log_type == "message_id":
        process_message_id(postfix_id, parsed_log)
    elif log_type == "queue_message":
        process_queue_message(postfix_id, parsed_log)
    elif log_type == "delivery_status":
        process_status(postfix_id, parsed_log)
        write_log(output_logger, DB_EXAMPLE[postfix_id])
        DB_EXAMPLE.pop(postfix_id)
    

# this function is called when pygtail finished writing to the offset file
# this should so something along the lines of flushing to the database
def on_update_offset():
    pass

if __name__ == "__main__":  
    # load all the environment variables  
    load_dotenv()
    LOGFILE_INPUT_PATH = os.getenv("LOGFILE_INPUT_PATH") # source log
    PYGTAIL_OFFSET_PATH = os.getenv("PYGTAIL_OFFSET_PATH")
    CONSOLIDATED_LOG_PATH = os.getenv("CONSOLIDATED_LOG_PATH") # destination consolidated log
    CONSOLIDATED_LOG_SIZE = int(os.getenv("CONSOLIDATED_LOG_SIZE"))
    CONSOLIDATED_LOG_BACKUP_COUNT = int(os.getenv("CONSOLIDATED_LOG_BACKUP_COUNT"))

    # file handler
    handler = RotatingFileHandler(filename=CONSOLIDATED_LOG_PATH, maxBytes=CONSOLIDATED_LOG_SIZE, backupCount=CONSOLIDATED_LOG_BACKUP_COUNT)

    # log handler
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    with open(CONSOLIDATED_LOG_PATH, "a", buffering=1) as consolidated_log_handler:
        while True:
            for line in Pygtail(filename=LOGFILE_INPUT_PATH, offset_file=PYGTAIL_OFFSET_PATH):
                process_log_line(line, logger)
            time.sleep(1)
