#!/usr/bin/env python
import uvicorn,os,sys,logging
from pathlib import Path
from uvicorn import Config, Server
from uvicorn.supervisors import ChangeReload
from fastcore.script import *

import logging
class FilterPollingLogs(logging.Filter):
    def filter(self, record): return record.getMessage().find("/get_runni") == -1
logging.getLogger("uvicorn.access").addFilter(FilterPollingLogs())

base_dir = Path(__file__).parent.parent

def run(app, host="0.0.0.0", port=8080, log_level=logging.INFO, reload=False, **kw):
    config = Config( app, host=host, port=port, log_level=log_level, reload=reload, **kw)
    server = Server(config)
    if reload: server = ChangeReload(config, target=server.run, sockets=[config.bind_socket()])
    try: server.run()
    except KeyboardInterrupt: pass

@call_parse
def main(
    host:str=os.environ.get('HOST', '0.0.0.0'),  # Host to bind to
    port:int=int(os.environ.get('PORT', 5001)),  # Port to bind to
    reload:bool_arg=True  # Enable auto-reload on file changes
):
    "Run the SolveIt app server"
    run(
        "solveit.core:app", host=host, port=port,
        ws="websockets", ws_max_queue=64, ws_ping_interval=10.0, ws_ping_timeout=10.0,
        reload=reload, reload_dirs=[f"{base_dir}/solveit", f"{base_dir}/assets"] if reload else None
    )

