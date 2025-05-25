# syntax=docker/dockerfile:1
FROM postgres:latest
COPY startupSQL.sql /docker-entrypoint-initdb.d/
COPY /dataset/btcusd_1-min_data.csv /docker-entrypoint-initdb.d/
