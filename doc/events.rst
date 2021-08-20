Events
=======

DHALSIM has support for network events. This chapter will explain the configuration for these.

If you want to put the events in a separate file, see the section :ref:`Events in a separate file`.

network events
--------------

Events are situations started by a trigger that do not necessarily are attacks. In addition, events do not require launching additional mininet nodes or having additional mininet nodes interacting with the simulation.

Example:

.. code-block:: yaml

    network_events:
      - name: link_loss
        type: packet_loss
        target: PLC1
        trigger:
            type: time
            start: 648
            end: 792
        value: 25The following sections will explain the different configuration parameters.

name
~~~~
*This option is required*

This defines the name of the event. It cannot have whitespaces.

trigger
~~~~~~~~
*This option is required*

This parameter defines when the event is triggered. There are 4 different types of triggers:

* Timed events
    * :code:`time` - This is a timed event. This means that the event will start at a given iteration and stop at a given iteration
* Sensor attacks: These are event that will be triggered when a certain sensor in the water network meets a certain condition.
    * :code:`below` - This will make the event trigger while a certain tag is below or equal to a given value
    * :code:`above` - This will make the event execute while a certain tag is above or equal to a given value
    * :code:`between` - This will ensure that the event is executed when a certain tag is between or equal to two given values

These are the required parameters per type of trigger:

* For :code:`time` events:
    * :code:`start` - The start time of the event (in iterations).
    * :code:`end` - The end time of the event (in iterations).
* For :code:`below` and :code:`above` events:
    * :code:`sensor` - The sensor of which the value will be used as the trigger.
    * :code:`value` - The value which has to be reached in order to trigger the event.
* For :code:`between` events:
    * :code:`sensor` - The sensor of which the value will be used as the trigger.
    * :code:`lower_value` - The lower bound.
    * :code:`upper_value` - The upper bound.

target
~~~~~~~~~
*This option is required*

This parameter defines the PLC link that will be affected. In DHALSIM, the PLCs have only one network link (interface)

type
~~~~~~~
*This option is required*

This parameter defines the type of network event. Currently, only packet_loss is supported

value
~~~~~~~
*This option is required*
This parameter defines the percentage of packets that will be lost in the network link during the event
