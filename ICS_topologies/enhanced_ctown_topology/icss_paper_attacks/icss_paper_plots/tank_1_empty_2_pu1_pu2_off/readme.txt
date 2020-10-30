The objective of this attack is to empty the tank1 by launching an attack on the communication between PLC2-PLC1
The attack is run in the C-Town Enhanced topology and is launched in iteration 648 using a 300seconds timestep.
Attack finishes at iteration 1152. During the attack, pumps PU1 and PU2 are closed, emptying the tank1. 
The attack is a mitm attack that spoofs the T1 value, giving the reading an offset that causes both pumps to close

A similar attack called "pu2_off" was launched in which only PU2 was closed