The objective of this attack was to empty tank5 through a MiTM attack.

These is a sister attack, the sister would be tank5_overflow_exponential

The objective of the attack is to have an offset that gradually causes T5 to empty.

This attack was dropped because the empty option did not worked as expected
This was run after we solved the bug in the script. Nevertheless, T5 is also filled by the pu9 pump, which seems to always be empty.

The empty attack causes the weird behavior of emptying T1. For this reason, the attack was dropped