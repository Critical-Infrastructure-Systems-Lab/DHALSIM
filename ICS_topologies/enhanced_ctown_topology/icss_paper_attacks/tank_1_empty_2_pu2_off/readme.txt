The objective of this attack is to empty the tank1 by launching an attack on the communication between PLC2-PLC1
The attack is run in the C-Town Enhanced topology and is launched in iteration 648 using a 300seconds timestep.
Attack finishes at iteration 1152. During the attack, pump PU2 is closed, emptying the tank1. 
The attack is a mitm attack that spoofs the T1 value, giving the reading an offset that causes PU2 to close

This attack was launched in an attempt to create an attack that would be dificult  to diferentiate from faulty equipment (PU2)
Nevertheless, the attack did not worked as planned, because tank_1_empty_1_pu2_off and tank_empty_2_pu2_off do not have exactly the same
physical response
