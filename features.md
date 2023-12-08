# Features

List of implemented and planned features of an iot machine.

## Implemented

* Read power consumption from mqtt
* Log power consumption timeline
* Calculate internal state using power consumption thresholds
  * States are _off_, _idle_, _running_ and _unknown_.
* Propagate internal state to mqtt
* Determine _online status_ based on date of last received message
* Add optional _needs treatment status_
  * _needs treatment status_ is true or false
  * False on startup
  * Set to true when switching from _working_ state to any other
  * Handle mqtt messages to manipulate _needs treatment status_

## Planned

* Use analytics on power consumption to determine internal state
  * Calculate state clusters for power consumption
  * Let user label state clusters, whereby _off_, _idle_ and _working_ must be declared
  * Propagate label for current power consumption
* Manage things in web
  * Add eThings
  * Display eThing details
    * Internal State
    * _needs treatment status_
    * Current power consumption
    * _online status_
    * Date of last message
  * Configure eThing
    * Configure mqtt topics/queries (show last received message)
    * Choose how internal state is calculated (threshold or analytical)
    * Show power consumption timeline

