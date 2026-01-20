# ModbusTcp Mosaik HIL Simulator Adapter

A Python project that integrates Modbus as a Hardware-in-the-Loop (HIL) simulator for Mosaik co-simulation framework.

## Overview

This adapter enables Modbus communication within Mosaik scenarios, allowing hardware devices or simulators using the Modbus protocol to participate in co-simulation environments.

## Installation

// TODO


## Mosaik Scenario Integration

To integrate this simulator in a Mosaik scenario, you first need to define all models you want to use in the ConfigurationManager.

**This step has to be done before creating initializing the Mosaik world** as the ConfigurationManager needs to be aware of all available models at that point.

```python
from modbushil.configurationmanager import ConfigurationManager

ConfigurationManager.register_model("<ModelName>", <ModelConfig>)
```

How the model configuration looks like is described in section [Configuration File Structure](#configuration-file-structure) below.

After registering the models, you can define the simulator in your Mosaik scenario just like any other Mosaik simulator:

```python
import mosaik

# Create simulation configuration
SIM_CONFIG = {
	"ModbusSim": {
		"python": "modbushil.siminterface:ModbusSimInterface",
	},
}

# Initialize world
world = mosaik.World(SIM_CONFIG)

# Start the Modbus simulator
modbus_sim = world.start("ModbusSim", step_size=1, use_async=True)

# Create simulator instance
modbus_entity = modbus_sim.ModelName.create(
    1,
    host="localhost",
    port=5002
)
```

`ModelName` must match the name used when registering the model in the ConfigurationManager. And host:port must be a reachable Modbus server. If the model configuration does not match the Modbus device setup, errors may occur during runtime.

### Asynchronous vs Synchronous Operation

Setting `use_async=True` runs Modbus I/O in the background, preventing the simulator from blocking while waiting for device communication. Note this adds a one-step latency: values written in step t are sent immediately, but the corresponding read results (including effects of that write) become available to the Mosaik world in step t+1. If you need immediate read-after-write consistency within the same step, use `use_async=False`. This however will block execution until Modbus communication completes, which may slow down the simulation.


## Configuration File Structure

The configuration file consists of three main sections:

```json
{
  "modbus_io_bundles": { ... },
  "variables": { ... },
  "methods": { ... }
}
```

Only `modbus_io_bundles` and `variables` are required.
The `methods` section is optional.

---

### Modbus I/O Bundles

Modbus I/O bundles define which Modbus registers are read or written together in a single request.

Valid register types are:

* `coil`
* `discrete_input`
* `holding_register`
* `input_register`


A bundle can contain:

* Single address (e.g. `"60"`)
* Range (e.g. `"1-12"`)


Example:

```json
"modbus_io_bundles": {
  "read": {
    "input_register": [
      "1-12",
      "60",
      "70-89"
    ]
  },
  "write": {
    "holding_register": [
      "10-20"
    ]
  }
}
```


---

### Variables

The `variables` section defines the individual data points exchanged between the Modbus device and the simulation.
They can also be used for intermediate calculations.

Each variable must specify:
* `iotype`: `read`, `write`, or `both`

Variables mapped to Modbus registers must also specify:
* `datatype`: Modbus data type
  * Supported data types: `bool`, `uint16`, `int16`, `uint32`, `int32`, `uint64`, `int64`, `float`, `double`
  * Only has an effect right after reading from or right before writing to Modbus where castings are performed.
* `register`: Modbus register
  * `{type}{address|range}` format (e.g. `h1` for holding register 1, `i10-20` for input registers 10 to 20 inclusive)
  * valid register types: `c` (coil), `d` (discrete input), `h` (holding register), `i` (input register)
  * write operations can only use `coil` or `holding_register`

Variables mapped to Modbus registers can optionally specify:
* `scale`: scaling factor applied to the value
  * Multiplies value after reading from Modbus
  * Divides value before writing to Modbus

Variables that should be exposed to Mosaik must also specify:
* `mosaik`: `true`

Example:

```json
"variables": {
  "P_target[MW]": {
    "iotype": "write",
    "datatype": "uint16",
    "register": "h1",
    "mosaik": true,
    "scale": 0.000001
  },
  "IntermediateValue": {
    "iotype": "both"
  }
}
```

---

### Data Processing Methods (Optional)

The optional `methods` section allows simple processing of values directly in the configuration file.

Methods can be applied:

* **after reading** from Modbus (`read`) (after scaling and type casting)
* **before writing** to Modbus (`write`) (before scaling and type casting)

Each method defines:

* The target variable (`set`)
* An action (`eval` / `function`)

Depending on the action, one of the following must be specified:
* `expression`: for `eval` action
* `function` and `parameters`: for `function` action

#### Eval Action

Expressions can reference variables using the `$( )` syntax.

Example:

```json
"methods": {
  "read": [
    {
      "set": "P[MW]",
      "action": "eval",
      "expression": "$(E[MWH]) / (1000 / 1e6)"
    }
  ],
  "write": [
    {
      "set": "State",
      "action": "eval",
      "expression": "if $(P_target[MW]) > 0 then 1 else 0"
    }
  ]
}
```

#### Function Action

A function action must reference a callable Python object in the `function` field and provide an ordered list of variable names from this configuration in `parameters`. The simulator will pass the current values of those variables to your function in the specified order; the parameter names used inside your Python function do not need to match the config variable names. The function’s return value is assigned to the `set` target.

Example:

```python
def calc_power(voltage: float, current: float) -> float:
    return voltage * current

config ={
  "methods": {
    "read": [
      {
        "set": "P[W]",
        "action": "function",
        "function": calc_power,
        "parameters": ["U[V]", "I[A]"]
      }
    ]
  }
}
```
