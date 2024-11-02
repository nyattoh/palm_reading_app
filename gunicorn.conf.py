import multiprocessing

# Server Socket
bind = "0.0.0.0:10000"  # Renderのデフォルトポート
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 300

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
