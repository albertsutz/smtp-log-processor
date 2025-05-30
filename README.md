# smtp-log-processor
Processing logs given by Postfix and sending to Postgresql

# Details
- Python 3.10.13 is used when developing this. However, older or newer version should still be possible to use.

# How to use
1. configure the `.env` file to the proper values. It should be okay to use as is.

2. install the requirements via `pip install -r requirements.txt`

3. [OPTIONAL] create a sample log from postfix. There is a script called `stream_creator.py` that will simulate postfix log creation continuously. (1 sets of message every 1 second) `python stream_creator.py`

4. create the directories. for example, `input`, `internal` and `logstash_ingest_data` (if following the default environment variables)

5. run `log_processor.py` to start the aggregation process. The consolidated log file will be created.

# Example of postfix log
```
May 30 14:18:06 mailserver1 postfix/smtpd[2140]: 28C0738B99F: client=webapp.local[192.168.1.10]

May 30 14:18:06 mailserver1 postfix/cleanup[2635]: 28C0738B99F: header Subject: Email Delivery From A

May 30 14:18:06 mailserver1 postfix/cleanup[5727]: 28C0738B99F: message-id=<28c0738b99f@example.com>

May 30 14:18:06 mailserver1 postfix/qmgr[6379]: 28C0738B99F: from=<noreply@example.com>, size=1182, nrcpt=1 (queue active)

May 30 14:18:06 mailserver1 postfix/smtp[5264]: 28C0738B99F: to=<user1@outlook.com>, relay=outlook-com.olc.protection.outlook.com[40.101.50.1]:25, delay=2.9, delays=0.07/0.02/0.3/2.57, dsn=2.0.0, status=sent (250 2.0.0 OK)

May 30 14:18:06 mailserver1 postfix/qmgr[8486]: 28C0738B99F: removed
```

# Example of consolidated log
```
{
  "postfix_id": "28C0738B99F",
  "postfix_hostname": "mailserver1",
  "subject": "Email Delivery From A",
  "message_id": "28c0738b99f@example.com",
  "status": "sent",
  "from": "noreply@example.com",
  "to": "user1@outlook.com",
  "relay": "outlook-com.olc.protection.outlook.com[40.101.50.1]:25",
  "size": "1182",
  "timestamp": "May 30 14:18:06",
  "status_message": "250 2.0.0 OK"
}
```