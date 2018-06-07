#!/usr/bin/env python
"""
Runs flask application in production or debug mode.
"""
import sys
from app import app

# set debug mode or production mode
params = {}
if len(sys.argv) > 1 and sys.argv[1] == "--debug":
    params["debug"] = True
else:
    params["host"] = "0.0.0.0"

app.run(**params)
