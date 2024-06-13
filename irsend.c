#include <stdio.h>
#include "irslinger.h"

int main(int argc, char *argv[])
{
	uint32_t outPin = 22;            // The Broadcom pin number the signal will be sent on
	int frequency = 38000;           // The frequency of the IR signal in Hz
	double dutyCycle = 0.5;          // The duty cycle of the IR signal. 0.5 means for every cycle,
	                                 // the LED will turn on for half the cycle time, and off the other half
	int leadingPulseDuration = 3150; // The duration of the beginning pulse in microseconds
	int leadingGapDuration = 1030;   // The duration of the gap in microseconds after the leading pulse
	int onePulse = 471;              // The duration of a pulse in microseconds when sending a logical 1
	int zeroPulse = 471;             // The duration of a pulse in microseconds when sending a logical 0
	int oneGap = 1060;               // The duration of the gap in microseconds when sending a logical 1
	int zeroGap = 349;               // The duration of the gap in microseconds when sending a logical 0
	int sendTrailingPulse = 1;       // 1 = Send a trailing pulse with duration equal to "onePulse"
	                                 // 0 = Don't send a trailing pulse

  char code[MAX_COMMAND_SIZE];
    if (argc > 1) {
        strncpy(code, argv[1], MAX_COMMAND_SIZE);
    } else {
        printf("Usage: irsend <code>\n");
        return 1;
    }
	int result = irSling(
		outPin,
		frequency,
		dutyCycle,
		leadingPulseDuration,
		leadingGapDuration,
		onePulse,
		zeroPulse,
		oneGap,
		zeroGap,
		0,
		"11100010011010011011001000100000000000000000000100000010000000000000000010000000000000000000000000000000010100000");

        int second = irSling(
                outPin,
                frequency,
                dutyCycle,
                471,
                70000,
                onePulse,
                zeroPulse,
                oneGap,
                zeroGap,
                sendTrailingPulse,
                code);
	return result;
}
