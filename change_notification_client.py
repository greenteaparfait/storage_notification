"""Notification handling Client to operate on bucket and files in Google Cloud Storage."""
import StringIO
import json
import logging
import os
import cloudstorage as gcs
import webapp2
from google.appengine.api import app_identity
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import math
from google.appengine.api import taskqueue
from google.appengine.ext import ndb
import time
from google.appengine.api import urlfetch

class MainPage(webapp2.RequestHandler):

  #Process notification events.
  def get(self):
    logging.info("Get request to notification page.")
    self.response.write("Welcome to the notification app Ver.5.")

#[START post request handler]
  def post(self):  # pylint: disable-msg=C6409
    """Process the notification event.

    This method is invoked when the notification channel is first created with
    a sync event, and then subsequently every time an object is added to the
    bucket, updated (both content and metadata) or removed. It records the
    notification message in the log.
    """
    """ Logging request """
    logging.debug(
        '%s\n\n%s',
        '\n'.join(['%s: %s' % x for x in self.request.headers.iteritems()]),
        self.request.body)

    if 'X-Goog-Resource-State' in self.request.headers:
      resource_state = self.request.headers['X-Goog-Resource-State']
      if resource_state == 'sync':
        logging.info('Sync message received.')
      else:
        an_object = json.loads(self.request.body)   # when a file is loaded on the bucket
        bucket = an_object['bucket']
        objectname = an_object['name']
        logging.info('Channel ID : %s Resource ID : %s', self.request.headers['X-Goog-Channel-Id'], self.request.headers['X-Goog-Resource-Id'])
        logging.info('%s/%s %s', bucket, objectname, resource_state)
        bucket_path = '/' + bucket
        filepath = bucket_path + '/' + objectname
        self.tmp_filenames_to_clean_up = []
        try:
          self.process_file(filepath, objectname)  # process_file does file read, calculation, image saving, and enqueuing a task with calculation result
        except Exception, e:
          logging.exception(e)
          #self.delete_files(filepath)  
        else:
          self.delete_files(filepath)   # deletes file after processing
          logging.info('file %s was deleted.', objectname)
#[END post request handler]
              
#[START process_file]
  def process_file(self, path, an_object):
 	
#[START function1]  a sub function for extfit
    def function1(x):
      k = 1.0433
      c = 3.7
      w = 2.5
      value = (pow(k,-1*x)*x - pow(k, -1*c)*c)/w
      return value
#[END function1]

#[START extfit]  Extreme Fit Function
    def extfit(x):
      y = -0.9745
      a = 3.5
      value = y + a*math.exp(-1*math.exp(-1*function1(x)) - function1(x) + 1 )
      return value
#[END extfit]  	
  	 
  	 # Creating Datastack class for saving roughness data
    class Datastack(ndb.Model):
            material = ndb.StringProperty()            
            roughness = ndb.FloatProperty()
            create_date = ndb.DateTimeProperty(auto_now_add=True)
            
    """ Prepare empty array to hold data """
    sampleArray = np.zeros((990,3))
    
    """ Open storage file and read data into lines as list """
    gcs_file = gcs.open(path)
    logging.info('file %s was read.', an_object)
    lines = gcs_file.read().split('\n')   
    num_data = len(lines) 
    gcs_file.close()
    #self.tmp_filenames_to_clean_up.append(path)
    
    """ Split each lines by comma and fill sampleArray """
    for index in range(1,num_data-2):  # Skip first and last incomplete data
      #logging.info(index)
      fragmented_line = lines[index].split(',')
      for i in range(3):	        
        sampleArray[index][i] = float(fragmented_line[i])  # index for line #, i = 0 for time interval, i = 1 for fingerprint sensor, i = 2 for graphene sponge
        #logging.info('%s %s %s', str(index), str(i), fragmented_line[i])
     
    """ Put time data into sampleArray[i][0] and time domain signal into timeDomain[i] """
    time = np.zeros(num_data)
    timeDomain = np.zeros(num_data)
    for i in range(1,num_data-2):  # Skip 0th line
      time[i] = sampleArray[i][0]/1000000 + time[i-1] # Accumulation of sampling interval
      timeDomain[i] = sampleArray[i][1]  # Copying to timeDomain array

    """ Preparation of json data to send to compute engine for linear regression """    
    timeList = time.tolist()
    timeDomainList = timeDomain.tolist()

    # For checking
    #for i in range(0,10):
    #  logging.info('%s %s',str(timeList[i]), str(timeDomainList[i]))
      
    form_fields = {
        'time' : timeList,
        'timeDomain' : timeDomainList    
    }
    form_data = json.dumps(form_fields)  
    headers = {'Content-Type': 'application/json'}  
    
    """ Sending json to compute engine """
    result = urlfetch.fetch(
                url='http://104.196.190.227/',
                payload=form_data,
                method=urlfetch.POST,
                headers=headers)
    
    """ Receving linear regression results for leveling timeDomain data """
    jsonreturn = json.loads(result.content)  # Converting to dic type
    slope = str(jsonreturn['slope'])
    intercept = str(jsonreturn['intercept'])
    logging.info('Regression result, Slope: %s', slope)
    logging.info('Regression result, Intercept: %s', intercept)    
    
    """ Leveling timeDomain data """
        
    
    length = num_data-2 # Length of data = number of data-2 
    aveSamInt = time[num_data-3]/length  # Average sample internal
    logging.info('Number of data : %s', str(length))
    logging.info('Average Sampling Interval : %s sec', str(aveSamInt))
    logging.info('Sample Frequency : %s Hz', str(1/aveSamInt))
    logging.info('Total Duration of Sampling : %s sec', str(length*aveSamInt))
    
    """[START] Plotting and saving """
    plt.subplot(2,3,1)  # Plot for time-domain signal
    plt.plot(time, timeDomain, 'k-')
    plt.xlabel('time')
    plt.ylabel('amplitude')

    plt.subplot(2,3,2)  # Plot for FFT in dB in frequency axis
    # k = frequency vector
    k = np.arange(length)
    # T = Total length of duration    
    T = length*aveSamInt 
    frq = k/T
    freq = frq[range(length/2)]   
    Y = np.fft.fft(timeDomain)/length       
    Y = Y[range(length/2)]
    Y2 = np.zeros(length/2)  # For displaying Y in dB        
    for i in range(1,length/2):
      Y2[i] = 10*math.log(abs(Y[i]),10)
    plt.ylim(-10,30)
    plt.plot(freq, Y2, 'r-')
    plt.xlabel('freq (Hz)')
    plt.ylabel('|Y(freq) dB|')

    lamda = np.zeros(length/2)  # Lamda as Period length
    ExtremeFit = np.zeros(length/2)
    for i in range(1, length/2):
      lamda[i] = 10/freq[i]  # 1cm/sec = 10 mm/sec, lamda = 10 mm/sec divided by freq
      ExtremeFit[i] = extfit(lamda[i])

    plt.subplot(2,3,3)  # Plot for FFT in amplitude in period axis
    plt.xlim(0,20)
    plt.ylim(-30,30)
    plt.plot(lamda, Y, 'r^')
    plt.xlabel('Period (mm)')
    plt.ylabel('Y(mm) in Amp')

    plt.subplot(2,3,4)  # Plot for Extreme Fit function in period
    plt.xlim(0,20)
    plt.plot(lamda, ExtremeFit, 'k*')
    plt.xlabel('Period (mm)')
    plt.ylabel('Extreme Fit Function')

    plt.subplot(2,3,5)  # Plot for Abs(FFT) in period
    plt.plot(lamda, abs(Y), 'r^')
    plt.xlim(0,20)
    plt.ylim(0,30)
    plt.xlabel('Period (mm)')
    plt.ylabel('|Y(mm) in Amp|')

    plt.subplot(2,3,6)  # Plot for Abs(FFT)*Extfit in period
    Z = np.zeros(length/2)
    for i in range(1, length/2):
      Z[i] = sampleArray[i][0]/1000000*math.fabs(Y[i])*extfit(lamda[i])
    plt.plot(lamda, Z, 'r^')
    plt.xlim(0,20)
    plt.xlabel('Period (mm)')
    plt.ylabel('|Z(Period)|')

    """ Saving plots as an image in a bucket """
    rv = StringIO.StringIO()
    plt.savefig(rv, format = 'png')
    image_name = list(an_object)
    image_name = image_name[0:-4]
    an_object = "".join(image_name)
    image_file = gcs.open('/testcloudstorage-1470232940384.appspot.com/' + an_object + '.png', 'w', content_type = 'image/png')
    image_file.write(rv.getvalue())
    image_file.close()    
    plt.clf()
    rv.close()
    """ [END] Plotting and saving """
    logging.info('image was saved')
    
    """ summation of weighted fourier transform """
    sum = 0
    for i in range (0, length/2):
    	sum = sum + Z[i]
    	
    """ Storing roughness factor in datastore """
    root = ndb.Key('datastack', 'rootdata')
    aData = Datastack(parent = root)
    aData.material = an_object
    aData.roughness = sum
    aData.put()
    
    """ Add a task to post the calculation result """
    q = taskqueue.Queue('pull-queue')
    tasks = []
    payload_str = str(sum)
    tasks.append(taskqueue.Task(payload=payload_str, method='PULL'))
    q.add(tasks)
    logging.info('Calculation result, ' + payload_str + ' was saved in queue.')
#[END process_file]

#[START delete_files]
  def delete_files(self, path):
    for filename in self.tmp_filenames_to_clean_up:
      try:
        gcs.delete(path)
      except gcs.NotFoundError:
        pass
#[END delete_files]



logging.getLogger().setLevel(logging.DEBUG)
app = webapp2.WSGIApplication([('/', MainPage)], debug=True)