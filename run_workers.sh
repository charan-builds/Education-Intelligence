#!/usr/bin/env bash

celery -A app worker -Q critical --concurrency=4 --loglevel=info &
celery -A app worker -Q analytics --concurrency=2 --loglevel=info &
celery -A app worker -Q ai --concurrency=2 --loglevel=info &
celery -A app worker -Q ops --concurrency=1 --loglevel=info &
