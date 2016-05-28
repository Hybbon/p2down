# p2down: minimal directory download facility, improved

## What's this?

This is a very simple Flask+Redis based webapp which lists the directories in a root directory and allows clients to download the listed directories entirely in zip files. These zips are created on-the-fly and streamed directly to the client via [python-zipstream](https://github.com/allanlei/python-zipstream).

The way this works means no extra disk space should be needed, although it comes at a possible cost of memory and processing power, due to the fact that these zips are generated every time a request is made. This may not be optimal for your use case, but it's perfect for me, given how clogged my seedbox has been these days.

By the way, I made a point of making this pretty simple. The main file for this is only 151 lines long, and I kept most of the functionality inside of it. I hope it's still readable.

## Quickstart

You'll need Python 3+, pip and a Redis server running, as well as a directory with directories to be served. It's also recommended that you have a virtual environment to install the required packages, but not strictly required, if you don't mind making a mess of your global Python install.

First, install the (not that many) required packages:

```
cd p2down
pip install -r requirements.txt
```

Then, make a symbolic link to the indexed directory:

```
ln -s /path/to/your/directory index
```

If your Redis server is at localhost at the default port with no password, you're set (Otherwise, check the next section of this readme). Run p2down in debug mode by directly executing `app.py` to make sure everything is fine:

```
python p2down/app.py
```

Finally, run it in production mode through your favorite Python WSGI server. Here's how I do it using gunicorn:

```
gunicorn -w 4 p2down:app
```

If you want to run it directly from `app.py` in production mode (which I wouldn't recommend), you can set the first command-line argument to `nodebug`:

```
python p2down/app.py nodebug
```


## Not-so-quick start

Ok, you actually need to configure something, I understand. Well, then. If you're feeling really lazy, just go ahead and edit `app.py`, nobody's looking at you. Of course, that's not the only way to do it: you can also load a provided config file by setting the environment variable `P2DOWN_SETTINGS` to its path:

*my_config_file.cfg*
```
REDIS_HOST = "some_other_host"
ROOT_DIR = "/absolute/path/for/a/change"
```

```
P2DOWN_SETTINGS=/absolute/path/to/my_config_file.cfg gunicorn -w 4 p2down:app
```

Or, if you're a fancy [fish](http://fishshell.com/) user like me,

```
set -x P2DOWN_SETTINGS /absolute/path/to/my_config_file.cfg
gunicorn -w 4 p2down:app
```

## License

The MIT License (MIT)

Copyright (c) 2016 Victor Diniz.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
