#!/bin/bash
#
# Script to perform daily correction for a synchronous clock.
# Requires gpiod.
#
gpioset gpiochip0 17=1
sleep 8
gpioset gpiochip0 17=0
