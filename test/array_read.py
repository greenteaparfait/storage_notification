import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import StringIO
import math

#[START function1]
def function1(x):
  k = 1.0049
  xc = 3.6
  w = 2.806
  value = (pow(k,-x)*x - pow(k, -xc)*xc)/w
  return value
#[END function1]

#[START extfit]
def extfit(x):
  y0 = -0.9745
  A = 3.5
  value = y0 + A*math.exp(-math.exp(-function1(x)) - function1(x) + 1 )
  return value
#[END extfit]

# Prepare empty array to hold data
sampleArray = np.zeros((990,3))

# Read data from file into sampleArray
lines = [line.rstrip('\n') for line in open('scan-1132871455.txt')]
for index in range(1,990):
    #print(lines[index])
    fragmented_line = lines[index].split(',')
    for i in range(3):	
        #print(fragmented_line[i])        
        sampleArray[index][i] = float(fragmented_line[i])

# Put time data into sampleArray[0] and signal into timeDomain
time = np.zeros(990)
timeDomain = np.zeros(990)
for i in range(1,990):  # Skip 0th line
    time[i] = sampleArray[i][0]/1000000 + time[i-1] # Accumulation of sampling interval
    timeDomain[i] = sampleArray[i][1]  

length = len(time) # Length of data = number of data
aveSamInt = time[len(time)-1]/length  # Average sample internal
print('Number of data : ' + str(length))
print('Average Sampling Interval : ' + str(aveSamInt) + 'sec')
print('Sample Frequency : ' + str(1/aveSamInt) + 'Hz')
print('Total Duration of Sampling : ' + str(length*aveSamInt) + 'sec')

plt.subplot(2,3,1)
plt.plot(time, timeDomain, 'k-')
plt.xlabel('time (Seconds)')
plt.ylabel('amplitude')

plt.subplot(2,3,2)
k = np.arange(length)
T = length*aveSamInt # Total length of duration
frq = k/T
freq = frq[range(length/2)]   # Reducing length of frq by half
Y = np.fft.fft(timeDomain)/length    # Fast Fourier Transform   
Y = Y[range(length/2)]        # Reducing length of Y by half
for i in range(1,length/2):
  Y[i] = 10*math.log(abs(Y[i]),10)
plt.ylim(-10,30)
plt.plot(freq, Y, 'r-')
plt.xlabel('freq (Hz)')
plt.ylabel('|Y(freq) dB|')

lamda = np.zeros(length/2)  # Period
ExtremeFit = np.zeros(length/2)
for i in range(1, length/2):
  lamda[i] = 10/freq[i]  # 1cm/sec = 10 mm/sec, lamda = 10 mm/sec divided by freq
  ExtremeFit[i] = extfit(lamda[i])

plt.subplot(2,3,3)
plt.xlim(0,20)
plt.ylim(-10,30)
plt.plot(lamda, Y, 'r^')
plt.xlabel('Period (mm)')
plt.ylabel('Y(mm) dB')

plt.subplot(2,3,4)
plt.xlim(0,20)
plt.plot(lamda, ExtremeFit, 'k*')
#plt.xlable('Period (m)')
#plt.ylable('Extreme Fit Function')

plt.subplot(2,3,5)
plt.plot(lamda, abs(Y), 'r^')
plt.xlim(0,20)
plt.ylim(0,30)
plt.xlabel('Period (mm)')
plt.ylabel('|Y(mm) dB|')

plt.subplot(2,3,6)
Z = np.zeros(length/2)
for i in range(1, length/2):
  Z[i] = math.fabs(Y[i])*extfit(lamda[i])
plt.plot(lamda, Z, 'r^')
plt.xlim(0,20)
plt.xlabel('Period (mm)')
plt.ylabel('|Z(Period)|')

plt.show()

plt.savefig('myfig.png')


