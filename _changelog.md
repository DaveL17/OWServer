### v2025.2.7
- Fixes `updateDeviceStates()`'s comm-failure handler discarding the underlying exception and logging an ambiguous
  "Error parsing sensor states." message with no indication of which configured server failed; now splits
  `ElementTree.ParseError` (a truncated/corrupted response, e.g. a server losing power mid-transfer) from other
  exceptions, tags both with `server_ip`, and retains `str(e)` in the Warning-level log line, with a debug-level
  traceback for the non-`ParseError` case.
- Fixes `get_details_xml()`'s two exception handlers not identifying which configured server the failure was about;
  both now include `server_ip` and `str(e)`.

### v2025.2.6 [released]
- Fixes excessive change notifications sent to Indigo per poll cycle; all device state updates are now batched into a
  single `updateStatesOnServer()` call per device, eliminating the flood of `subscribeToChanges()` events previously
  triggered by per-state `updateStateOnServer()` calls.
- Fixes `getServerList()` socket not being closed when a non-timeout exception is raised during server discovery.
- Fixes `updateDeviceStates()` raising a bare `Exception` on failed XML fetch, causing a misleading second "Error
  parsing sensor states" log entry after the connection failure was already reported; the failed server is now skipped
  with `continue`.
- Fixes dead-code `if not dev:` guard in `updateDeviceStates()` that could never be true inside an `itervalues` loop.
- Fixes swapped comments on `"BPH"` and `"BPM"` cases in `updateEDS0066()` (labels were transposed; code was correct).
- Adds more tests
- Updates wiki.

### v2025.2.5 [released]
- Bump version number.

### v2025.2.4
- Migrates HTTP client from `requests` to `httpx`.
- Linting changes.

### v2025.2.3
- Fixes wiki typos.
- Reflows wiki text lines exceeding 120 characters across `configuration.md`, `devices.md`, `installation.md`,
  `scripting.md`, and `tutorials.md`.

### v2025.2.2
- Fixes `updateEDS0080()` duplicate `'RelayFunction'` entry in props list causing the prop to be written twice per poll
  cycle.
- Fixes `updateEDS0090()` duplicate `'DiscreteIO3PulldownState'` entry in props list causing the prop to be written
  twice per poll cycle.
- Fixes `updateDS2423()` using two separate `if` statements instead of `if`/`elif` to select the counter value,
  leaving a redundant second check that could never change behavior but obscures intent.
- Fixes `getSensorList()` debug guard comparing the debug level against `3` (valid levels are 10–50), making the
  guard always true when `showDebugInfo` is set; now correctly checks `<= 10`.
- Fixes `runConcurrentThread()` still able to pass `0` to `self.sleep()` when the configured poll interval equals
  exactly `5` seconds; enforces a minimum sleep of `5` seconds.

### v2025.2.1
- Fixes `dumpXML()` writing an empty log file when the server is unreachable; `None` check now precedes the file 
  `open()` call.
- Fixes `getSensorList()` and `getServerList()` crashing with `AttributeError` when `OWServerIP` pref is absent 
  (changed default from `None` to `''`).
- Fixes `toggle_led()` and `toggle_relay()` sending an empty value to hardware when reading device state raises an 
  exception.
- Fixes `updateDeviceStates()` disabling devices on all servers when one server fails; only devices belonging to the 
  failing server are now turned off.
- Fixes `updateDS2408()` bit-index mismatch where `owsInput{N}` states used MSB-first indexing but `sensorValue` `S_N` 
  cases used LSB-first, causing them to reflect different physical inputs.
- Fixes `populate_props()` raising `AttributeError` when an expected XML element is absent; missing elements now stored 
  as `"Unsupported"`.
- Fixes `runConcurrentThread()` logging "Fatal error" on normal graceful shutdown (`StopThread`).
- Fixes `updateEDS0071()` `"T"` sensorValue case bypassing `temp_convert()` and the temperature compensation offset,
  causing raw °C to be displayed regardless of user preferences.
- Fixes `getServerList()` permanently overwriting the global socket timeout; previous timeout is now saved and restored
  via `finally`.
- Fixes `getSensorList()` raising `TypeError` when debug logging is enabled due to comparing a string pref value against
  an integer.
- Fixes unbalanced parentheses in the `closedPrefsConfigUi()` debug-level log message.
- Fixes `runConcurrentThread()` passing zero or a negative value to `self.sleep()` when the poll interval is 5 seconds
  or less.
- Fixes `updateEDS0071()` state loop storing raw °C in the `owsTemperature` state regardless of unit preference or
  compensation offset; now applies `temp_convert()` consistently with all other temperature-capable sensors.
- Fixes `updateDeviceStates()` using bare key access for `OWServerIP` pref, raising `KeyError` and crashing the polling
  loop if the pref is absent.

### v2025.2.0
- Fixes `sendToServerAction()` and `customWriteToDevice()` using `https://` (EDS hardware requires `http://`).
- Fixes dead `None` check in `getSensorList()` (list is never `None`; changed to `not sensor_id_list`).
- Fixes `dumpXML()` passing a `%s` format string to `indigo.server.log()`, which does not support format substitution.
- Fixes `__init__()` comparing string pref value against integers when validating debug level, causing it to reset on 
  every startup.
- Fixes `updateEDS0080()` `case "C_1"` reading counter into an unused variable instead of `input_value`.
- Fixes `populate_props()` never calling `replacePluginPropsOnServer()`, silently discarding all writable prop updates.
- Fixes `updateDeviceStates()` calling `self.sleep()` inside the device loop for unconfigured devices, blocking all 
  remaining devices from updating.
- Converts `DLFramework` files from static copies to symlinks (shared development library).

### v2025.1.0
- Stability and performance improvements.
- Standardized project `.gitignore` file.
- Removes unused variables from `tests/.env` file.
- Removes empty plugin directories.

### v2022.0.4
- Adds foundation for API `3.1`.

### v2022.0.3
- Adds `_to_do_list.md` and changes changelog to Markdown.
- Moves plugin environment logging to plugin menu item (log only on request).

### v2022.0.2 [released]
- Bumps version number.

### v2022.0.1
- Updates plugin for Indigo 2022.1 and Python 3.
- Standardizes Indigo method implementation.

### v1.0.12
- Updates communication to use the requests library.

### v1.0.11
- Logging refinements.

### v1.0.10
- Removes aggressive logging of unsupported data elements for Server devices.

### v1.0.09
- Fixes broken link to readme logo.

### v1.0.08
- Better integration of DLFramework.

### v1.0.07
- Removes all references to legacy version checking.

### v1.0.06
- Removes plugin update notifications.
- Code refinements.

### v1.0.05
- Updates plist link to wiki.
- Updates plugin update checker to use curl to overcome outdated security of Apple's Python install.

### v1.0.04
- Code consolidation using DLFramework.
- Adds note to documentation that the plugin does not require Internet access to function.
- IPS configuration.

### v1.0.03
- Stylistic changes to Indigo Plugin Update Checker module.
- Improves code used to write sensor data to the Indigo Logs folder.
- Standardizes plugin menu item styles. Menu items with an ellipsis (...) denote that a dialog box will open. Menu
  items without an ellipsis denote that the plugin will take immediate action.

### v1.0.02
- Moves support URL to GitHub.
- Minor UI refinements.
- Fixes bug in plugin configuration dialog validation.
- Fixes bug in device configuration dialog validation.
- Fixes bug in test server communication routine.
- Code refinements.

### v1.0.01
- Moves project to GitHub and increments version number.

### v0.8.3
- Modifies string substitution methods for future functionality.
- Updates error trapping for future functionality.

### v0.8.2
- Fixes bug that will cause new installations to fail when setting up plugin configuration for the first time.

### v0.8.1
- UI refinements.

### v0.8.0
- Adds support for
  - EDS0064 (Temperature Sensor with Counter)
  - EDS0065 (Temperature and Humidity Sensor)
  - EDS0066 (Temperature and Barometric Pressure Sensor)
  - EDS0070 (Vibration Sensor)
  - EDS0071 (RTD Interface, 4 Wire)
  - EDS0080 (Octal 4-20 Milliamp Input)
  - EDS0082 (Octal Current Input)
  - EDS0083 (Quad 4-20 Milliamp Input)
  - EDS0085 (Quad 0-10 Volt Input)
  - EDS0090 (Octal Discrete IO)
- Adds config setting for sensors with/without optional relay.
- Adds temperature adjustment field to allow for fine-tuning sensor temperature values (value in °C.) For example,
  entering a value of -1 will adjust the temperature reading by -1°C or by -1.8°F.
- Adds Indigo Action item to update all sensor devices.
- Adds Indigo Action item to send command to a 1-Wire device.
- Adds Indigo Menu item to send command to a 1-Wire device.
- Updates DS2408 to allow selection of switches 0-7 as the primary sensor display value.
- Implements Indigo custom device state icons for all switches, relays, and LED states to reflect on or off.
- Fixes bug where some devices did not properly track LED and Relay states.
- Moves server communication test from plugin configuration menu to the Indigo plugin menu (reduces clicks to run the
  test) and allows user to send XML output to the Indigo log (useful when troubleshooting problems.)
- Reorders sensor list by sensor number rather than name for easier identification.
- Code enhancements:
  - Fixes some device state data types.
  - Simplifies configuration validation code.
  - Simplifies data parsing routines.
  - Standardizes device display preferences. May require users to reselect default display value for some devices.

### v0.7.02
- Refines logging of device update status for OW-Server-ENET (Rev. 1)
- Refines device states to account for differences in OW-Server_ENET (Rev 1 and Rev 2) servers.
- Refines compliance with PEP8.

### v0.7.01
- Adds uniform support for OWSERVER-ENET version 1 server.
- Adds support for EDS0067 Temperature and Light.
- Adds menu items to enable/disable all OWS devices.
- Adds Indigo custom device icon enumeration (device list, Indigo Touch, etc.)
- Adds configuration option to suppress results logging (still logs errors.)
- Code Refinements:
  - Refines configuration dialogs.
  - Improves Unicode support.
  - Increases compliance with PEP8.
  - Updates plugin to use Python 2.6 as default.
  - Moves parsing to methods for each type of sensor.
  - Improves debug logging implementation.
  - Minor improvement to built-in timer accuracy.
- Fixes bug in display precision routine.
- Fixes bug where new (un-configured) devices are reported as being offline.
- Fixes bug in debug logging.

### v0.7.0
- WARNING! This update may require users to delete and reassign all existing sensor devices.
  - Adds a new device type to represent the OW server itself.
  - Significant rewrite of device code including support for numerous
    new sensor types.
  - Implements new device features including: greater use of device
    controls where appropriate: UI state values, on/off state, etc.
  - Adds user control over which device state to display in the item
    list and under the state "sensorValue" -- this applies only to
    devices where the choice is appropriate.
  - Adds menu item to provide for instantaneous refresh of device
    states (sensor values) which is under: "Refresh Sensors Now..."
  - All sensors update after configuration dialog closed with 'Save'.
  - Adds debug levels -- Low, Medium, High.
  - Many, many code refinements.

### v0.6.93
- Wraps sensor ID list in Unicode.

### v0.6.92
- Adds support for DS2450 Quad A/D Converter.
- Consolidates parsing functions.
- Fixes bug in "Test the IP Address" method within the plugin config dialog.

### v0.6.91
- Code refined to account for Unicode characters where possible.

### v0.6.9
- Fixes bug in temperature conversion routine for metric installations.

### v0.6.8
- Adds plugin menu items for instant version update checking and for debug toggling.

### v0.6.7
- Fixes a problem with plugin package naming structure that can cause problems in some installations.

### v0.6.6
- Includes additional sensor types.
- Code refinements and enhancements.
- Bug fixes.

### v0.6.5
- Added quarter day refresh option.
- Error handling enhancements.
- Refined normal logging and error logging.
- Bug fixes.

### v0.6.3
- Alpha publicly available.

### v0.6.2
- Added code for functioning 'Send Status Request' button.

### v0.6.1
- Addressed condition when device config returned object of noneType.
- Added descriptive comments to plugin code.
- Bug fixes

### v0.6.0
- Added method to identify missing sensors (devices won’t update).
- Bug fixes.

### v0.5.1
- Addressed known errors arising during device add.

### v0.5.0
- Addressed condition where no devices of type exist.
- Addressed condition where there are more devices than sensors to assign.
- Addressed condition where no plugin preferences file exists.
- Assign default values to plugin prefs if pluginPrefs doesn’t exist.
- Added placeholder to configUI for HA7Net.

### v0.4.0
- Major rewrite of code writing sensor values to devices based on romID.
- Added preference for temperature display value precision to plugin config.
- Added placeholder for ‘Send Status Request’ callback (actionControlCenter).

### v0.3.0
- Temperature conversions moved to method.
- Refined sensorArray to show only unassigned devices when adding new sensors.

### v0.2.2
- Add XML dump to config menu.

### v0.2.1
- Pass romID to devices.xml.

### v0.2.0
- Write sensor values to variables.

### v0.1.0
- Moved scheduled script to plugin framework.
