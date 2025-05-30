from datetime import datetime
import random
import time
from typing import TextIO, List

FILE_PATH = "input/sample_mail.log"

POSTFIX_CHAR = ["A", "B", "C", "D", "E", "F", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
SAMPLE_ENTRIES = [
    {
        "msg_id": "",
        "to": "user1@outlook.com",
        "status": "sent",
        "response": "250 2.0.0 OK"
    },
    {
        "msg_id": "",
        "to": "user2@fullmailbox.com",
        "status": "bounced",
        "response": "552 5.2.2 user2@fullmailbox.com Mailbox full (in reply to RCPT TO command)"
    },
    {
        "msg_id": "",
        "to": "user3@temporaryerror.com",
        "status": "deferred",
        "response": "450 4.2.0 Try again later (in reply to RCPT TO command)"
    }
]

SAMPLE_SUBJECT = ["Email Delivery From A", "Email Delivery From B", "Email Delivery From C", "Email Delivery From D"]


def gen_random_postfix_id() -> str:
    answer: str = ""
    for i in range(11):
        answer += POSTFIX_CHAR[random.randint(0, 15)]
    return answer

def gen_log(timestamp, process, msg_id, content) -> str:
    return f"{timestamp} mailserver1 postfix/{process}[{random.randint(1000,9999)}]: {msg_id}: {content}"

def generate_log_from_entry(entry) -> List[str]:
    ts = datetime.now().strftime('%b %d %H:%M:%S')
    log_lines = []
    log_lines.append(gen_log(ts, "smtpd", entry["msg_id"], f"client=webapp.local[192.168.1.10]"))
    log_lines.append(gen_log(ts, "cleanup", entry["msg_id"], f"header Subject: {SAMPLE_SUBJECT[random.randint(0,3)]}"))
    log_lines.append(gen_log(ts, "cleanup", entry["msg_id"], f"message-id=<{entry['msg_id'].lower()}@example.com>"))
    log_lines.append(gen_log(ts, "qmgr", entry["msg_id"], f"from=<noreply@example.com>, size={random.randint(900, 1200)}, nrcpt=1 (queue active)"))
    
    delay = round(random.uniform(1.0, 3.5), 1)
    delays = f"{round(random.uniform(0.01, 0.1), 2)}/0.02/0.3/{round(delay - 0.33, 2)}"
    
    if entry["status"] == "sent":
        log_lines.append(gen_log(ts, "smtp", entry["msg_id"],
            f"to=<{entry['to']}>, relay=outlook-com.olc.protection.outlook.com[40.101.50.1]:25, delay={delay}, delays={delays}, dsn=2.0.0, status=sent ({entry['response']})"))
    elif entry["status"] == "bounced":
        log_lines.append(gen_log(ts, "smtp", entry["msg_id"],
            f"to=<{entry['to']}>, relay=mail.fullmailbox.com[203.0.113.10]:25, delay={delay}, delays={delays}, dsn=5.2.2, status=bounced (host mail.fullmailbox.com[203.0.113.10] said: {entry['response']})"))
    elif entry["status"] == "deferred":
        log_lines.append(gen_log(ts, "smtp", entry["msg_id"],
            f"to=<{entry['to']}>, relay=mail.temporaryerror.com[198.51.100.20]:25, delay={delay}, delays={delays}, dsn=4.2.0, status=deferred (host mail.temporaryerror.com[198.51.100.20] said: {entry['response']})"))
    log_lines.append(gen_log(ts, "qmgr", entry["msg_id"], "removed"))
    
    return log_lines

def generate_sample_log(file_handler: TextIO): 
    random_int = random.randint(0, 9)
    if random_int <= 7:
        entry_id = 0
    elif random_int == 8:
        entry_id = 1
    else:
        entry_id = 2

    entry = SAMPLE_ENTRIES[entry_id]
    entry["msg_id"] = gen_random_postfix_id() 
    print(f"generating logs with ID: {entry['msg_id']} {entry['status']}", flush=True)
    
    log_lines = generate_log_from_entry(entry)
    for log_line in log_lines:
        file_handler.write(log_line + "\n")
        time.sleep(0.1)


if __name__ == "__main__":
    # Write to file
    with open(FILE_PATH, "a", buffering=1) as f:
        while True:
            generate_sample_log(f)
            time.sleep(1)