#!/bin/sh

# Puerto dinámico (Azure proporciona PORT)
: "${PORT:=80}"

exec npm run preview -- --host 0.0.0.0 --port "$PORT"
