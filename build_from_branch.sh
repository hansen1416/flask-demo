#!/bin/bash
docker build -t hansen1416/coda_api_test https://github.com/hansen1416/coda.git#master:api

# docker run -itd --restart unless-stopped hansen1416/coda_api_test