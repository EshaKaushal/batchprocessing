#!/bin/bash

# Make a copy of our secrets template
cp secret_template.json secret.json

# Encode our GCS creds
GCS_ENCODED=$(cat $GOOGLE_APPLICATION_CREDENTIALS | base64 -w 0)

# Substitute those creds into our secrets file
sed -i -e 's|'REPLACE_GCS_CREDS'|'"$GCS_ENCODED"'|g' secret.json

# Create our secret
pachctl create secret -f secret.json
