#!/usr/bin/env python
import sys
import argparse
import time
import os
import RPi.GPIO as GPIO
import pygame
import random
import glob

GPIO.setmode(GPIO.BCM)

# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
  if ((adcnum > 7) or (adcnum < 0)):
    return -1
  GPIO.output(cspin, True)

  GPIO.output(clockpin, False)  # start clock low
  GPIO.output(cspin, False)     # bring CS low

  commandout = adcnum
  commandout |= 0x18  # start bit + single-ended bit
  commandout <<= 3    # we only need to send 5 bits here
  for i in range(5):
    if (commandout & 0x80):
      GPIO.output(mosipin, True)
    else:   
      GPIO.output(mosipin, False)
    commandout <<= 1
    GPIO.output(clockpin, True)
    GPIO.output(clockpin, False)

  adcout = 0
  # read in one empty bit, one null bit and 10 ADC bits
  for i in range(12):
    GPIO.output(clockpin, True)
    GPIO.output(clockpin, False)
    adcout <<= 1
    if (GPIO.input(misopin)):
      adcout |= 0x1

  GPIO.output(cspin, True)

  adcout /= 2       # first bit is 'null' so drop it
  return adcout

# change these as desired - they're the pins connected from the
# SPI port on the ADC to the Cobbler
SPICLK = 18
SPIMISO = 23
SPIMOSI = 24
SPICS = 25

# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)

# temperature sensor connected channel 0 of mcp3008
adcnum = 0

def run(args):
  # grab program parameters
  argsDict = vars(args)
  bufferDepth = int(argsDict['bufferDepth'])
  samplesForAction = int(argsDict['samplesForAction'])
  threshold = int(argsDict['threshold'])
  refresh = float(argsDict['refresh'])
  directory = argsDict['directory']
  playProbability = float(argsDict['probability'])
  
  # initialization
  sensorHistory = [0]*bufferDepth
  count = 0
  triggerValLast = False
  triggerValNew = False
  
  # find all mp3/wav files in a particular directory
  sounds = glob.glob(directory + '/*.mp3') + glob.glob(directory + '/*.wav')
  numSounds = len(sounds)
  if numSounds == 0 :
    print 'Could not find any sounds (.mp3 or .wav) in directory: ' + directory
    return
  
  random.seed()
  pygame.mixer.init()
  
  while True:
    # read the analog pin - from raspberry pi tutorials
    read_adc0 = readadc(adcnum, SPICLK, SPIMOSI, SPIMISO, SPICS)

    # convert analog reading to millivolts = ADC * ( 3300 / 1024 )
    millivolts = read_adc0 * ( 3300.0 / 1024.0)

    # remove decimal point from millivolts
    millivolts = "%d" % millivolts
    
    # determine if this is a hit - we've detected enough light
    passesThreshold = int(int(millivolts) > threshold)

    # update history variables        
    sensorHistory[count] = passesThreshold
    count = (count+1)%bufferDepth

    # calculate total number of hits
    score = sum(sensorHistory)
    
    # toggle triggerValNew based on program parameters
    if score >= samplesForAction:
      triggerValNew = True
    elif score <= bufferDepth-samplesForAction:
      triggerValNew = False
      
    print "read_adc0:\t", read_adc0
    print "millivolts:\t", millivolts
    print "passesThreshold:", passesThreshold
    print '[%s]' % '' .join(map(str, sensorHistory))
    print
    
    if not triggerValLast and triggerValNew:
      # trigger rising edge, check to see if we play a sound
      if random.random() < playProbability : 
        # randomly choose a sound to play
        soundToPlay = sounds[random.randint(0,numSounds-1)]
        pygame.mixer.music.load(soundToPlay)
        pygame.mixer.music.play()
        print 'playing ' + soundToPlay
      else :
        print 'playing nothing'
    elif triggerValLast and not triggerValNew :
      # trigger falling edge, stop playing sound
      pygame.mixer.music.stop()
      
    triggerValLast = triggerValNew

    time.sleep(refresh)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Light sensor -> sounds')
  parser.add_argument('-t', '--threshold', help='millivolt threshold for sensing light', default=2500, required=False)
  parser.add_argument('-r', '--refresh', help='refresh rate for detections in seconds', default=0.25, required=False)
  parser.add_argument('-b', '--bufferDepth', help='depth of history buffer', default=10, required=False)
  parser.add_argument('-s', '--samplesForAction', help='number of matching samples required to trigger action', default=8, required=False)
  parser.add_argument('-d', '--directory', help='file directory containing all mp3s or wavs to play', default='.', required=False)
  parser.add_argument('-p', '--probability', help='probability of playing a sound when conditions are met (0 to 1)', default=1.0, required=False)
  run(parser.parse_args())
  