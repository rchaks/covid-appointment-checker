# covid-appointment-checker
A simple python script which checks for website messages
indicative of available appointments (pre-loaded with websites 
for NJ).

## Setup

_All commands should be executed from directory root_

### (Optional) Setup Python 3 Virtualenv

- Install [pip](https://pip.pypa.io/en/stable/) if not already installed
- Install [virtualenv](https://virtualenv.pypa.io/en/latest/) if desired for environment isolation
- Install [python 3.x](https://www.python.org/downloads/) if not already installed
  * Code tested with 3.8; but presumably any Python 3 version should work
- Create & activate virtualenv:
  ```
  virtualenv -p python3 venv
  source venv/bin/activate
  ```

### Install dependencies

```
pip install -r requirements.txt
```

### Set Twilio credentials as environment variables

> NOTE: you can just print messages to the screen if you don't want SMS texts to be sent.

You can create a [Twilio account](https://www.twilio.com/try-twilio) & use it
to send a SMS _to the phone number that you signed up with_ for free. Once you have 
an account, set these details as environment variables (see 
[API docs](https://www.twilio.com/docs/iam/test-credentials) for how to get these 
details):

```
# Add values from 
export TWILIO_ACCOUNT_SID=
export TWILIO_AUTH_TOKEN=
export TWILIO_PHONE_NUMBER=
# Should be the same number you signed up with if you're using the free account
export RECIPIENT_PHONE_NUMBER=
```   

### Choose websites to track 
The code is simplistic, it iterates over a set of webpages and, for each webpage:
 - gets the HTML content of the webpage
 - tries to match the corresponding `Message` to the contents. The `Message`
   object consists of a string (e.g. `All appointments currently are full.`) and
   a boolean value `should_exist` which tells the script whether the script should
   check for the existence of the string or lack thereof before deciding to 
   send a notification
 - right now the list of webpages is hardcoded on line 15 of 
   [check_for_available_appointments.py](check_for_available_appointments.py) 
   with the urls & corresponding messages for the websites taken from
   [NJVSS](https://covid19.nj.gov/pages/covid-19-vaccine-locations-for-eligible-recipients)
   for
     * Bergen County
     * Essex County
     * Passaic County
   > Feel free to modify this list in the code as needed 

### Run the script

```
python check_for_available_appointments.py --notification-type sms --recepient ${RECIPIENT_PHONE_NUMBER}
```

#### Schedule a cron job

You may wish to schedule this as a cron job. Here's a sample shell script which can be scheduled to
kick off the above command:

```
#!/bin/bash
set -eo pipefail

# Replace with git repo directory
GIT_DIR=~/workspaces/covid-appointment-checker

# Uncomment if using virtualenv
# source ${GIT_DIR}/venv/bin/activate

# Add values from https://www.twilio.com/docs/iam/test-credentials
export TWILIO_ACCOUNT_SID=
export TWILIO_AUTH_TOKEN=
export TWILIO_PHONE_NUMBER=
export RECIPIENT_PHONE_NUMBER=

python ${GIT_DIR}/check_for_available_appointments.py --notification-type sms --recepient ${RECIPIENT_PHONE_NUMBER}
```
