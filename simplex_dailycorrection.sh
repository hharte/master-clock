#!/bin/bash
#
# Script to perform hourly correction for a synchronous clock.
# Requires gpiod.
#
gpioset gpiochip0 17=1
sleep 14
gpioset gpiochip0 17=0
