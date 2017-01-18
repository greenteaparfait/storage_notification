#!/usr/bin/python

import boto
import gcs_oauth2_boto_plugin
import os
import shutil
import StringIO
import tempfile
import time

# URI scheme for Cloud Storage.
GOOGLE_STORAGE = 'gs'
# URI scheme for accessing local files.
LOCAL_FILE = 'file'

project_id = 'testcloudstorage-1470232940384'
header_values = {"x-goog-project-id": project_id}

# Fallback logic. In https://console.cloud.google.com/
# under Credentials, create a new client ID for an installed application.
# Required only if you have not configured client ID/secret in
# the .boto file or as environment variables.
CLIENT_ID = '931890424032-f0c002pnlnvf6guurutfan0mjo05qop4.apps.googleusercontent.com'
CLIENT_SECRET = 'U3TeUjePqH7jhbVAGQPsL7Nm'
gcs_oauth2_boto_plugin.SetFallbackClientIdAndSecret(CLIENT_ID, CLIENT_SECRET)


uri = boto.storage_uri('', GOOGLE_STORAGE)
# If the default project is defined, call get_all_buckets() without arguments.
#for bucket in uri.get_all_buckets(headers=header_values):
#  print bucket.name
    
uri = boto.storage_uri("testcloudbucket", GOOGLE_STORAGE)
for obj in uri.get_bucket():
  print '%s://%s/%s' % (uri.scheme, uri.bucket_name, obj.name)
  print '  "%s"' % obj.get_contents_as_string()