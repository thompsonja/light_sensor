light_sensor
============

Raspberry Pi Python script for detecting light and playing sounds.

This is a Halloween project using a Raspberry Pi, MCP3008 ADC, and photoresistor.

The goal is to detect light and then play spooky sound effects.

Customizable via command line:
  -Select how many samples are needed to detect light
  -Select ADC thresholds for what is considered light
  -Select how many historical samples to keep
  -Select how frequently to sample data
  -Select which directory to look for sound effects (.mp3/.wav)
  -Select probability of playing sound when light is detected