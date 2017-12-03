#!/bin/bash -xe
##################################################################################
# outline
# $1:
# exit NORMAL:no error
# exit ABNORMAL END:-
##################################################################################
gunicorn -c env/deploy/production/gunicorn.conf.py \
        -k "geventwebsocket.gunicorn.workers.GeventWebSocketWorker" \
        nepenthes:app
