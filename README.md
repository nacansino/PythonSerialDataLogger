# PythonSerialDataLogger
This is a script that fetches data from a real-time serial data stream and writes the data into a csv file.

This supports auto-detection of Arduino serial ports.

The implementation requires the setting of a pre-defined start byte defined by the constant START_CONDITION. Moreover, this only supports data stream of C-structs in little endian format.

The packet's struct format and size must be defined using the variable s and PACKET_SIZE respectively.

A more general implementation will be written in the future.
