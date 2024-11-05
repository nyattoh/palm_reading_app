import os

# Server Socket
bind = "0.0.0.0:5000"
workers = 1
worker_class = "sync"
timeout = 300

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
