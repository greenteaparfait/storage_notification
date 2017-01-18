"""Notification handling Client to operate on bucket and files in Google Cloud Storage."""

import json
import logging
import os
import cloudstorage as gcs
import webapp2
from google.appengine.api import app_identity

class MainPage(webapp2.RequestHandler):
  """Process notification events."""
  def get(self):
    logging.info("Get request to notification page.")
    self.response.write("Welcome to the notification app Ver.4.")

  def post(self):  # pylint: disable-msg=C6409
    """Process the notification event.

    This method is invoked when the notification channel is first created with
    a sync event, and then subsequently every time an object is added to the
    bucket, updated (both content and metadata) or removed. It records the
    notification message in the log.
    """
    logging.debug(
        '%s\n\n%s',
        '\n'.join(['%s: %s' % x for x in self.request.headers.iteritems()]),
        self.request.body)

    if 'X-Goog-Resource-State' in self.request.headers:
      resource_state = self.request.headers['X-Goog-Resource-State']
      if resource_state == 'sync':
        logging.info('Sync message received.')
      else:
        an_object = json.loads(self.request.body)
        bucket = an_object['bucket']
        object_name = an_object['name']
        logging.info('%s/%s %s', bucket, object_name, resource_state)
    
    self.response.headers['Content-Type'] = 'text/plain'
    self.response.write('GCS Notification Application running from Version: ' + os.environ['CURRENT_VERSION_ID'] + '\n')
    self.response.write('Using bucket: ' + bucket + ' and file: ' + object_name +  '\n\n')

    bucket_path = '/' + bucket
    file_path = bucket_path + '/' + object_name
    self.tmp_filenames_to_clean_up = []
    try:
       self.read_file(filename)
       self.response.write('\n\n')
    except Exception, e:
       logging.exception(e)
       self.delete_files()
       self.response.write('\n\nThere was an error running the demo! Please check the logs for more details.\n')               
    else:
       self.delete_files()
       self.response.write('\n\nThe demo ran successfully!\n') 
              
#[START read]
  def read_file(self, filename):
    self.response.write('Reading file content:\n')
    gcs_file = gcs.open(filename)
    self.response.write(gcs_file.read())
    gcs_file.close()
    self.tmp_filenames_to_clean_up.append(filename)
#[END read]

#[START delete_files]
  def delete_files(self):
    self.response.write('Deleting files...\n')
    for filename in self.tmp_filenames_to_clean_up:
      self.response.write('Deleting file %s\n' % filename)
      try:
        gcs.delete(filename)
      except gcs.NotFoundError:
        pass
#[END delete_files]

app = webapp2.WSGIApplication([('/', MainPage)], debug=True)