# Virtual Entities [![Quality](https://github.com/steineggerroland/VirtualEntities/actions/workflows/quality.yml/badge.svg)](https://github.com/steineggerroland/VirtualEntities/actions/workflows/quality.yml) [![BehaviorTest](https://github.com/steineggerroland/VirtualEntities/actions/workflows/behavior_test.yml/badge.svg)](https://github.com/steineggerroland/VirtualEntities/actions/workflows/behavior_test.yml)

Do you have a washing machine or dryer that is not smart? Make it smart!

Do you have a problem with too high or too low humidity? One look and you know when to ventilate.

Enhance your home and make it smart. 

## Motivation

In our family, we had a problem to coordinate our house work - the washing machine has finished and we forgot to unload the clothes, dirty dishes piled up even though the dishwasher had already been emptied.
In addition, it happened that we forgot to ventilate the bathroom after showering, leading to high humidity.

We wanted to track the work around washing machine, dishwasher and dryer.
Does it need to be unloaded? Is it free and can be used?
Is the humidity too high and we need to air the rooms?

This project helped us a lot with some sensors and power plug adapters as well as a coordination hub (in our case OpenHAB).

## What it does

* Configure your virtual entities, i.e., **appliances**, **rooms** and **calendars** of **persons**
* Reads power consumption, temperature and humidity measurements from [**MQTT**](https://en.wikipedia.org/wiki/MQTT)
* Notifies about new status of entities through MQTT
* Adapts status of entities based on the measurements
  * Power consumption above a certain **threshold** indicates the appliance is _running_
  * When power consumption is below a **threshold** for a certain time the run is expected to be **finished**. A finished run **needs some treatment** afterwards, e.g. the washing machine needs to be unlaoded
  * Indicate unloading or loading of an appliance by MQTT messages
* Status of entities can be viewed on a **webpage** and **dashboard** as depicted on the image.

![Overview of entities](https://github.com/steineggerroland/VirtualEntities/assets/4447371/89b26b16-99e8-447c-b563-1cf939b3b05a)

## How it's done

The project is mainly written in python and offers a website with some vanilla javascript enhancements.

It is tested on a unit test basis and with behavior tests using [selenium](https://github.com/SeleniumHQ/selenium) and [behave](https://github.com/behave/behave).

## Possible setup

I am using a [Raspberry Pi 3 B+](https://www.raspberrypi.com/products/raspberry-pi-3-model-b-plus/) to coordinate my sensors and power plugs and a [Raspberry Pi 4 B](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/) running OpenHAB and [Virtual entities](#).

All my room climate sensors support the [Zigbee standard](https://en.wikipedia.org/wiki/Zigbee), thus, I am running [Zigbee2MQTT](https://github.com/Koenkk/zigbee2mqtt) which sends measurements of sensors as message to MQTT.
Some of my power plugs support Zigbee and are connected using Zigbee2MQTT. On the other hand I have power plugs that just use Bluetooth. These plugs are connected to MQTT using [sem600 mqtt](https://github.com/steineggerroland/sem6000-mqtt).

OpenHAB is used to read the new features / status of the now smart entities. The status messages send by this project are consumed by OpenHAB.
Additionally, OpenHAB handles physical buttons in my home and converts their actions to MQTT messages which are consumed to manipulate the virtual entities. I have buttons attached to my dishwasher, washing machine etc.
For example, when I press the button on my washing machine, the virtual washing machine is triggered to be unloaded AND some lights in my home are triggered to celebrate the done house work.
