#!/bin/bash
# A script to generate .env if it's not present using .env.sample as template

ENV_PATH=".env"
SAMPLE_ENV_PATH=".env.sample"

if [ ! -f "$ENV_PATH" ]; then
    while IFS= read -r line; do
        processed_line=$(echo $line | perl -pe 's/\{\{(.+)\}\}/`$1`/ge')
        echo "$processed_line" >> $ENV_PATH
    done < "$SAMPLE_ENV_PATH"
    echo "Generated .env file from sample."
else
    echo ".env file already exists."
fi
