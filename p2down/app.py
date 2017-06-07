import os
import sys
import datetime
import time
import redis
import zipstream

from collections import namedtuple
from operator import attrgetter
from babel.dates import format_timedelta
from slugify import slugify
from flask import Flask, Response, g, render_template, current_app
from flask.ext import assets


class BaseConfig:
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_DB = 0
    ROOT_DIR = "index"


class DebugConfig:
    DEBUG = True

CONFIG_ENVVAR = "P2DOWN_SETTINGS"  # Set this envvar to the path to your cfg


app = Flask(__name__)
app.config.from_object(BaseConfig)
app.config.from_envvar(CONFIG_ENVVAR, silent=True)
# The debug config is loaded at the end of this file, if it is run
# directly (name == main)


# Load assets (currently only the scss stylesheet)

env = assets.Environment(app)
env.load_path = [
    os.path.join(os.path.dirname(__file__), "assets")
]
style = assets.Bundle(
    "style.css"
)
env.register("style", style)



# Redis

@app.before_request
def connect_redis():
    c = current_app.config
    g.redis = redis.StrictRedis(host = c["REDIS_HOST"],
                                port = c["REDIS_PORT"],
                                db = c["REDIS_DB"])



# Path-ID correspondence
# Assigns each path to an unique ID and provides functions for getting
# an ID's path and vice-versa.


def path_id(path):
    """Get a unique id for a path. If there is none, it is created."""
    uid = g.redis.hget("p2down_path_id", path)
    if not uid:
        uid = g.redis.incr("p2down_id_counter")
        g.redis.hset("p2down_path_id", path, uid)
        g.redis.hset("p2down_id_path", uid, path)
    return int(uid)


def path_from_id(entry_id):
    """Get the path for an id or None, if the path isn't in the registry"""
    path = g.redis.hget("p2down_id_path", entry_id)
    return path.decode("utf-8") if path else None


def zip_dir(addr):
    """Generate a zipstream for a directory"""
    zf = zipstream.ZipFile(mode="w")

    # This function places the directory's content inside the zip in an
    # internal directory with the same name as the original folder, ra-
    # ther than directly at the root of the zip.
    zip_top_dir = addr.strip(os.path.sep).split(os.path.sep)[-1]

    for dir_path, subdirs, files in os.walk(addr):
        # Path relative to the zip's top directory
        rel_dir_path = os.path.relpath(dir_path, start=addr)
        for file_path in files:
            fs_path = os.path.join(dir_path, file_path)
            zip_path = os.path.join(zip_top_dir, rel_dir_path, file_path)
            zf.write(fs_path, zip_path)

    return zf


@app.route("/zip/<int:entry_id>/<string:slug>")
def serve_zip(entry_id, slug):
    """Respond with a zip for a directory"""
    path = path_from_id(entry_id)
    name = os.path.basename(path)
    slug = slugify(name)
    # Not using path_slug because a user could easily hijack it
    zf = zip_dir(path)
    r = Response(zf, mimetype="application/zip")
    r.headers["Content-Disposition"] = "attachment; filename={}.zip".format(slug)
    return r


def listdirs(path):
    """List all directories in a directory"""
    return [item for item in os.listdir(path)
            if os.path.isdir(os.path.join(path, item))]


Entry = namedtuple("Entry", ["name", "id", "mtime", "delta_ago", "slug"])


def dir_entries(top):
    """Generate a list of entries for a directory"""
    dirs = listdirs(top)
    entries = []
    for d in dirs:
        full_path = os.path.join(top, d)

        mtime = os.stat(full_path).st_mtime
        delta = datetime.timedelta(seconds=mtime - time.time())
        delta_ago = format_timedelta(delta, locale="en_US",
                                     add_direction=True)  # x ago/in x

        e = Entry(name=d, id=path_id(full_path), mtime=mtime,
                  delta_ago=delta_ago, slug=slugify(d))
        entries.append(e)
    return sorted(entries, key=attrgetter("mtime"), reverse=True)


@app.route("/")
def index():
    """Respond with the index page, listing all directories"""
    return render_template("index.html", entries=dir_entries(app.config['ROOT_DIR']))


# Debug mode: run this file directly
if __name__ == '__main__':
    if len(sys.argv) <= 1 or sys.argv[2] != "nodebug":
        print("WARNING: running this app in debug mode.")
        app.config.from_object(DebugConfig)
        # Loads from envvar once again, for it override the debug configs if needed
        app.config.from_envvar(CONFIG_ENVVAR, silent=True)
    app.run()
