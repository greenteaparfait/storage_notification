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
    self.response.write("Welcome to the notification app Ver.5.")

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
        objectname = an_object['name']
        logging.info('Channel ID : %s Resource ID : %s', self.request.headers['X-Goog-Channel-Id'], self.request.headers['X-Goog-Resource-Id'])
        logging.info('%s/%s %s', bucket, objectname, resource_state)
        bucket_path = '/' + bucket
        filepath = bucket_path + '/' + objectname
        self.tmp_filenames_to_clean_up = []
        try:
          self.read_file(filepath)
        except Exception, e:
          logging.exception(e)
          #self.delete_files(filepath)
        else:
          self.delete_files(filepath)
          logging.info('file %s was deleted.', objectname)
              
#[START read]
  def read_file(self, filepath):
    gcs_file = gcs.open(filepath)
    #logging.info('file %s was read.', objectname)
    logging.info(gcs_file.read())    
    gcs_file.close()
    self.tmp_filenames_to_clean_up.append(filepath)
#[END read]

#[START delete_files]
  def delete_files(self, filepath):
    for filename in self.tmp_filenames_to_clean_up:
      try:
        gcs.delete(filepath)
      except gcs.NotFoundError:
        pass
#[END delete_files]

logging.getLogger().setLevel(logging.DEBUG)
app = webapp2.WSGIApplication([('/', MainPage)], debug=True)