import atexit
import json
import logging
import logging.handlers
import os
import re
import sys
import time
from subprocess import Popen

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask import Flask, jsonify, render_template, request, send_from_directory

from scoresheetgen import generate_from_file
from convert_to_sqbs import convert_to_sqbs
from utils import authorize_email, generate_filename, generate_filename_with_rounds, StreamLogger

GENERATION_SCHEDULE_INTERVAL = 15
CONVERSION_SCHEDULE_INTERVAL = 15
API_LIMIT = 90
EPOCH_LENGTH = 110
MAX_ROOMS = 35
MAX_ROUNDS = 16
MAX_EMAIL_LENGTH = 254
CONVERSION_REPEAT_DELAY = 5
api_calls_in_epoch = 0
api_calls_from_last = 0
last_epoch_start = int(time.time())

app = Flask("Scoresheet Generator")

queue = []
sqbs_queue = []

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

fileHandler = logging.handlers.TimedRotatingFileHandler("logs/log", when='D', backupCount=5)
formatter = logging.Formatter(style="%", fmt="%(asctime)s - %(levelname)s - %(message)s")
fileHandler.setFormatter(formatter)
log.addHandler(fileHandler)

sl = StreamLogger(log, logging.ERROR)
sys.stderr = sl

def schedule_generation():
    global queue
    global last_epoch_start
    global api_calls_from_last
    global api_calls_in_epoch

    if int(time.time()) - last_epoch_start > EPOCH_LENGTH:
        api_calls_in_epoch = 0
        last_epoch_start = int(time.time())

    for i, (filename, num_api_calls) in enumerate(queue):
        if api_calls_in_epoch + num_api_calls < API_LIMIT:
            api_calls_in_epoch += num_api_calls
            api_calls_from_last = num_api_calls
            queue.pop(i)

            log.info(f"[{filename}] -- Generating scoresheets")
            try:
                generate_from_file(os.path.join("generation_configs", filename))
            except Exception as e:
                log.error(f"[{filename}] -- {repr(e)}")
            log.info(f"[{filename}] -- Finished generating scoresheets")
        else:
            log.info(f"[{filename}] -- SKIPPED {num_api_calls} required with {api_calls_in_epoch} calls leftover and limit of {API_LIMIT}")

            break


def schedule_sqbs_conversion():
    if len(sqbs_queue) > 0:
        filename, round_min, round_max, tossups_per_game = sqbs_queue.pop(0)

        log.info(f"[{filename}] -- Running SQBS job")
        convert_to_sqbs(filename, round_min, round_max, tossups_per_game)
        log.info(f"[{filename}] -- Finished running SQBS job")


def validate_create_args(args):
    # will modify in place
    err_dict = {
        "missing": "Missing {}.",
        "email": "Invalid email.",
        "unauthorized": "Your email isn't authorized! Please contact Alistair if you're directing a (legitimate) tournament and would like to be authorized.",
        "rooms": "Invalid number of rooms. You may have between 1 and {} rooms.".format(MAX_ROOMS),
        "duplicate_room_names": "You have a duplicate room name."
    }

    # check if any required arguments aren't present (after client-side validation)
    for check_var in ("tourney_name", "email", "rooms", "tossups_per_game"):
        if check_var not in args:
            return {"error": err_dict["missing"].format(check_var)}

    # check there are enough rooms and they're unique
    if isinstance(args["rooms"], list):
        args["rooms"] = [i.strip()[:25] for i in args["rooms"] if len(i) > 0]
    elif args["rooms"].count(",") > 0:
        args["rooms"] = [i.strip()[:25]
                         for i in args["rooms"].split(",") if len(i.strip()) > 0]
    else:
        args["rooms"] = [i.strip()[:25]
                         for i in args["rooms"].split("\n") if len(i.strip()) > 0]

    if len(set(args["rooms"])) != len(args["rooms"]):
        return {"error": err_dict["duplicate_room_names"]}

    if len(args["rooms"]) > MAX_ROOMS or len(args["rooms"]) <= 0:
        return {"error": err_dict["rooms"]}

    # sketchy email validation but whatever
    email_match = re.match(
        r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', args["email"])
    if(not email_match or len(email_match.groups()[0]) > MAX_EMAIL_LENGTH):
        return {"error": err_dict["email"]}

    args["email"] = email_match.groups()[0]

    # check if email is authorized

    if not authorize_email(args["email"]):
        return {"error": err_dict["unauthorized"]}

    return False


def validate_convert_args(args):
    err_dict = {
        "missing": "Missing {}.",
        "unauthorized": "Your email is invalid or unauthorized! Make sure this is the same email you used to create your scoresheet.",
        "rounds_min": "First round number invalid - it must be a number no greater than {}.".format(MAX_ROUNDS),
        "rounds_max": "Last round number invalid - it must be a number no greater than {}.".format(MAX_ROUNDS),
        "min_lt_max": "First round number can't be greater than last round number."
    }

    # check if any required arguments aren't present (after client-side validation)
    for check_var in ("email", "rounds_min", "rounds_max"):
        if check_var not in args:
            return {"error": err_dict["missing"].format(check_var)}

    # validate against pre-approved emails
    if not authorize_email(args["email"]):
        return {"error": err_dict["unauthorized"]}

    # check round min and round max are integers, in the correct range, and min < max
    try:
        args["rounds_min"] = int(args["rounds_min"])
        assert args["rounds_min"] <= MAX_ROUNDS and args["rounds_min"] > 0
    except:
        return {"error": err_dict["rounds_min"]}
    try:
        args["rounds_max"] = int(args["rounds_max"])
        assert args["rounds_max"] <= MAX_ROOMS and args["rounds_max"] > 0
    except:
        return {"error": err_dict["rounds_max"]}

    try:
        assert args["rounds_min"] <= args["rounds_max"]
    except:
        return {"error": err_dict["min_lt_max"]}

    # if user has created sheets before, there'll be a sqbs config for it
    if os.path.isfile(os.path.join("sqbs_configs", generate_filename(args["email"], ".json"))):
        return False

    return {"error": err_dict["unauthorized"]}


@app.route("/")
def serve_index():
    return render_template("info.html")


@app.route("/about")
def serve_about():
    return render_template("about.html")


@app.route("/create")
def create_index():
    return render_template("create_form.html")


@app.route("/create/submit")
def create():
    global last_epoch_start
    req = dict((i, j.strip())
               for i, j in zip(request.args.keys(), request.args.values()))

    invalid = validate_create_args(req)

    if invalid:
        return jsonify(invalid)

    try:
        invalid = validate_create_args(req)

        if invalid:
            return jsonify(invalid)
    except Exception as e:
        print(repr(e))
        return {"error": "Invalid arguments"}

    filename = generate_filename(req["email"], ".json")
    with open(os.path.join("generation_configs", filename), "w") as f:
        json.dump(req, f)

    if len(queue) == 0:
        last_epoch_start = int(time.time())
    queue.append((filename, len(req["rooms"]) * 2 + 1))

    log.info(f"[{filename}] -- adding to creation queue -- {queue}")

    return {"success": req["email"]}


@app.route("/convert")
def convert_index():
    return render_template("convert_form.html")


@app.route("/convert/submit")
def convert():
    req = dict((i, j.strip()) for i, j in zip(request.args.keys(), request.args.values()))

    invalid = validate_convert_args(req)
    if invalid:
        return json.dumps(invalid)

    filename = generate_filename(req["email"], ".json")
    sqbs_filename = generate_filename_with_rounds(req["email"], req["rounds_min"], req["rounds_max"], ".sqbs")
    full_sqbs_filename = os.path.join("sqbs_configs", filename)
    full_generation_filename = os.path.join("generation_configs", filename)

    d = {}
    with open(full_sqbs_filename) as f:
        d = json.load(f)

    if int(time.time()) - d["last_run"] < CONVERSION_REPEAT_DELAY:
        return json.dumps({"error": "Please wait at least {} seconds in between submitting sqbs conversion jobs".format(CONVERSION_REPEAT_DELAY + CONVERSION_SCHEDULE_INTERVAL)})

    for item in sqbs_queue:
        if item[0] == full_sqbs_filename:
            return json.dumps({"error": "You already have a job request for that aggregate sheet"})

    if not isinstance(req["rounds_min"], int) or not isinstance(req["rounds_max"], int):
        return json.dumps({"error": "Round numbers must be integers"})

    g = {}
    with open(full_generation_filename) as f:
        g = json.load(f)

    if "tossups_per_game" in g:
        tossups_per_game = int(g["tossups_per_game"])
    else:
        tossups_per_game = 20

    log.info(f"[{filename}] -- adding to SQBS queue -- {sqbs_queue}")
    sqbs_queue.append((full_sqbs_filename, int(req["rounds_min"]), int(req["rounds_max"]), tossups_per_game))
    with open(full_sqbs_filename, "w") as f:
        d["email"] = req["email"]
        json.dump(d, f)
    return json.dumps({"success": sqbs_filename})


@app.route("/sqbs/<path:filename>")
def serve_sqbs_file(filename):
    return send_from_directory("sqbs_files", filename)


scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(func=schedule_generation, trigger=IntervalTrigger(
    seconds=GENERATION_SCHEDULE_INTERVAL), replace_existing=True)
scheduler.add_job(func=schedule_sqbs_conversion, trigger=IntervalTrigger(
    seconds=GENERATION_SCHEDULE_INTERVAL), replace_existing=True)
atexit.register(scheduler.shutdown)

if __name__ == '__main__':
    # app must block or scheduler will not work in the background; i.e. run this file to actually run jobs
    # alternatively, run using "FLASK_APP=main.py venv/bin/python -m flask run" to not run jobs
    log.info("Starting up")
    app.run(host="0.0.0.0")
