from pygtail import Pygtail
import json
import re

LOGFILE_PATH = "sample_mail.log"

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
    # print(f"processing subject: {subject}")
    DB_EXAMPLE[postfix_id]["subject"] = subject

def process_message_id(postfix_id, content):
    message_id = content['message_id']
    # print(f"processing message_id: {message_id}")
    DB_EXAMPLE[postfix_id]["message_id"] = message_id

def process_status(postfix_id, content):
    status = content['status']
    # print(f"processing status: {status}")
    DB_EXAMPLE[postfix_id]["subject"] = status

def process_log_line(line:str):
    parsed_log = parse_log_line(line)
    postfix_id = parsed_log["postfix_id"]
    
    if postfix_id not in DB_EXAMPLE:
        DB_EXAMPLE[postfix_id] = {
            "postfix_id": postfix_id,
            "subject": "",
            "message_id": ""
        }
    if parsed_log["type"] == "header_subject":
        process_subject(postfix_id, parsed_log)
    elif parsed_log["type"] == "message_id":
        process_message_id(postfix_id, parsed_log)
    elif parsed_log["type"] == "delivery_status":
        process_status(postfix_id, parsed_log)

if __name__ == "__main__":
    with open(LOGFILE_PATH, "r") as f:
        for line in f:
            process_log_line(line)
    print(json.dumps(DB_EXAMPLE, indent=2))