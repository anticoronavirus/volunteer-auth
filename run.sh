#!/bin/sh

cd src
uvicorn main:app $@
