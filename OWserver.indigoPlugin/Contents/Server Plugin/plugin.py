# noqa pylint: disable=too-many-lines, line-too-long, invalid-name, unused-argument, redefined-builtin, broad-except, fixme

"""
OWserver Embedded Data Systems (EDS) 1-Wire Server Plugin for Indigo
Author: DaveL17

Plugin for Indigo Home Control Server:
    https://www.indigodomo.com
    https://www.edsproducts.com

The OWServer Plugin loads XML data from one or more EDS 1-Wire servers, interprets the information,
and makes it available for plugin-supported devices. The plugin supports the following server types:

    OW-SERVER-ENET
    OW-SERVER-WiFi
    OW-SERVER-ENET2
    OW-SERVER-WiFi-2G

The plugin does _not_ support the HTML-based output of the HA7NET server.
"""

# =================================== TODOS ===================================
# TODO -
# ================================== IMPORTS ==================================
# Built-in modules
import datetime as dt
import json
import logging
import socket
import xml.etree.ElementTree as eTree

# Third-party modules
try:
    import indigo
    import requests
except ImportError:
    pass

# try:
#     import pydevd
# except ImportError:
#     pass

# My modules
import DLFramework.DLFramework as Dave  # noqa
import stateDict  # noqa
from constants import *  # noqa  pylint: disable=wildcard-import
from plugin_defaults import kDefaultPluginPrefs  # noqa  pylint: disable=unused-import

# =================================== HEADER ==================================
__author__    = Dave.__author__
__copyright__ = Dave.__copyright__
__license__   = Dave.__license__
__build__     = Dave.__build__
__title__     = 'OWServer Plugin for Indigo Home Control'
__version__   = '2022.0.1'


# =============================================================================
class Plugin(indigo.PluginBase):
    """
    Title placeholder

    Body placeholder
    """
    def __init__(self, plugin_id, plugin_display_name, plugin_version, plugin_prefs):
        super().__init__(plugin_id, plugin_display_name, plugin_version, plugin_prefs)

        # ============================ Instance Attributes =============================
        self.plugin_is_initializing  = True
        self.plugin_is_shutting_down = False
        self.state_dict              = stateDict.OWServer(self)
        self.device_list             = []
        self.number_of_sensors       = 0
        self.number_of_servers       = 0
        self.pad_log = "\n" + (" " * 34)  # 34 spaces to continue in line with log margin.
        self.xmlns = '{http://www.embeddeddatasystems.com/schema/owserver}'  # noqa - not https://

        # ========================== Initialize DLFramework ===========================
        self.Fogbert = Dave.Fogbert(self)
        # Log pluginEnvironment information when plugin is first started
        self.Fogbert.pluginEnvironment()

        # =============================== Debug Logging ================================
        log_format = '%(asctime)s.%(msecs)03d\t%(levelname)-10s\t%(name)s.%(funcName)-28s %(msg)s'
        self.debugLevel = int(self.pluginPrefs.get('showDebugLevel', "30"))
        self.plugin_file_handler.setFormatter(
            logging.Formatter(fmt=log_format, datefmt='%Y-%m-%d %H:%M:%S')
        )
        self.indigo_log_handler.setLevel(self.debugLevel)

        if self.pluginPrefs['showDebugLevel'] not in (10, 20, 30, 40, 50):
            self.pluginPrefs['showDebugLevel'] = 30

        self.plugin_is_initializing = False

    # ==============================================================================
    def __del__(self):
        """

        :return:
        """
        self.logger.debug("__del__ method called.")
        indigo.PluginBase.__del__(self)

    # =============================================================================
    # ============================== Indigo Methods ===============================
    # =============================================================================
    def closedDeviceConfigUi(self, values_dict, user_cancelled, type_id, dev_id):  # noqa
        """
        Title Placeholder

        :param indigo.Dict values_dict:
        :param Bool user_cancelled:
        :param str type_id:
        :param int dev_id:
        :return:
        """
        self.logger.debug('closedDeviceConfigUi() method called:')

        if user_cancelled:
            self.logger.debug("Device configuration cancelled.")

    # =============================================================================
    def closedPrefsConfigUi(self, values_dict, user_cancelled):  # noqa
        """
        Title Placeholder

        :param indigo.Dict values_dict:
        :param Bool user_cancelled:
        :return:
        """
        self.logger.debug("Plugin config dialog window closed.")

        if user_cancelled:
            self.logger.debug("User prefs dialog cancelled.")

            self.logger.debug("User prefs saved.")

            # Finally, update all device states upon close
            self.updateDeviceStates()

    # =============================================================================
    def deviceStartComm(self, dev):  # noqa
        """
        Title Placeholder

        :param indigo.Device dev:
        :return:
        """
        self.logger.debug(f"Starting OWServer device: {dev.name}")
        dev.stateListOrDisplayStateIdChanged()
        dev.updateStateOnServer('onOffState', value=True, uiValue=" ")

    # =============================================================================
    def deviceStopComm(self, dev):  # noqa
        """
        Title Placeholder

        :param indigo.Device dev:
        :return:
        """
        self.logger.debug(f"Stopping OWServer device: {dev.name}")
        dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

    # =============================================================================
    def runConcurrentThread(self):  # noqa
        """
        Title Placeholder

        :return:
        """
        self.logger.debug("Starting main OWServer thread.")

        # self.sleep(5)

        try:
            while True:
                self.spot_dead_sensors()
                self.updateDeviceStates()
                sleep_time = int(self.pluginPrefs.get('configMenuPollInterval', 900))
                self.sleep(sleep_time-5)

        except self.StopThread:
            self.logger.debug("Fatal error. Stopping OWServer thread.")

    # =============================================================================
    def shutdown(self):
        """
        Title placeholder

        Body placeholder

        :return:
        """
        self.plugin_is_shutting_down = True
        self.logger.debug("Shutting down OWServer plugin.")

    # =============================================================================
    def startup(self):
        """
        Title placeholder

        body placeholder

        :return:
        """
        self.logger.debug("Starting OWServer.")

        # =========================== Audit Server Version ============================
        self.Fogbert.audit_server_version(min_ver=2022)

    # =============================================================================
    def validatePrefsConfigUi(self, values_dict):  # noqa
        """
        Title placeholder

        :param indigo.Dict values_dict:
        :return:
        """
        self.logger.debug("validatePrefsConfigUi() method called.")

        address = values_dict['OWServerIP']
        auto_detect_servers = values_dict['autoDetectServers']
        error_msg_dict = indigo.Dict()
        split_ip = address.replace(" ", "").split(",")

        # A valid IP address must be at least 7 characters long.
        if not auto_detect_servers and len(address) < 7:
            error_msg_dict['OWServerIP'] = "An IP address is not long enough (at least 0.0.0.0)."
            return False, values_dict, error_msg_dict

        # Split apart the IP address(es) to ensure that they have at least four parts.
        if not auto_detect_servers:
            for server_ip in split_ip:
                address_parts = server_ip.split(".")
                if len(address_parts) != 4:
                    error_msg_dict['OWServerIP'] = (
                        "Please enter a valid IP address with four valid parts (0.0.0.0)."
                    )
                    return False, values_dict, error_msg_dict

                # Each part must be between the values of 0 and 255 (inclusive).
                for part in address_parts:
                    try:
                        part = int(part)
                        if part < 0 or part > 255:
                            error_msg_dict['OWServerIP'] = (
                                "You have entered a value out of range (not 0-255)."
                            )
                            return False, values_dict, error_msg_dict
                    except ValueError:
                        error_msg_dict['OWServerIP'] = (
                            "You have entered an IP address that contains a non-numeric character."
                        )
                        return False, values_dict, error_msg_dict

        return True, values_dict

    # =============================================================================
    # ============================== Plugin Methods ===============================
    # =============================================================================
    def sendToServer(self, val):  # noqa
        """
        Title Placeholder

        The sendToServer() method merely logs the url sent to the server for the purposes of
        confirmation and a signal that the event took place. This is a temporary method which will
        be removed if it's no longer needed.

        :param List val:
        """
        # https:// is not supported by the EDS server.
        write_url = (
            f"http://{val[0]}/devices.htm?rom={val[1]}&variable={val[2]}&value={val[3]}"  # noqa
        )

        try:
            reply = requests.get(write_url)

            self.logger.debug(f"Write to server URL: {write_url}")
            self.logger.debug(f"Reply: {reply}")

        except Exception:  # noqa
            self.logger.exception("sendToServer()")

    # =============================================================================
    def sendToServerAction(self, val):  # noqa
        """
        Title Placeholder

        The sendToServerExternal() method is for scripters to be able to send individual commands
        to devices through Indigo Python scripts. The syntax for the call is:
        =======================================================================
        pluginId = "com.fogbert.indigoplugin.OWServer"
        plugin = indigo.server.getPlugin(pluginId)
        props = {"server": "10.0.1.44",
                 "romId": "5D000003C74F4528",
                 "variable": "clearAlarms",
                 "value": "0"
                 }
        if plugin.isEnabled():
            plugin.executeAction("sendToServerAction", props)
        =======================================================================

        :param indigo.Dict val:
        """
        server   = val.props.get('server')
        rom_id   = val.props.get('romId')
        variable = val.props.get('variable')
        value    = val.props.get('value')
        write_url = f"https://{server}/devices.htm?rom={rom_id}&variable={variable}&value={value}"

        try:
            reply = requests.get(write_url)
            self.logger.debug(f"Write to server URL: {write_url}")
            self.logger.debug(f"Reply: {reply}")

        except Exception:  # noqa  # oqa
            self.logger.exception("sendToServerAction()")

    # =============================================================================
    def actionControlSensor(self, action, dev):  # noqa
        """
        Title Placeholder

        Get sensor update when user selects 'Send Status Request'. This updates all devices.

        :param indigo.PluginAction action:
        :param indigo.Device dev:
        """
        self.logger.debug("User request for status update.")
        self.logger.debug("actionControlSensor() method called.")
        self.updateDeviceStates()

    # =============================================================================
    def customWriteToDevice(self, values_dict, type_id):  # noqa
        """
        Title Placeholder

        The customWriteToDevice() method is called when a user selects the "Write Value to 1-Wire
        Device" item from the OWServer Plugin menu. Selecting this menu item causes a dialog to
        open which asks the user to select the relevant server IP and ROM ID, and enter both the
        variable to change and the value to write. There is limited error checking (obvious things)
        but mostly relies on user entering valid information.

        :param indigo.Dict values_dict:
        :param int type_id:
        """
        self.logger.debug('customWriteToDevice() method called.')

        error_msg_dict    = indigo.Dict()
        write_to_server   = values_dict['writeToServer']
        write_to_rom      = values_dict['writeToROM']       # "writeToROM" - alpha must be uppercase
        write_to_variable = values_dict['writeToVariable']  # "writeToVariable" - must be writeable
        write_to_value    = values_dict['writeToValue']     # "writeToValue" - must be decimal

        # We can only write decimal values to 1-Wire devices.  So let's check. We won't change
        # the value to something that will work but rather let the user know instead.
        if write_to_variable == "":
            error_msg_dict['writeToVariable'] = (
                "You must specify a value to write to the 1-Wire device."
            )
            return False, values_dict, error_msg_dict
        elif " " in write_to_variable:
            error_msg_dict['writeToVariable'] = "Variable names cannot contain a space."
            return False, values_dict, error_msg_dict

        if write_to_value == "":
            error_msg_dict['writeToValue'] = (
                "You must specify a value to write to the 1-Wire device."
            )
            return False, values_dict, error_msg_dict

        try:
            float(write_to_value)
        except Exception:  # noqa  # noqa
            error_msg_dict['writeToValue'] = "Only decimal values can be written to 1-Wire devices."
            return False, values_dict, error_msg_dict

        # All tests passed, so construct the URL to send to the server.
        write_to_url = (
            f"https://{write_to_server}/devices.htm?rom={write_to_rom}&variable={write_to_variable}"
            f"&value={write_to_value}"
        )

        self.logger.debug(f"URL constructed to post data to device: {write_to_url}")

        # Send the URL to the server.
        try:
            reply = requests.get(write_to_url)
            self.logger.info(f"{write_to_variable}: {write_to_value} written successfully.")
            self.logger.info(f"Reply: {reply}")
            return True

        # TODO - include requests exception handlers?
        # What happens if we're unsuccessful.
        # except urllib2.HTTPError as error:
        #     self.logger.exception()
        #     self.logger.critical("HTTP error writing server data.")
        #     error_msg_dict['writeToServer'] = f"{error.reason}"
        #     return False, values_dict, error_msg_dict
        except IOError as error:  # TODO: Check to see if these are IOErrors.
            self.logger.exception()
            self.logger.warning("Exception error getting server data.")
            # (no number, timed out)
            # (51, Network is unreachable) - OWServer has no LAN access
            # (50, Network is down) - EDS hardware offline
            # (54, Connection reset by peer) - EDS hardware offline
            error_msg_dict['writeToServer'] = f"{error}"
            return False, values_dict, error_msg_dict
        except Exception as error:
            self.logger.exception()
            self.logger.warning(
                "Misc. error downloading details.xml file. If the problem persists, please enable "
                "debugging in the OWServer configuration dialog and check user forum for more "
                "information."
            )
            error_msg_dict['writeToServer'] = f"{error}"
            return False, values_dict, error_msg_dict

    # =============================================================================
    def dumpXML(self, values_dict, type_id):  # noqa
        """
        Title Placeholder

        dumpXML(self, values_dict): This method grabs a copy of the details.xml file from the
        server at the specified IP address, parses it, and dumps a copy to a log file. The purpose
        is for the user to be able to confirm that the 1-Wire server is online and that the plugin
        can talk to it. Log file is written to the Indigo server logs folder.

        :param indigo.Dict values_dict:
        :param int type_id:
        """
        self.logger.debug("Dumping details.xml file to Indigo log file...")

        addr = values_dict['writeToServer']
        split_ip = addr.replace(" ", "").split(",")

        for server_ip in split_ip:
            try:
                ows_xml = self.get_details_xml(server_ip)
                if values_dict['writeXMLToLog']:
                    file_name = (
                        f"{indigo.server.getLogsFolderPath()}/{dt.datetime.today().date()} "
                        f"OWServer.txt"
                    )
                    with open(file_name, "w", encoding='utf-8') as data:
                        data.write("OWServer details.xml Log\n")
                        data.write(f"Written at: {dt.datetime.today()}\n")
                        data.write("=" * 72 + "\n")
                        data.write(str(ows_xml))

                if not ows_xml:
                    self.logger.critical(f"OWServer IP: {server_ip} failed.")
                else:
                    indigo.server.log(f"OWServer IP: {server_ip} passed.")

            except Exception:  # noqa
                self.logger.exception()
                self.logger.warning("Can't dump XML to log. Check server connection.")

    # =============================================================================
    def get_details_xml(self, server_ip):
        """
        Title Placeholder

        get_details_xml(): This method goes out to the 1-Wire server at the specified OWServerIP
        address and pulls in a copy of the details.xml file. It doesn't process it any way.

        :param str server_ip:
        """
        self.logger.debug("get_details_xml() method called.")

        try:
            # https:// not supported by EDS server.
            url      = f"http://{server_ip}/details.xml"  # noqa
            time_out = int(self.pluginPrefs.get('configMenuServerTimeout', 15))
            response = requests.get(url, timeout=time_out)
            self.logger.debug("details.xml file retrieved successfully.")
            return response.text

        # What happens if we're unsuccessful. No connection to Internet, no response from OWServer.
        # Let's keep trying.
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError
        ):
            self.logger.warning("Unable to make a successful connection to One Wire Server.")

        except Exception:  # noqa
            self.logger.exception()
            self.logger.warning(
                "Misc. error downloading details.xml file. If the problem persists, please enable "
                "debugging in the OWServer configuration dialog and check user forum for more "
                "information."
            )

    # =============================================================================
    def getSensorList(self, fltr="indigo.sensor", type_id=0, values_dict=None, target_id=0):  # noqa
        """
        Title Placeholder

        getSensorList(): This method constructs a list of 1-Wire sensors that have  been added to
        all servers. It's called when the user opens up a device config dialog. If there are no
        sensors left to assign (they have all been assigned to other devices) then the user is
        sent a message 'No sensors to add.' This string is necessary to address conditions where
        the method returns a noneType value instead of a list (Indigo throws an error when this
        happens.)

        :param str fltr:
        :param str type_id:
        :param indigo.Dict values_dict:
        :param str target_id:
        """
        self.logger.debug("getSensorList() method called.")
        self.logger.debug("Generating list of 1-Wire sensors...")

        server_list        = self.pluginPrefs.get('OWServerIP', None)
        clean_server_list  = server_list.replace(' ', '').split(',')
        sorted_server_list = sorted(clean_server_list)
        sorted_sensor_list = []
        sensor_id_list     = []

        for IP in sorted_server_list:
            try:
                ows_xml = self.get_details_xml(IP)
                root = eTree.fromstring(ows_xml)

                if self.pluginPrefs['showDebugInfo'] and self.pluginPrefs['showDebugLevel'] >= 3:
                    self.logger.debug(f"{ows_xml}")

                # Build a list of ROM IDs for all 1-Wire sensors on the network. We start  by
                # parsing out a list of all ROM IDs in the source details.xml file. The resulting
                # list is called "sensorID_list"
                for child in root:
                    if "owd_" in child.tag:
                        rom_id = child.find(self.xmlns + 'ROMId')
                        sensor_id_list += [rom_id.text]

                # If the list is empty, there are no ROM IDs in details.xml. Let's proceed with
                # an empty list.
                if sensor_id_list is None:
                    sensor_id_list = []

                # Sort the list (to make it easy to find the ROM ID needed), and return the list.
                sorted_sensor_list = sorted(sensor_id_list)

            except Exception:  # noqa
                self.logger.exception()
                self.logger.debug("Error reading sensor data from servers.")
                sorted_sensor_list = ["Error reading data from servers."]

        return sorted_sensor_list

    # =============================================================================
    def getServerList(self, fltr="indigo.sensor", type_id=0, values_dict=None, target_id=0):  # noqa
        """
        Title Placeholder

        getServerList(): This method provides the callback for defining server devices. It obtains
        its list of server IP addresses from one of two distinct procedures: (1) automatic server
        detection, and (2) manual declaration of server IPs. Within the plugin configuration
        dialog, the user either accepts automatic detection or else enters a comma delimited list
        of addresses. Despite whichever procedure is used, getServerList() returns a list
        (sorted_server_list) containing the list of IPs. This list is used to assign IP addresses
        when the user creates OWServer devices.

        :param str fltr:
        :param str type_id:
        :param indigo.Dict values_dict:
        :param int target_id:
        """
        self.logger.debug("getServerList() method called.")
        master_list = []
        my_socket = None

        if not self.pluginPrefs.get('autoDetectServers', True):
            server_list        = self.pluginPrefs.get('OWServerIP', None)
            clean_server_list  = server_list.replace(" ", "").split(",")
            sorted_server_list = sorted(clean_server_list)
            return sorted_server_list

        else:
            # We will ignore everything that responds to our UDP broadcast request unless it has
            # one of the following in its return.
            # FIXME - `server_list` is unused. Use it or lose it.
            server_list = [
                "OWServer_v2-Enet", "OWServer_v2G-WiFi", "OWServer-Enet", "OW_SERVER-Enet"
            ]

            try:
                socket.setdefaulttimeout(0.5)
                my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
                my_socket.sendto("D", ('<broadcast>', 30303))

                while True:
                    response = my_socket.recv(2048)
                    if response.find(b'{') >= 0:
                        response = response[response.find(b'{'):response.find(b'}')+1]

                        # This code removes a comma after the last field, which is sent in some
                        # older versions of EDS products.
                        comma_err = response.find(b',\r\n}')
                        if comma_err > 64:
                            response = response[:comma_err] + b'}'

                        # Unpack the response and add it to the server list.
                        j = json.loads(response)
                        master_list.append(j['IP'])

            except socket.timeout:
                my_socket.close()
                return sorted(master_list)

            except Exception as e:
                err = e.args
                if err[0] == 51:
                    self.logger.warning("The network is unreachable.")
                else:
                    self.logger.exception()
                return sorted(master_list)

    # =============================================================================
    def killAllComms(self):  # noqa
        """
        Set the enabled status of all plugin devices to false.
        """
        for dev in indigo.devices.itervalues("self"):
            if dev.enabled:
                indigo.device.enable(dev, value=False)

    # =============================================================================
    def unkillAllComms(self):  # noqa
        """
        Set the enabled status of all plugin devices to true.
        """
        for dev in indigo.devices.itervalues("self"):
            if not dev.enabled:
                indigo.device.enable(dev, value=True)

    # =============================================================================
    def spot_dead_sensors(self):
        """
        Log a warning when a sensor has been offline

        spot_dead_sensors(self): This method compares the time each plugin device was last updated
        to the current Indigo time. If the difference exceeds a set interval (currently set to 60
        seconds), then the sensor's onOffState is set to false and an error is thrown to the log.
        This condition could be for a number of reasons including sensor fail, wiring fail, 1-Wire
        network collisions, etc.
        """
        self.logger.debug("spot_dead_sensors() method called.")

        for dev in indigo.devices.itervalues("self"):
            if dev.enabled:
                diff_time = indigo.server.getTime() - dev.lastChanged
                pref_poll = int(self.pluginPrefs.get('configMenuPollInterval', 900))
                dead_time = (
                    dt.timedelta(seconds=pref_poll) +
                    dt.timedelta(seconds=60)
                )

                # If a sensor has been offline for more than the specified amount of time, throw a
                # message to the log and mark it offline. Starting with 60 seconds.
                if diff_time <= dead_time:
                    pass

                else:
                    self.logger.warning(
                        f"{dev.name} hasn't been updated in {diff_time}. If this condition "
                        f"persists, check it's connection."
                    )
                    try:
                        dev.updateStateOnServer('onOffState', value=False, uiValue="")
                    except Exception:  # noqa
                        self.logger.exception()
                        self.logger.warning("Unable to spot dead sensors.")

    # =============================================================================
    def humidex_convert(self, ows_humidex):
        """
        Title Placeholder

        humidex_convert(self): This method converts any humidex values used in the plugin based on
        user preference: self.pluginPrefs['configMenuHumidexDec'].

        :param str ows_humidex:
        """
        self.logger.debug("  Converting humidex values.")

        try:
            # Format the humidex value to the requested number of decimal places.
            format_humidex = f"%.{self.pluginPrefs.get('configMenuHumidexDec', '1')}f"
            ows_humidex = float(ows_humidex)
            ows_humidex = (format_humidex % ows_humidex)
            return ows_humidex

        except Exception:  # noqa
            self.logger.exception()
            self.logger.warning("Error formatting humidex value. Returning value unchanged.")
            return ows_humidex

    # =============================================================================
    def humidity_convert(self, ows_humidity):
        """
        Title Placeholder

        humidity_convert(self): This method converts any humidity values used in the plugin based on
        user preference: self.pluginPrefs['configMenuHumidityDec'].

        :param str ows_humidity:
        """
        self.logger.debug("  Converting humidity values.")

        try:
            # Format the humidity value to the requested number of decimal places.
            format_humidity = f"%.{self.pluginPrefs.get('configMenuHumidityDec', '1')}f"
            ows_humidity    = float(ows_humidity)
            ows_humidity    = (format_humidity % ows_humidity)
            return ows_humidity

        except Exception:  # noqa
            self.logger.exception()
            self.logger.warning("Error formatting humidity value. Returning value unchanged.")
            return ows_humidity

    # =============================================================================
    def pressure_convert(self, ows_pressure):
        """
        Title Placeholder

        pressure_convert(self): This method converts any pressure values used in the plugin based on
        user preference: self.pluginPrefs['configMenuPressureDec'].

        :param float ows_pressure:
        """
        self.logger.debug("  Converting pressure values.")

        try:
            # Format the pressure value to the requested number of decimal places.
            format_pressure = f"%.{self.pluginPrefs.get('configMenuPressureDec', '1')}f"
            ows_pressure = float(ows_pressure)
            ows_pressure = (format_pressure % ows_pressure)
            return ows_pressure

        except Exception:  # noqa
            self.logger.exception()
            self.logger.warning("Error formatting pressure value. Returning value unchanged.")
            return ows_pressure

    # =============================================================================
    def temp_convert(self, ows_temp):
        """
        Title Placeholder

        temp_convert(self): This method converts any temperature values used in the plugin based on
        user preference: self.pluginPrefs['configMenuDegreesDec']. This method returns a string
        that is formatted based on user preferences.

        :param float ows_temp:
        """
        self.logger.debug("  Converting temperature values.")

        # Format the temperature value to the requested number of decimal places.
        format_temp = f"%.{self.pluginPrefs.get('configMenuDegreesDec', '1')}f"

        if self.pluginPrefs.get('configMenuDegrees', 'F') == "C":
            ows_temp = float(ows_temp)
            ows_temp = (format_temp % ows_temp)

        elif self.pluginPrefs.get('configMenuDegrees', 'F') != "C":
            ows_temp = float(ows_temp) * 1.8000 + 32.00
            ows_temp = (format_temp % ows_temp)

        return ows_temp

    # =============================================================================
    def volts_convert(self, ows_volts):
        """
        Title Placeholder

        volts_convert(self): This method converts any voltages values used in the plugin based on
        user preference: self.pluginPrefs['configMenuVoltsDec']. This method returns a string that
        is formatted based on user preferences.

        :param str ows_volts:
        """
        self.logger.debug("  Converting volts values.")

        # Format the value to the requested number of decimal places.
        format_volts = f"%.{self.pluginPrefs.get('configMenuVoltsDec', '1')}f"
        ows_volts    = float(ows_volts)
        ows_volts    = (format_volts % ows_volts)
        return ows_volts

    # =============================================================================
    # ================== Server and Sensor Device Update Methods ==================
    # =============================================================================
    def updateOWServer(self, dev, root, server_ip):  # noqa
        """
        Title Placeholder

        Server Type: Covers OWSERVER-ENET Rev. 1 and Rev. 2

        :param indigo.Device dev:
        :param JSON root:
        :param str server_ip:
        """
        self.logger.debug("updateOWServer() method called.")

        try:
            server_state_dict = self.state_dict.server_state_dict()

            for key, value in server_state_dict.items():
                try:
                    dev.updateStateOnServer(key, value=root.find(self.xmlns + value).text)
                except AttributeError:
                    dev.updateStateOnServer(key, value="Unsupported")

            try:
                devices_connected = root.find(self.xmlns + 'DevicesConnected').text
                if devices_connected == "1":
                    input_value = f"{devices_connected} sensor"
                else:
                    input_value = f"{devices_connected} sensors"
                dev.updateStateOnServer('onOffState', value=True, uiValue=input_value)
                dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)

            except Exception:  # noqa
                self.logger.debug(f"Unable to update device state on server. Device: {dev.name}")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
                dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
                self.logger.exception()

            new_props = dev.pluginProps
            new_props['address'] = dev.states['owsMACAddress']
            dev.replacePluginPropsOnServer(new_props)

            self.number_of_servers += 1

            self.logger.debug("Success. Polling next server if appropriate.")
            return True

        except Exception:  # noqa
            self.logger.critical("Server update failure. Check settings.")
            self.logger.exception()
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateDS18B20(self, dev, ows_sensor, server_ip):  # noqa
        """
        Title Placeholder

        DS18B20 Description = "Programmable resolution thermometer"

        :param indigo.Device dev:
        :param XML ows_sensor:
        :param str server_ip:
        """
        self.logger.debug("updateDS18B20() method called.")

        try:
            ds18b20_state_dict = self.state_dict.ds18b20_state_dict()

            for key, value in ds18b20_state_dict.items():
                try:
                    if key == "owsTemperature":
                        ows_temp    = ows_sensor.find(self.xmlns + 'Temperature').text
                        comp_val    = dev.pluginProps.get('DS18B20TempComp', '0.0')
                        input_value = float(ows_temp) + float(comp_val)
                        input_value = self.temp_convert(input_value)
                        dev.updateStateOnServer(key, value=input_value)
                    else:
                        dev.updateStateOnServer(key, value=ows_sensor.find(self.xmlns + value).text)
                except Exception:  # noqa
                    self.logger.exception()
                    self.logger.debug(
                        f"Unable to update device state on server. Device: {dev.name}"
                    )
                    self.logger.debug(f"Key: {key} : Value: Unsupported")
                    dev.updateStateOnServer(key, value="Unsupported")

            try:
                ows_temp    = ows_sensor.find(self.xmlns + 'Temperature').text
                comp_val    = dev.pluginProps.get('DS18B20TempComp', '0.0')
                input_value = float(ows_temp) + float(comp_val)
                input_value = self.temp_convert(input_value)
                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)
            except Exception:  # noqa
                self.logger.exception()
                self.logger.debug(f"Unable to update device state on server. Device: {dev.name}")
                dev.updateStateOnServer('sensorValue', value="Unsupported", uiValue="Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']          = dev.states['owsRomID']
            new_props['DS18B20UserByte1'] = ows_sensor.find(self.xmlns + 'UserByte1').text
            new_props['DS18B20UserByte2'] = ows_sensor.find(self.xmlns + 'UserByte2').text
            dev.replacePluginPropsOnServer(new_props)

            self.number_of_sensors += 1

            dev.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)
            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.logger.debug("Success. Polling next sensor if appropriate.")
            return True

        except Exception:  # noqa
            self.logger.critical("Sensor update failure. Check connection.")
            self.logger.exception()
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateDS18S20(self, dev, ows_sensor, server_ip):  # noqa
        """
        Title Placeholder

        DS18S20 Description = "Parasite Power Thermometer"

        :param indigo.Device dev:
        :param XML ows_sensor:
        :param str server_ip:
        """
        self.logger.debug("updateDS18S20() method called.")

        try:
            ds18s20_state_dict = self.state_dict.ds18s20_state_dict()

            for key, value in ds18s20_state_dict.items():
                try:
                    if key == "owsTemperature":
                        ows_temp    = ows_sensor.find(self.xmlns + 'Temperature').text
                        comp_val    = dev.pluginProps.get('DS18S20TempComp', '0.0')
                        input_value = float(ows_temp) + float(comp_val)
                        input_value = self.temp_convert(input_value)
                        dev.updateStateOnServer(key, value=input_value)
                    else:
                        dev.updateStateOnServer(key, value=ows_sensor.find(self.xmlns + value).text)
                except Exception:  # noqa
                    self.logger.exception()
                    self.logger.debug(
                        f"Unable to update device state on server. Device: {dev.name}"
                    )
                    self.logger.debug(f"Key: {key} : Value: Unsupported")
                    dev.updateStateOnServer(key, value="Unsupported")

            try:
                ows_temp    = ows_sensor.find(self.xmlns + 'Temperature').text
                comp_val    = dev.pluginProps.get('DS18S20TempComp', '0.0')
                input_value = float(ows_temp) + float(comp_val)
                input_value = self.temp_convert(input_value)
                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)
            except Exception:  # noqa
                self.logger.debug(f"Unable to update device state on server. Device: {dev.name}")
                dev.updateStateOnServer('sensorValue', value="Unsupported", uiValue="Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']          = dev.states['owsRomID']
            new_props['DS18S20UserByte1'] = ows_sensor.find(self.xmlns + 'UserByte1').text
            new_props['DS18S20UserByte2'] = ows_sensor.find(self.xmlns + 'UserByte2').text
            dev.replacePluginPropsOnServer(new_props)

            self.number_of_sensors += 1

            dev.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)
            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.logger.debug("Success. Polling next sensor if appropriate.")
            return True

        except Exception:  # noqa
            self.logger.critical("Sensor update failure. Check connection.")
            self.logger.exception()
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateDS2406(self, dev, ows_sensor, server_ip):  # noqa
        """
        Title Placeholder

        DS2406 Description = "Dual Addressable Switch Plus Memory"

        :param indigo.Device dev:
        :param XML ows_sensor:
        :param str server_ip:
        """
        self.logger.debug("updateDS2406() method called.")

        try:
            ds2406_state_dict = self.state_dict.ds2406_state_dict()
            input_value = None

            for key, value in ds2406_state_dict.items():
                try:
                    dev.updateStateOnServer(key, value=ows_sensor.find(self.xmlns + value).text)
                except Exception:  # noqa
                    self.logger.exception()
                    self.logger.debug(
                        f"Unable to update device state on server. Device: {dev.name}"
                    )
                    self.logger.debug(f"Key: {key} : Value: Unsupported")
                    dev.updateStateOnServer(key, value="Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue2406'] == "I_A":  # Input Level A
                    input_value = ows_sensor.find(self.xmlns + 'InputLevel_A').text
                    if input_value == "0":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue2406'] == "I_B":  # Input Level B
                    input_value = ows_sensor.find(self.xmlns + 'InputLevel_B').text
                    if input_value == "0":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:  # noqa
                self.logger.exception()
                self.logger.debug(f"Unable to update device state on server. Device: {dev.name}")
                dev.updateStateOnServer('sensorValue', value="Unsupported", uiValue="Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address'] = dev.states['owsRomID']
            new_props['DS2406ActivityLatchReset'] = ows_sensor.find(self.xmlns +
                                                                    'ActivityLatchReset').text
            dev.replacePluginPropsOnServer(new_props)

            self.number_of_sensors += 1

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.logger.debug("Success. Polling next sensor if appropriate.")
            return True

        except Exception:  # noqa
            self.logger.critical("Sensor update failure. Check connection.")
            self.logger.exception()
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateDS2408(self, dev, ows_sensor, server_ip):  # noqa
        """
        Title Placeholder

        DS2408 Description = "8-Channel Addressable Switch"

        :param indigo.Device dev:
        :param XML ows_sensor:
        :param str server_ip:
        """
        self.logger.debug("updateDS2408() method called.")

        try:
            ds2408_state_dict = self.state_dict.ds2408_state_dict()
            input_value = None

            for key, value in ds2408_state_dict.items():
                try:
                    dev.updateStateOnServer(key, value=ows_sensor.find(self.xmlns + value).text)
                except Exception:  # noqa
                    self.logger.exception()
                    self.logger.debug(
                        f"Unable to update device state on server. Device: {dev.name}"
                    )
                    self.logger.debug(f"Key: {key} : Value: Unsupported")
                    dev.updateStateOnServer(key, value="Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                # We need to parse the switch state out of the binary number stored in
                # PIOOutputLatchState.
                latch_state     = float(dev.states['owsPIOOutputLatchState'])
                latch_state_int = int(latch_state)
                latch_state_bin = int(bin(latch_state_int)[2:])
                latch_state_str = str(latch_state_bin)
                latch_state_str = latch_state_str.zfill(8)

                # These states don't exist in the details.xml file. We impute them from
                # <PIOOutputLatchState>.
                dev.updateStateOnServer('owsInput1', value=latch_state_str[0])
                dev.updateStateOnServer('owsInput2', value=latch_state_str[1])
                dev.updateStateOnServer('owsInput3', value=latch_state_str[2])
                dev.updateStateOnServer('owsInput4', value=latch_state_str[3])
                dev.updateStateOnServer('owsInput5', value=latch_state_str[4])
                dev.updateStateOnServer('owsInput6', value=latch_state_str[5])
                dev.updateStateOnServer('owsInput7', value=latch_state_str[6])
                dev.updateStateOnServer('owsInput8', value=latch_state_str[7])

                if dev.pluginProps['prefSensorValue2408'] == "S_0":  # Switch 0
                    input_value = latch_state_str[7]
                    if input_value == "0":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue2408'] == "S_1":  # Switch 1
                    input_value = latch_state_str[6]
                    if input_value == "0":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue2408'] == "S_2":  # Switch 2
                    input_value = latch_state_str[5]
                    if input_value == "0":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue2408'] == "S_3":  # Switch 3
                    input_value = latch_state_str[4]
                    if input_value == "0":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue2408'] == "S_4":  # Switch 4
                    input_value = latch_state_str[3]
                    if input_value == "0":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue2408'] == "S_5":  # Switch 5
                    input_value = latch_state_str[2]
                    if input_value == "0":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue2408'] == "S_6":  # Switch 6
                    input_value = latch_state_str[1]
                    if input_value == "0":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue2408'] == "S_7":  # Switch 7
                    input_value = latch_state_str[0]
                    if input_value == "0":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:  # noqa
                self.logger.exception()
                self.logger.debug(f"Unable to update device state on server. Device: {dev.name}")
                dev.updateStateOnServer('sensorValue', value="Unsupported", uiValue="Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address'] = dev.states['owsRomID']

            new_props['DS2408PIOActivityLatchState'] = (
                ows_sensor.find(self.xmlns + 'PIOActivityLatchState').text
            )
            new_props['DS2408PIOOutputLatchState'] = (
                ows_sensor.find(self.xmlns + 'PIOOutputLatchState').text
            )
            new_props['DS2408PowerOnResetLatch'] = (
                ows_sensor.find(self.xmlns + 'PowerOnResetLatch').text
            )
            new_props['DS2408RSTZconfiguration'] = (
                ows_sensor.find(self.xmlns + 'RSTZconfiguration').text
            )
            dev.replacePluginPropsOnServer(new_props)

            self.number_of_sensors += 1

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.logger.debug("Success. Polling next sensor if appropriate.")
            return True

        except Exception:  # noqa
            self.logger.critical("Sensor update failure. Check connection.")
            self.logger.exception()
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateDS2423(self, dev, ows_sensor, server_ip):  # noqa
        """
        Title Placeholder

        DS2423 Description = "RAM with Counters"

        :param indigo.Device dev:
        :param XML ows_sensor:
        :param str server_ip:
        """
        self.logger.debug("updateDS2423() method called.")

        try:
            ds2423_state_dict = self.state_dict.ds2423_state_dict()
            input_value = None

            for key, value in ds2423_state_dict.items():
                try:
                    dev.updateStateOnServer(key, value=ows_sensor.find(self.xmlns + value).text)
                except Exception:  # noqa
                    self.logger.exception()
                    self.logger.debug(
                        f"Unable to update device state on server. Device: {dev.name}"
                    )
                    self.logger.debug(f"Key: {key} : Value: Unsupported")
                    dev.updateStateOnServer(key, value="Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue2423'] == "C_A":  # Counter A
                    input_value = ows_sensor.find(self.xmlns + 'Counter_A').text
                if dev.pluginProps['prefSensorValue2423'] == "C_B":  # Counter B
                    input_value = ows_sensor.find(self.xmlns + 'Counter_B').text

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)
                dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

            except Exception:  # noqa
                self.logger.exception()
                self.logger.debug(f"Unable to update device state on server. Device: {dev.name}")
                dev.updateStateOnServer('sensorValue', value="Unsupported", uiValue="Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            # The DS2423 does not have any writable parameters.
            new_props = dev.pluginProps
            new_props['address'] = dev.states['owsRomID']
            dev.replacePluginPropsOnServer(new_props)

            self.number_of_sensors += 1

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
            self.logger.debug("Success. Polling next sensor if appropriate.")
            return True

        except Exception:  # noqa
            self.logger.critical("Sensor update failure. Check connection.")
            self.logger.exception()
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateDS2438(self, dev, ows_sensor, server_ip):  # noqa
        """
        Title Placeholder

        DS2438 Description = "Smart battery monitor"

        :param indigo.Device dev:
        :param XML ows_sensor:
        :param str server_ip:
        """
        self.logger.debug("updateDS2438() method called.")

        try:
            ds2438_state_dict = self.state_dict.ds2438_state_dict()

            for key, value in ds2438_state_dict.items():
                try:
                    if key == "owsTemperature":
                        ows_temp = ows_sensor.find(self.xmlns + 'Temperature').text
                        comp_val = dev.pluginProps.get('DS2438TempComp', '0.0')
                        input_value = float(ows_temp) + float(comp_val)
                        input_value = self.temp_convert(input_value)
                        dev.updateStateOnServer(key, value=input_value)
                    else:
                        dev.updateStateOnServer(key, value=ows_sensor.find(self.xmlns + value).text)
                except Exception:  # noqa
                    self.logger.exception()
                    self.logger.debug(
                        f"Unable to update device state on server. Device: {dev.name}"
                    )
                    self.logger.debug(f"Key: {key} : Value: Unsupported")
                    dev.updateStateOnServer(key, value="Unsupported")

            try:
                ows_temp = ows_sensor.find(self.xmlns + 'Temperature').text
                comp_val = dev.pluginProps.get('DS2438TempComp', '0.0')
                input_value = float(ows_temp) + float(comp_val)
                input_value = self.temp_convert(input_value)
                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)
            except Exception:  # noqa
                self.logger.exception()
                self.logger.debug(f"Unable to update device state on server. Device: {dev.name}")
                dev.updateStateOnServer('sensorValue', value="Unsupported", uiValue="Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            # The DS2438 does not have any writable parameters.
            new_props = dev.pluginProps
            new_props['address'] = dev.states['owsRomID']
            dev.replacePluginPropsOnServer(new_props)

            self.number_of_sensors += 1

            dev.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)
            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.logger.debug("Success. Polling next sensor if appropriate.")
            return True

        except Exception:  # noqa
            self.logger.critical("Sensor update failure. Check connection.")
            self.logger.exception()
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateDS2450(self, dev, ows_sensor, server_ip):  # noqa
        """
        Title Placeholder

        DS2450 Description = "Quad A/D Converter"

        :param indigo.Device dev:
        :param XML ows_sensor:
        :param str server_ip:
        """
        self.logger.debug("updateDS2450() method called.")

        try:
            ds2450_state_dict = self.state_dict.ds2450_state_dict()
            input_value = None

            for key, value in ds2450_state_dict.items():
                try:
                    dev.updateStateOnServer(key, value=ows_sensor.find(self.xmlns + value).text)
                except Exception:  # noqa
                    self.logger.exception()
                    self.logger.debug(
                        f"Unable to update device state on server. Device: {dev.name}"
                    )
                    self.logger.debug(f"Key: {key} : Value: Unsupported")
                    dev.updateStateOnServer(key, value="Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue2450'] == "C_A":  # Counter A
                    input_value = ows_sensor.find(self.xmlns + 'ChannelAConversionValue').text
                elif dev.pluginProps['prefSensorValue2450'] == "C_B":  # Counter B
                    input_value = ows_sensor.find(self.xmlns + 'ChannelBConversionValue').text
                elif dev.pluginProps['prefSensorValue2450'] == "C_C":  # Counter C
                    input_value = ows_sensor.find(self.xmlns + 'ChannelCConversionValue').text
                elif dev.pluginProps['prefSensorValue2450'] == "C_D":  # Counter D
                    input_value = ows_sensor.find(self.xmlns + 'ChannelDConversionValue').text

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)
                dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

            except Exception:  # noqa
                self.logger.exception()
                self.logger.debug(f"Unable to update device state on server. Device: {dev.name}")
                dev.updateStateOnServer('sensorValue', value="Unsupported", uiValue="Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']                            = dev.states['owsRomID']
            new_props['DS2450ChannelAConversionRange']      = ows_sensor.find(self.xmlns + 'ChannelAConversionRange').text
            new_props['DS2450ChannelAConversionResolution'] = ows_sensor.find(self.xmlns + 'ChannelAConversionResolution').text
            new_props['DS2450ChannelAOutputControl']        = ows_sensor.find(self.xmlns + 'ChannelAOutputControl').text
            new_props['DS2450ChannelAOutputEnable']         = ows_sensor.find(self.xmlns + 'ChannelAOutputEnable').text
            new_props['DS2450ChannelBConversionRange']      = ows_sensor.find(self.xmlns + 'ChannelBConversionRange').text
            new_props['DS2450ChannelBConversionResolution'] = ows_sensor.find(self.xmlns + 'ChannelBConversionResolution').text
            new_props['DS2450ChannelBOutputControl']        = ows_sensor.find(self.xmlns + 'ChannelBOutputControl').text
            new_props['DS2450ChannelBOutputEnable']         = ows_sensor.find(self.xmlns + 'ChannelBOutputEnable').text
            new_props['DS2450ChannelCConversionRange']      = ows_sensor.find(self.xmlns + 'ChannelCConversionRange').text
            new_props['DS2450ChannelCConversionResolution'] = ows_sensor.find(self.xmlns + 'ChannelCConversionResolution').text
            new_props['DS2450ChannelCOutputControl']        = ows_sensor.find(self.xmlns + 'ChannelCOutputControl').text
            new_props['DS2450ChannelCOutputEnable']         = ows_sensor.find(self.xmlns + 'ChannelCOutputEnable').text
            new_props['DS2450ChannelDConversionRange']      = ows_sensor.find(self.xmlns + 'ChannelDConversionRange').text
            new_props['DS2450ChannelDConversionResolution'] = ows_sensor.find(self.xmlns + 'ChannelDConversionResolution').text
            new_props['DS2450ChannelDOutputControl']        = ows_sensor.find(self.xmlns + 'ChannelDOutputControl').text
            new_props['DS2450ChannelDOutputEnable']         = ows_sensor.find(self.xmlns + 'ChannelDOutputEnable').text
            new_props['DS2450PowerOnReset']                 = ows_sensor.find(self.xmlns + 'PowerOnReset').text
            new_props['DS2450VCCControl']                   = ows_sensor.find(self.xmlns + 'VCCControl').text
            dev.replacePluginPropsOnServer(new_props)

            self.number_of_sensors += 1

            dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.logger.debug("Success. Polling next sensor if appropriate.")
            return True

        except Exception:  # noqa
            self.logger.critical("Sensor update failure. Check connection.")
            self.logger.exception()
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0064(self, dev, ows_sensor, server_ip):  # noqa
        """
        Title Placeholder

        EDS0064 Description = "Octal Current Input Device"

        :param indigo.Device dev:
        :param XML ows_sensor:
        :param str server_ip:
        """
        self.logger.debug("updateEDS0064() method called.")

        try:
            eds0064_state_dict = self.state_dict.eds0064_state_dict()
            input_value = None

            for key, value in eds0064_state_dict.items():
                try:
                    if key == "owsTemperature":
                        ows_temp = ows_sensor.find(self.xmlns + 'Temperature').text
                        comp_val = dev.pluginProps.get('EDS0064TempComp', '0.0')
                        input_value = float(ows_temp) + float(comp_val)
                        input_value = self.temp_convert(input_value)
                        dev.updateStateOnServer(key, value=input_value)
                    else:
                        dev.updateStateOnServer(key, value=ows_sensor.find(self.xmlns + value).text)
                except Exception:  # noqa
                    self.logger.exception()
                    self.logger.debug(
                        f"Unable to update device state on server. Device: {dev.name}"
                    )
                    self.logger.debug(f"Key: {key} : Value: Unsupported")
                    dev.updateStateOnServer(key, value="Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0064'] == "C_1":  # Counter 1
                    input_value = ows_sensor.find(self.xmlns + 'Counter1').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0064'] == "C_2":  # Counter 2
                    input_value = ows_sensor.find(self.xmlns + 'Counter2').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0064'] == "LED":  # LED
                    input_value = ows_sensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0064'] == "Relay":  # Relay
                    input_value = ows_sensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0064'] == "T":  # Temperature
                    ows_temp = ows_sensor.find(self.xmlns + 'Temperature').text
                    comp_val = dev.pluginProps.get('EDS0064TempComp', '0.0')
                    input_value = float(ows_temp) + float(comp_val)
                    input_value = self.temp_convert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:  # noqa
                self.logger.exception()
                self.logger.debug(f"Unable to update device state on server. Device: {dev.name}")
                dev.updateStateOnServer('sensorValue', value="Unsupported", uiValue="Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']                          = dev.states['owsRomID']
            new_props['EDS0064LEDFunction']               = ows_sensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0064RelayFunction']             = ows_sensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0064TemperatureHighAlarmValue'] = ows_sensor.find(self.xmlns + 'TemperatureHighAlarmValue').text
            new_props['EDS0064TemperatureLowAlarmValue']  = ows_sensor.find(self.xmlns + 'TemperatureLowAlarmValue').text
            dev.replacePluginPropsOnServer(new_props)

            self.number_of_sensors += 1

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.logger.debug("Success. Polling next sensor if appropriate.")
            return True

        except Exception:  # noqa
            self.logger.critical("Sensor update failure. Check connection.")
            self.logger.exception()
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0065(self, dev, ows_sensor, server_ip):  # noqa
        """
        Title Placeholder

        EDS0065 Description = "Temperature and Humidity Sensor"

        :param indigo.Device dev:
        :param XML ows_sensor:
        :param str server_ip:
        """
        self.logger.debug("updateEDS0065() method called.")

        try:
            eds0065_state_dict = self.state_dict.eds0065_state_dict()
            input_value = None

            for key, value in eds0065_state_dict.items():
                try:
                    if key == "owsTemperature":
                        ows_temp = ows_sensor.find(self.xmlns + 'Temperature').text
                        comp_val = dev.pluginProps.get('EDS0065TempComp', '0.0')
                        input_value = float(ows_temp) + float(comp_val)
                        input_value = self.temp_convert(input_value)
                        dev.updateStateOnServer(key, value=input_value)
                    else:
                        dev.updateStateOnServer(key, value=ows_sensor.find(self.xmlns + value).text)
                except Exception:  # noqa
                    self.logger.exception()
                    self.logger.debug(
                        f"Unable to update device state on server. Device: {dev.name}"
                    )
                    self.logger.debug(f"Key: {key} : Value: Unsupported")
                    dev.updateStateOnServer(key, value="Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0065'] == "C_1":  # Counter 1
                    input_value = ows_sensor.find(self.xmlns + 'Counter1').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0065'] == "C_2":  # Counter 2
                    input_value = ows_sensor.find(self.xmlns + 'Counter2').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0065'] == "DP":  # Dew Point
                    dew_point = ows_sensor.find(self.xmlns + 'DewPoint').text
                    input_value = self.temp_convert(dew_point)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0065'] == "Hu":  # Humidity
                    humidity = ows_sensor.find(self.xmlns + 'Humidity').text
                    input_value = self.humidity_convert(humidity)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0065'] == "Hx":  # Humidex
                    humidex = ows_sensor.find(self.xmlns + 'Humidex').text
                    input_value = self.humidex_convert(humidex)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0065'] == "HI":  # Heat Index
                    heat_index = ows_sensor.find(self.xmlns + 'HeatIndex').text
                    input_value = self.temp_convert(heat_index)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0065'] == "LED":  # LED
                    input_value = ows_sensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0065'] == "Relay":  # Relay
                    input_value = ows_sensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0065'] == "T":  # Temperature
                    ows_temp = ows_sensor.find(self.xmlns + 'Temperature').text
                    comp_val = dev.pluginProps.get('EDS0065TempComp', '0.0')
                    input_value = float(ows_temp) + float(comp_val)
                    input_value = self.temp_convert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:  # noqa
                self.logger.exception()
                self.logger.debug(f"Unable to update device state on server. Device: {dev.name}")
                dev.updateStateOnServer('sensorValue', value="Unsupported", uiValue="Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address'] = dev.states['owsRomID']
            new_props['EDS0065DewPointHighAlarmValue']    = ows_sensor.find(self.xmlns + 'DewPointHighAlarmValue').text
            new_props['EDS0065DewPointLowAlarmValue']     = ows_sensor.find(self.xmlns + 'DewPointLowAlarmValue').text
            new_props['EDS0065HeatIndexHighAlarmValue']   = ows_sensor.find(self.xmlns + 'HeatIndexHighAlarmValue').text
            new_props['EDS0065HeatIndexLowAlarmValue']    = ows_sensor.find(self.xmlns + 'HeatIndexLowAlarmValue').text
            new_props['EDS0065HumidexHighAlarmValue']     = ows_sensor.find(self.xmlns + 'HumidexHighAlarmValue').text
            new_props['EDS0065HumidexLowAlarmValue']      = ows_sensor.find(self.xmlns + 'HumidexLowAlarmValue').text
            new_props['EDS0065HumidityHighAlarmValue']    = ows_sensor.find(self.xmlns + 'HumidityHighAlarmValue').text
            new_props['EDS0065HumidityLowAlarmValue']     = ows_sensor.find(self.xmlns + 'HumidityLowAlarmValue').text
            new_props['EDS0065LEDFunction']               = ows_sensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0065RelayFunction']             = ows_sensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0065TemperatureHighAlarmValue'] = ows_sensor.find(self.xmlns + 'TemperatureHighAlarmValue').text
            new_props['EDS0065TemperatureLowAlarmValue']  = ows_sensor.find(self.xmlns + 'TemperatureLowAlarmValue').text
            dev.replacePluginPropsOnServer(new_props)

            self.number_of_sensors += 1

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.logger.debug("Success. Polling next sensor if appropriate.")
            return True

        except Exception:  # noqa
            self.logger.critical("Sensor update failure. Check connection.")
            self.logger.exception()
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0066(self, dev, ows_sensor, server_ip):  # noqa
        """
        Title Placeholder

        EDS0066 Description = "Temperature and Barometric Pressure Sensor"

        :param indigo.Device dev:
        :param XML ows_sensor:
        :param str server_ip:
        """
        self.logger.debug("updateEDS0066() method called.")

        try:
            eds0066_state_dict = self.state_dict.eds0066_state_dict()
            input_value = None

            for key, value in eds0066_state_dict.items():
                try:
                    if key == "owsTemperature":
                        ows_temp = ows_sensor.find(self.xmlns + 'Temperature').text
                        comp_val = dev.pluginProps.get('EDS0066TempComp', '0.0')
                        input_value = float(ows_temp) + float(comp_val)
                        input_value = self.temp_convert(input_value)
                        dev.updateStateOnServer(key, value=input_value)
                    else:
                        dev.updateStateOnServer(key, value=ows_sensor.find(self.xmlns + value).text)
                except Exception:  # noqa
                    self.logger.exception()
                    self.logger.debug(
                        f"Unable to update device state on server. Device: {dev.name}"
                    )
                    self.logger.debug(f"Key: {key} : Value: Unsupported")
                    dev.updateStateOnServer(key, value="Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0066'] == "C_1":  # Counter 1
                    input_value = ows_sensor.find(self.xmlns + 'Counter1').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0066'] == "C_2":  # Counter 2
                    input_value = ows_sensor.find(self.xmlns + 'Counter2').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0066'] == "BPH":  # Barometric Pressure (Mb)
                    bph = ows_sensor.find(self.xmlns + 'BarometricPressureHg').text
                    input_value = self.pressure_convert(bph)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.LightSensor)
                elif dev.pluginProps['prefSensorValue0066'] == "BPM":  # Barometric Pressure (Hg)
                    bpm = ows_sensor.find(self.xmlns + 'BarometricPressureMb').text
                    input_value = self.pressure_convert(bpm)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0066'] == "LED":  # LED
                    input_value = ows_sensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0066'] == "Relay":  # Relay
                    input_value = ows_sensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0066'] == "T":  # Temperature
                    ows_temp = ows_sensor.find(self.xmlns + 'Temperature').text
                    comp_val = dev.pluginProps.get('EDS0066TempComp', '0.0')
                    input_value = float(ows_temp) + float(comp_val)
                    input_value = self.temp_convert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:  # noqa
                self.logger.exception()
                self.logger.debug(f"Unable to update device state on server. Device: {dev.name}")
                dev.updateStateOnServer('sensorValue', value="Unsupported", uiValue="Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']                                   = dev.states['owsRomID']
            new_props['EDS0066BarometricPressureHgHighAlarmValue'] = ows_sensor.find(self.xmlns + 'BarometricPressureHgHighAlarmValue').text
            new_props['EDS0066BarometricPressureHgLowAlarmValue']  = ows_sensor.find(self.xmlns + 'BarometricPressureHgLowAlarmValue').text
            new_props['EDS0066BarometricPressureMbHighAlarmValue'] = ows_sensor.find(self.xmlns + 'BarometricPressureMbHighAlarmValue').text
            new_props['EDS0066BarometricPressureMbLowAlarmValue']  = ows_sensor.find(self.xmlns + 'BarometricPressureMbLowAlarmValue').text
            new_props['EDS0066LEDFunction']                        = ows_sensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0066RelayFunction']                      = ows_sensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0066TemperatureHighAlarmValue']          = ows_sensor.find(self.xmlns + 'TemperatureHighAlarmValue').text
            new_props['EDS0066TemperatureLowAlarmValue']           = ows_sensor.find(self.xmlns + 'TemperatureLowAlarmValue').text
            dev.replacePluginPropsOnServer(new_props)

            self.number_of_sensors += 1

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.logger.debug("Success. Polling next sensor if appropriate.")
            return True

        except Exception:  # noqa
            self.logger.critical("Sensor update failure. Check connection.")
            self.logger.exception()
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0067(self, dev, ows_sensor, server_ip):  # noqa
        """
        Title Placeholder

        EDS0067 Description = "Temperature and Light Sensor"

        :param indigo.Device dev:
        :param XML ows_sensor:
        :param str server_ip:
        """
        self.logger.debug("updateEDS0067() method called.")

        try:
            eds0067_state_dict = self.state_dict.eds0067_state_dict()
            input_value = None

            for key, value in eds0067_state_dict.items():
                try:
                    if key == "owsTemperature":
                        ows_temp = ows_sensor.find(self.xmlns + 'Temperature').text
                        comp_val = dev.pluginProps.get('EDS0067TempComp', '0.0')
                        input_value = float(ows_temp) + float(comp_val)
                        input_value = self.temp_convert(input_value)
                        dev.updateStateOnServer(key, value=input_value)
                    else:
                        dev.updateStateOnServer(key, value=ows_sensor.find(self.xmlns + value).text)
                except Exception:  # noqa
                    self.logger.exception()
                    self.logger.debug(
                        f"Unable to update device state on server. Device: {dev.name}"
                    )
                    self.logger.debug(f"Key: {key} : Value: Unsupported")
                    dev.updateStateOnServer(key, value="Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0067'] == "C_1":  # Counter 1
                    input_value = ows_sensor.find(self.xmlns + 'Counter1').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0067'] == "C_2":  # Counter 2
                    input_value = ows_sensor.find(self.xmlns + 'Counter2').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0067'] == "IL":  # Illumination
                    input_value = ows_sensor.find(self.xmlns + 'Light').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.LightSensor)
                elif dev.pluginProps['prefSensorValue0067'] == "LED":  # LED
                    input_value = ows_sensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0067'] == "Relay":  # Relay
                    input_value = ows_sensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0067'] == "T":  # Temperature
                    ows_temp = ows_sensor.find(self.xmlns + 'Temperature').text
                    comp_val = dev.pluginProps.get('EDS0067TempComp', '0.0')
                    input_value = float(ows_temp) + float(comp_val)
                    input_value = self.temp_convert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:  # noqa
                self.logger.exception()
                self.logger.debug(f"Unable to update device state on server. Device: {dev.name}")
                dev.updateStateOnServer('sensorValue', value="Unsupported", uiValue="Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']                          = dev.states['owsRomID']
            new_props['EDS0067LEDFunction']               = ows_sensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0067LightHighAlarmValue']       = ows_sensor.find(self.xmlns + 'LightHighAlarmValue').text
            new_props['EDS0067LightLowAlarmValue']        = ows_sensor.find(self.xmlns + 'LightLowAlarmValue').text
            new_props['EDS0067RelayFunction']             = ows_sensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0067TemperatureHighAlarmValue'] = ows_sensor.find(self.xmlns + 'TemperatureHighAlarmValue').text
            new_props['EDS0067TemperatureLowAlarmValue']  = ows_sensor.find(self.xmlns + 'TemperatureLowAlarmValue').text
            dev.replacePluginPropsOnServer(new_props)

            self.number_of_sensors += 1

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.logger.debug("Success. Polling next sensor if appropriate.")
            return True

        except Exception:  # noqa
            self.logger.critical("Sensor update failure. Check connection.")
            self.logger.exception()
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0068(self, dev, ows_sensor, server_ip):  # noqa
        """
        Title Placeholder

        EDS0068 Description = "Temperature, Humidity,Barometric Pressure and Light Sensor"

        :param indigo.Device dev:
        :param XML ows_sensor:
        :param str server_ip:
        """
        self.logger.debug("updateEDS0068() method called.")
        local = {}
        try:
            local['eds0068_state_dict'] = self.state_dict.eds0068_state_dict()

            for key, value in local['eds0068_state_dict'].items():
                try:
                    if key == "owsTemperature":
                        local['ows_temp'] = float(ows_sensor.find(self.xmlns + 'Temperature').text)
                        comp_val = float(dev.pluginProps.get('EDS0068TempComp', 0.0))
                        local['input_value'] = local['ows_temp'] + comp_val
                        local['input_value'] = self.temp_convert(float(local['input_value']))
                        dev.updateStateOnServer(key, value=local['input_value'])
                    else:
                        dev.updateStateOnServer(key, value=ows_sensor.find(self.xmlns + value).text)
                except Exception:  # noqa
                    self.logger.exception()
                    self.logger.debug(
                        f"Unable to update device state on server. Device: {dev.name}"
                    )
                    self.logger.debug(f"Key: {key} : Value: Unsupported")
                    dev.updateStateOnServer(key, value="Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0068'] == "BH":  # Barometric pressure HG
                    ows_baro_hg = float(ows_sensor.find(self.xmlns + 'BarometricPressureHg').text)
                    local['input_value'] = self.pressure_convert(ows_baro_hg)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0068'] == "BM":  # Barometric pressure MB
                    ows_baro_mb = float(ows_sensor.find(self.xmlns + 'BarometricPressureMb').text)
                    local['input_value'] = self.pressure_convert(ows_baro_mb)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0068'] == "C_1":  # Counter 1
                    local['input_value'] = ows_sensor.find(self.xmlns + 'Counter1').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0068'] == "C_2":  # Counter 2
                    local['input_value'] = ows_sensor.find(self.xmlns + 'Counter2').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0068'] == "DP":  # Dewpoint
                    dewpoint = ows_sensor.find(self.xmlns + 'DewPoint').text
                    local['input_value'] = self.temp_convert(dewpoint)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0068'] == "HI":  # Heat Index
                    heat_index = ows_sensor.find(self.xmlns + 'HeatIndex').text
                    local['input_value'] = self.temp_convert(heat_index)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0068'] == "HX":  # Humidex
                    ows_humidex = ows_sensor.find(self.xmlns + 'Humidex').text
                    local['input_value'] = self.humidex_convert(ows_humidex)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0068'] == "HY":  # Humidity
                    ows_humidity = ows_sensor.find(self.xmlns + 'Humidity').text
                    local['input_value'] = self.humidity_convert(ows_humidity)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0068'] == "IL":  # Illumination
                    local['input_value'] = ows_sensor.find(self.xmlns + 'Light').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.LightSensor)
                elif dev.pluginProps['prefSensorValue0068'] == "LED":  # LED
                    local['input_value'] = ows_sensor.find(self.xmlns + 'LED').text
                    if local['input_value'] == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0068'] == "Relay":  # Relay
                    local['input_value'] = ows_sensor.find(self.xmlns + 'Relay').text
                    if local['input_value'] == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0068'] == "T":  # Temperature
                    local['ows_temp'] = float(ows_sensor.find(self.xmlns + 'Temperature').text)
                    comp_val = float(dev.pluginProps.get('EDS0068TempComp', '0.0'))
                    local['input_value'] = local['ows_temp'] + comp_val
                    local['input_value'] = self.temp_convert(float(local['input_value']))
                    dev.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)

                dev.updateStateOnServer('sensorValue', value=local['input_value'], uiValue=local['input_value'])

            except Exception:  # noqa
                self.logger.exception()
                self.logger.debug(f"Unable to update device state on server. Device: {dev.name}")
                dev.updateStateOnServer('sensorValue', value="Unsupported", uiValue="Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            # This code ensures that the device's props are up-to-date and in line with what they
            # are on the server.
            new_props = dev.pluginProps
            new_props['address']                                       = dev.states['owsRomID']
            new_props['EDS0068barometricHgHighAlarmValue']             = ows_sensor.find(self.xmlns + 'BarometricPressureHgHighAlarmValue').text
            new_props['EDS0068barometricHgHighConditionalSearchState'] = ows_sensor.find(self.xmlns + 'BarometricPressureHgHighConditionalSearchState').text
            new_props['EDS0068barometricHgLowAlarmValue']              = ows_sensor.find(self.xmlns + 'BarometricPressureHgLowAlarmValue').text
            new_props['EDS0068barometricHgLowConditionalSearchState']  = ows_sensor.find(self.xmlns + 'BarometricPressureHgLowConditionalSearchState').text
            new_props['EDS0068barometricMbHighAlarmValue']             = ows_sensor.find(self.xmlns + 'BarometricPressureMbHighAlarmValue').text
            new_props['EDS0068barometricMbHighConditionalSearchState'] = ows_sensor.find(self.xmlns + 'BarometricPressureMbHighConditionalSearchState').text
            new_props['EDS0068barometricMbLowAlarmValue']              = ows_sensor.find(self.xmlns + 'BarometricPressureMbLowAlarmValue').text
            new_props['EDS0068barometricMbLowConditionalSearchState']  = ows_sensor.find(self.xmlns + 'BarometricPressureMbLowConditionalSearchState').text
            new_props['EDS0068dewpointHighAlarmValue']                 = ows_sensor.find(self.xmlns + 'DewPointHighAlarmValue').text
            new_props['EDS0068dewpointHighConditionalSearchState']     = ows_sensor.find(self.xmlns + 'DewPointHighConditionalSearchState').text
            new_props['EDS0068dewpointLowAlarmValue']                  = ows_sensor.find(self.xmlns + 'DewPointLowAlarmValue').text
            new_props['EDS0068dewpointLowConditionalSearchState']      = ows_sensor.find(self.xmlns + 'DewPointLowConditionalSearchState').text
            new_props['EDS0068heatIndexHighAlarmValue']                = ows_sensor.find(self.xmlns + 'HeatIndexHighAlarmValue').text
            new_props['EDS0068heatIndexHighConditionalSearchState']    = ows_sensor.find(self.xmlns + 'HeatIndexHighConditionalSearchState').text
            new_props['EDS0068heatIndexLowAlarmValue']                 = ows_sensor.find(self.xmlns + 'HeatIndexLowAlarmValue').text
            new_props['EDS0068heatIndexLowConditionalSearchState']     = ows_sensor.find(self.xmlns + 'HeatIndexLowConditionalSearchState').text
            new_props['EDS0068humidexHighAlarmValue']                  = ows_sensor.find(self.xmlns + 'HumidexHighAlarmValue').text
            new_props['EDS0068humidexHighConditionalSearchState']      = ows_sensor.find(self.xmlns + 'HumidexHighConditionalSearchState').text
            new_props['EDS0068humidexLowAlarmValue']                   = ows_sensor.find(self.xmlns + 'HumidexLowAlarmValue').text
            new_props['EDS0068humidexLowConditionalSearchState']       = ows_sensor.find(self.xmlns + 'HumidexLowConditionalSearchState').text
            new_props['EDS0068humidityHighAlarmValue']                 = ows_sensor.find(self.xmlns + 'HumidityHighAlarmValue').text
            new_props['EDS0068humidityHighConditionalSearchState']     = ows_sensor.find(self.xmlns + 'HumidityHighConditionalSearchState').text
            new_props['EDS0068humidityLowAlarmValue']                  = ows_sensor.find(self.xmlns + 'HumidityLowAlarmValue').text
            new_props['EDS0068humidityLowConditionalSearchState']      = ows_sensor.find(self.xmlns + 'HumidityLowConditionalSearchState').text
            new_props['EDS0068ledFunction']                            = ows_sensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0068lightHighAlarmValue']                    = ows_sensor.find(self.xmlns + 'LightHighAlarmValue').text
            new_props['EDS0068lightHighConditionalSearchState']        = ows_sensor.find(self.xmlns + 'LightHighConditionalSearchState').text
            new_props['EDS0068lightLowAlarmValue']                     = ows_sensor.find(self.xmlns + 'LightLowAlarmValue').text
            new_props['EDS0068lightLowConditionalSearchState']         = ows_sensor.find(self.xmlns + 'LightLowConditionalSearchState').text
            new_props['EDS0068relayFunction']                          = ows_sensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0068temperatureHighAlarmValue']              = ows_sensor.find(self.xmlns + 'TemperatureHighAlarmValue').text
            new_props['EDS0068temperatureHighConditionalSearchState']  = ows_sensor.find(self.xmlns + 'TemperatureHighConditionalSearchState').text
            new_props['EDS0068temperatureLowAlarmValue']               = ows_sensor.find(self.xmlns + 'TemperatureLowAlarmValue').text
            new_props['EDS0068temperatureLowConditionalSearchState']   = ows_sensor.find(self.xmlns + 'TemperatureLowConditionalSearchState').text
            dev.replacePluginPropsOnServer(new_props)

            self.number_of_sensors += 1

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.logger.debug("Success. Polling next sensor if appropriate.")
            return True

        except Exception:  # noqa
            self.logger.critical("Sensor update failure. Check connection.")
            self.logger.exception()
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0070(self, dev, ows_sensor, server_ip):  # noqa
        """
        Title Placeholder

        EDS0070 Description = "Vibration Sensor"

        :param indigo.Device dev:
        :param XML ows_sensor:
        :param str server_ip:
        """
        self.logger.debug("updateEDS0070() method called.")

        try:
            eds0070_state_dict = self.state_dict.eds0070_state_dict()
            input_value = None

            for key, value in eds0070_state_dict.items():
                try:
                    dev.updateStateOnServer(key, value=ows_sensor.find(self.xmlns + value).text)
                except Exception:  # noqa
                    self.logger.exception()
                    self.logger.debug(
                        f"Unable to update device state on server. Device: {dev.name}"
                    )
                    self.logger.debug(f"Key: {key} : Value: Unsupported")
                    dev.updateStateOnServer(key, value="Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0070'] == "C_1":  # Counter
                    input_value = ows_sensor.find(self.xmlns + 'Counter').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0070'] == "LED":  # LED State
                    input_value = ows_sensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0070'] == "Relay":  # Relay State
                    input_value = ows_sensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0070'] == "V":  # Vibration
                    input_value = ows_sensor.find(self.xmlns + 'VibrationInstant').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:  # noqa
                self.logger.exception()
                self.logger.debug(f"Unable to update device state on server. Device: {dev.name}")
                dev.updateStateOnServer('sensorValue', value="Unsupported", uiValue="Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']                        = dev.states['owsRomID']
            new_props['EDS0070LEDFunction']             = ows_sensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0070RelayFunction']           = ows_sensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0070VibrationHighAlarmValue'] = ows_sensor.find(self.xmlns + 'VibrationHighAlarmValue').text
            new_props['EDS0070VibrationLowAlarmValue']  = ows_sensor.find(self.xmlns + 'VibrationLowAlarmValue').text
            dev.replacePluginPropsOnServer(new_props)

            self.number_of_sensors += 1

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.logger.debug("Success. Polling next sensor if appropriate.")
            return True

        except Exception:  # noqa
            self.logger.critical("Sensor update failure. Check connection.")
            self.logger.exception()
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0071(self, dev, ows_sensor, server_ip):  # noqa
        """
        Title Placeholder

        EDS0071 Description = "RTD Interface, 4 Wire"

        :param indigo.Device dev:
        :param XML ows_sensor:
        :param str server_ip:
        """
        self.logger.debug("updateEDS0071() method called.")

        try:
            eds0071_state_dict = self.state_dict.eds0071_state_dict()
            input_value = None

            for key, value in eds0071_state_dict.items():
                try:
                    dev.updateStateOnServer(key, value=ows_sensor.find(self.xmlns + value).text)
                except Exception:  # noqa
                    self.logger.exception()
                    self.logger.debug(
                        f"Unable to update device state on server. Device: {dev.name}"
                    )
                    self.logger.debug(f"Key: {key} : Value: Unsupported")
                    dev.updateStateOnServer(key, value="Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0071'] == "C_1":  # Counter
                    input_value = ows_sensor.find(self.xmlns + 'Counter').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0071'] == "LED":  # LED State
                    input_value = ows_sensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0071'] == "Relay":  # Relay State
                    input_value = ows_sensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0071'] == "RTD":  # RTD
                    conversion_value = ows_sensor.find(self.xmlns + 'RTDOhms').text
                    input_value = self.volts_convert(conversion_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0071'] == "T":  # Temperature
                    input_value = ows_sensor.find(self.xmlns + 'Temperature').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:  # noqa
                self.logger.exception()
                self.logger.debug(f"Unable to update device state on server. Device: {dev.name}")
                dev.updateStateOnServer('sensorValue', value="Unsupported", uiValue="Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']                            = dev.states['owsRomID']
            new_props['EDS0071CalibrationKey']              = ows_sensor.find(self.xmlns + 'CalibrationKey').text
            new_props['EDS0071LEDFunction']                 = ows_sensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0071RelayFunction']               = ows_sensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0071RTDReadDelay']                = ows_sensor.find(self.xmlns + 'RTDReadDelay').text
            new_props['EDS0071RTDResistanceHighAlarmValue'] = ows_sensor.find(self.xmlns + 'RTDResistanceHighAlarmValue').text
            new_props['EDS0071RTDResistanceLowAlarmValue']  = ows_sensor.find(self.xmlns + 'RTDResistanceLowAlarmValue').text
            new_props['EDS0071TemperatureHighAlarmValue']   = ows_sensor.find(self.xmlns + 'TemperatureHighAlarmValue').text
            new_props['EDS0071TemperatureLowAlarmValue']    = ows_sensor.find(self.xmlns + 'TemperatureLowAlarmValue').text
            dev.replacePluginPropsOnServer(new_props)

            self.number_of_sensors += 1

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.logger.debug("Success. Polling next sensor if appropriate.")
            return True

        except Exception:  # noqa
            self.logger.critical("Sensor update failure. Check connection.")
            self.logger.exception()
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0080(self, dev, ows_sensor, server_ip):  # noqa
        """
        Title Placeholder

        EDS0080 Description = "Octal 4-20 Milliamp Input"

        :param indigo.Device dev:
        :param XML ows_sensor:
        :param str server_ip:
        """
        self.logger.debug("updateEDS0080() method called.")

        try:
            eds0080_state_dict = self.state_dict.eds0080_state_dict()
            input_value = None

            for key, value in eds0080_state_dict.items():
                try:
                    dev.updateStateOnServer(key, value=ows_sensor.find(self.xmlns + value).text)
                except Exception:  # noqa
                    self.logger.exception()
                    self.logger.debug(
                        f"Unable to update device state on server. Device: {dev.name}"
                    )
                    self.logger.debug(f"Key: {key} : Value: Unsupported")
                    dev.updateStateOnServer(key, value="Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0080'] == "I_1":  # Input 1
                    conversion_value = ows_sensor.find(self.xmlns + 'v4to20mAInput1Instant').text
                    input_value = self.volts_convert(conversion_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0080'] == "I_2":  # Input 2
                    conversion_value = ows_sensor.find(self.xmlns + 'v4to20mAInput2Instant').text
                    input_value = self.volts_convert(conversion_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0080'] == "I_3":  # Input 3
                    conversion_value = ows_sensor.find(self.xmlns + 'v4to20mAInput3Instant').text
                    input_value = self.volts_convert(conversion_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0080'] == "I_4":  # Input 4
                    conversion_value = ows_sensor.find(self.xmlns + 'v4to20mAInput4Instant').text
                    input_value = self.volts_convert(conversion_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0080'] == "I_5":  # Input 5
                    conversion_value = ows_sensor.find(self.xmlns + 'v4to20mAInput5Instant').text
                    input_value = self.volts_convert(conversion_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0080'] == "I_6":  # Input 6
                    conversion_value = ows_sensor.find(self.xmlns + 'v4to20mAInput6Instant').text
                    input_value = self.volts_convert(conversion_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0080'] == "I_7":  # Input 7
                    conversion_value = ows_sensor.find(self.xmlns + 'v4to20mAInput7Instant').text
                    input_value = self.volts_convert(conversion_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0080'] == "I_8":  # Input 8
                    conversion_value = ows_sensor.find(self.xmlns + 'v4to20mAInput8Instant').text
                    input_value = self.volts_convert(conversion_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0080'] == "LED":  # LED State
                    input_value = ows_sensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0080'] == "Relay":  # Relay State
                    input_value = ows_sensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0080'] == "C_1":  # Counter 1
                    conversion_value = ows_sensor.find(self.xmlns + 'Counter').text

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:  # noqa
                self.logger.exception()
                self.logger.debug(f"Unable to update device state on server. Device: {dev.name}")
                dev.updateStateOnServer('sensorValue', value="Unsupported", uiValue="Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']                              = dev.states['owsRomID']
            new_props['EDS0080LEDFunction']                  = ows_sensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0080RelayFunction']                = ows_sensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0080v4to20mAInput1HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v4to20mAInput1HighAlarmValue').text
            new_props['EDS0080v4to20mAInput1LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v4to20mAInput1LowAlarmValue').text
            new_props['EDS0080v4to20mAInput2HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v4to20mAInput2HighAlarmValue').text
            new_props['EDS0080v4to20mAInput2LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v4to20mAInput2LowAlarmValue').text
            new_props['EDS0080v4to20mAInput3HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v4to20mAInput3HighAlarmValue').text
            new_props['EDS0080v4to20mAInput3LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v4to20mAInput3LowAlarmValue').text
            new_props['EDS0080v4to20mAInput4HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v4to20mAInput4HighAlarmValue').text
            new_props['EDS0080v4to20mAInput4LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v4to20mAInput4LowAlarmValue').text
            new_props['EDS0080v4to20mAInput5HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v4to20mAInput5HighAlarmValue').text
            new_props['EDS0080v4to20mAInput5LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v4to20mAInput5LowAlarmValue').text
            new_props['EDS0080v4to20mAInput6HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v4to20mAInput6HighAlarmValue').text
            new_props['EDS0080v4to20mAInput6LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v4to20mAInput6LowAlarmValue').text
            new_props['EDS0080v4to20mAInput7HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v4to20mAInput7HighAlarmValue').text
            new_props['EDS0080v4to20mAInput7LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v4to20mAInput7LowAlarmValue').text
            new_props['EDS0080v4to20mAInput8HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v4to20mAInput8HighAlarmValue').text
            new_props['EDS0080v4to20mAInput8LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v4to20mAInput8LowAlarmValue').text
            dev.replacePluginPropsOnServer(new_props)

            self.number_of_sensors += 1

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.logger.debug("Success. Polling next sensor if appropriate.")
            return True

        except Exception:  # noqa
            self.logger.critical("Sensor update failure. Check connection.")
            self.logger.exception()
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0082(self, dev, ows_sensor, server_ip):  # noqa
        """
        Title Placeholder

        EDS0082 Description = "Octal Current Input Device"

        :param indigo.Device dev:
        :param XML ows_sensor:
        :param str server_ip:
        """
        self.logger.debug("updateEDS0082() method called.")

        try:
            eds0082_state_dict = self.state_dict.eds0082_state_dict()
            input_value = None

            for key, value in eds0082_state_dict.items():
                try:
                    dev.updateStateOnServer(key, value=ows_sensor.find(self.xmlns + value).text)
                except Exception:  # noqa
                    self.logger.exception()
                    self.logger.debug(
                        f"Unable to update device state on server. Device: {dev.name}"
                    )
                    self.logger.debug(f"Key: {key} : Value: Unsupported")
                    dev.updateStateOnServer(key, value="Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0082'] == "I_1":  # Input 1 Instant
                    input_value = ows_sensor.find(self.xmlns + 'v0to10VoltInput1Instant').text
                    input_value = self.volts_convert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0082'] == "I_2":  # Input 2 Instant
                    input_value = ows_sensor.find(self.xmlns + 'v0to10VoltInput2Instant').text
                    input_value = self.volts_convert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0082'] == "I_3":  # Input 3 Instant
                    input_value = ows_sensor.find(self.xmlns + 'v0to10VoltInput3Instant').text
                    input_value = self.volts_convert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0082'] == "I_4":  # Input 4 Instant
                    input_value = ows_sensor.find(self.xmlns + 'v0to10VoltInput4Instant').text
                    input_value = self.volts_convert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0082'] == "I_5":  # Input 5 Instant
                    input_value = ows_sensor.find(self.xmlns + 'v0to10VoltInput5Instant').text
                    input_value = self.volts_convert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0082'] == "I_6":  # Input 6 Instant
                    input_value = ows_sensor.find(self.xmlns + 'v0to10VoltInput6Instant').text
                    input_value = self.volts_convert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0082'] == "I_7":  # Input 7 Instant
                    input_value = ows_sensor.find(self.xmlns + 'v0to10VoltInput7Instant').text
                    input_value = self.volts_convert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0082'] == "I_8":  # Input 8 Instant
                    input_value = ows_sensor.find(self.xmlns + 'v0to10VoltInput8Instant').text
                    input_value = self.volts_convert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0082'] == "LED":  # LED State
                    input_value = ows_sensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0082'] == "Relay":  # Relay State
                    input_value = ows_sensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:  # noqa
                self.logger.exception()
                self.logger.debug(f"Unable to update device state on server. Device: {dev.name}")
                dev.updateStateOnServer('sensorValue', value="Unsupported", uiValue="Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']                               = dev.states['owsRomID']
            new_props['EDS0082LEDFunction']                    = ows_sensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0082RelayFunction']                  = ows_sensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0082v0to10VoltInput1HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v0to10VoltInput1HighAlarmValue').text
            new_props['EDS0082v0to10VoltInput1LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v0to10VoltInput1LowAlarmValue').text
            new_props['EDS0082v0to10VoltInput2HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v0to10VoltInput2HighAlarmValue').text
            new_props['EDS0082v0to10VoltInput2LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v0to10VoltInput2LowAlarmValue').text
            new_props['EDS0082v0to10VoltInput3HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v0to10VoltInput3HighAlarmValue').text
            new_props['EDS0082v0to10VoltInput3LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v0to10VoltInput3LowAlarmValue').text
            new_props['EDS0082v0to10VoltInput4HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v0to10VoltInput4HighAlarmValue').text
            new_props['EDS0082v0to10VoltInput4LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v0to10VoltInput4LowAlarmValue').text
            new_props['EDS0082v0to10VoltInput5HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v0to10VoltInput5HighAlarmValue').text
            new_props['EDS0082v0to10VoltInput5LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v0to10VoltInput5LowAlarmValue').text
            new_props['EDS0082v0to10VoltInput6HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v0to10VoltInput6HighAlarmValue').text
            new_props['EDS0082v0to10VoltInput6LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v0to10VoltInput6LowAlarmValue').text
            new_props['EDS0082v0to10VoltInput7HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v0to10VoltInput7HighAlarmValue').text
            new_props['EDS0082v0to10VoltInput7LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v0to10VoltInput7LowAlarmValue').text
            new_props['EDS0082v0to10VoltInput8HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v0to10VoltInput8HighAlarmValue').text
            new_props['EDS0082v0to10VoltInput8LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v0to10VoltInput8LowAlarmValue').text
            dev.replacePluginPropsOnServer(new_props)

            self.number_of_sensors += 1

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.logger.debug("Success. Polling next sensor if appropriate.")
            return True

        except Exception:  # noqa
            self.logger.critical("Sensor update failure. Check connection.")
            self.logger.exception()
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0083(self, dev, ows_sensor, server_ip):  # noqa
        """
        Title Placeholder

        EDS0083 Description = "Octal Current Input Device"

        :param indigo.Device dev:
        :param XML ows_sensor:
        :param str server_ip:
        """
        self.logger.debug("updateEDS0083() method called.")

        try:
            eds0083_state_dict = self.state_dict.eds0083_state_dict()
            input_value = None

            for key, value in eds0083_state_dict.items():
                try:
                    dev.updateStateOnServer(key, value=ows_sensor.find(self.xmlns + value).text)
                except Exception:  # noqa
                    self.logger.exception()
                    self.logger.debug(
                        f"Unable to update device state on server. Device: {dev.name}"
                    )
                    self.logger.debug(f"Key: {key} : Value: Unsupported")
                    dev.updateStateOnServer(key, value="Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0083'] == "I_1":  # Input 1 Instant
                    input_value = ows_sensor.find(self.xmlns + 'v4to20mAInput1Instant').text
                    input_value = self.volts_convert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0083'] == "I_2":  # Input 2 Instant
                    input_value = ows_sensor.find(self.xmlns + 'v4to20mAInput2Instant').text
                    input_value = self.volts_convert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0083'] == "I_3":  # Input 3 Instant
                    input_value = ows_sensor.find(self.xmlns + 'v4to20mAInput3Instant').text
                    input_value = self.volts_convert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0083'] == "I_4":  # Input 4 Instant
                    input_value = ows_sensor.find(self.xmlns + 'v4to20mAInput4Instant').text
                    input_value = self.volts_convert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0083'] == "LED":  # LED State
                    input_value = ows_sensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0083'] == "Relay":  # Relay State
                    input_value = ows_sensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:  # noqa
                self.logger.exception()
                self.logger.debug(f"Unable to update device state on server. Device: {dev.name}")
                dev.updateStateOnServer('sensorValue', value="Unsupported", uiValue="Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']                             = dev.states['owsRomID']
            new_props['EDS0083LEDFunction']                  = ows_sensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0083RelayFunction']                = ows_sensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0083v4to20mAInput1HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v4to20mAInput1HighAlarmValue').text
            new_props['EDS0083v4to20mAInput1LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v4to20mAInput1LowAlarmValue').text
            new_props['EDS0083v4to20mAInput2HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v4to20mAInput2HighAlarmValue').text
            new_props['EDS0083v4to20mAInput2LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v4to20mAInput2LowAlarmValue').text
            new_props['EDS0083v4to20mAInput3HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v4to20mAInput3HighAlarmValue').text
            new_props['EDS0083v4to20mAInput3LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v4to20mAInput3LowAlarmValue').text
            new_props['EDS0083v4to20mAInput4HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v4to20mAInput4HighAlarmValue').text
            new_props['EDS0083v4to20mAInput4LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v4to20mAInput4LowAlarmValue').text
            dev.replacePluginPropsOnServer(new_props)

            self.number_of_sensors += 1

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.logger.debug("Success. Polling next sensor if appropriate.")
            return True

        except Exception:  # noqa
            self.logger.critical("Sensor update failure. Check connection.")
            self.logger.exception()
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0085(self, dev, ows_sensor, server_ip):  # noqa
        """
        Title Placeholder

        EDS0085 Description = "Octal Current Input Device"

        :param indigo.Device dev:
        :param XML ows_sensor:
        :param str server_ip:
        """
        self.logger.debug("updateEDS0085() method called.")

        try:
            eds0085_state_dict = self.state_dict.eds0085_state_dict()
            input_value = None

            for key, value in eds0085_state_dict.items():
                try:
                    dev.updateStateOnServer(key, value=ows_sensor.find(self.xmlns + value).text)
                except Exception:  # noqa
                    self.logger.exception()
                    self.logger.debug(
                        f"Unable to update device state on server. Device: {dev.name}"
                    )
                    self.logger.debug(f"Key: {key} : Value: Unsupported")
                    dev.updateStateOnServer(key, value="Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0085'] == "I_1":  # Input 1 Instant
                    input_value = ows_sensor.find(self.xmlns + 'v0to10VoltInput1Instant').text
                    input_value = self.volts_convert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0085'] == "I_2":  # Input 2 Instant
                    input_value = ows_sensor.find(self.xmlns + 'v0to10VoltInput2Instant').text
                    input_value = self.volts_convert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0085'] == "I_3":  # Input 3 Instant
                    input_value = ows_sensor.find(self.xmlns + 'v0to10VoltInput3Instant').text
                    input_value = self.volts_convert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0085'] == "I_4":  # Input 4 Instant
                    input_value = ows_sensor.find(self.xmlns + 'v0to10VoltInput4Instant').text
                    input_value = self.volts_convert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0085'] == "LED":  # LED State
                    input_value = ows_sensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0085'] == "Relay":  # Relay State
                    input_value = ows_sensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:  # noqa
                self.logger.exception()
                self.logger.debug(f"Unable to update device state on server. Device: {dev.name}")
                dev.updateStateOnServer('sensorValue', value="Unsupported", uiValue="Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']                               = dev.states['owsRomID']
            new_props['EDS0085LEDFunction']                    = ows_sensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0085RelayFunction']                  = ows_sensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0085v0to10VoltInput1HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v0to10VoltInput1HighAlarmValue').text
            new_props['EDS0085v0to10VoltInput1LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v0to10VoltInput1LowAlarmValue').text
            new_props['EDS0085v0to10VoltInput2HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v0to10VoltInput2HighAlarmValue').text
            new_props['EDS0085v0to10VoltInput2LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v0to10VoltInput2LowAlarmValue').text
            new_props['EDS0085v0to10VoltInput3HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v0to10VoltInput3HighAlarmValue').text
            new_props['EDS0085v0to10VoltInput3LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v0to10VoltInput3LowAlarmValue').text
            new_props['EDS0085v0to10VoltInput4HighAlarmValue'] = ows_sensor.find(self.xmlns + 'v0to10VoltInput4HighAlarmValue').text
            new_props['EDS0085v0to10VoltInput4LowAlarmValue']  = ows_sensor.find(self.xmlns + 'v0to10VoltInput4LowAlarmValue').text
            dev.replacePluginPropsOnServer(new_props)

            self.number_of_sensors += 1

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.logger.debug("Success. Polling next sensor if appropriate.")
            return True

        except Exception:  # noqa
            self.logger.critical("Sensor update failure. Check connection.")
            self.logger.exception()
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0090(self, dev, ows_sensor, server_ip):  # noqa
        """
        Title Placeholder

        EDS0090 Description = "Octal Discrete IO"

        :param indigo.Device dev:
        :param XML ows_sensor:
        :param str server_ip:
        """
        self.logger.debug("updateEDS0090() method called.")

        try:
            eds0090_state_dict = self.state_dict.eds0090_state_dict()
            input_value = None

            for key, value in eds0090_state_dict.items():
                try:
                    dev.updateStateOnServer(key, value=ows_sensor.find(self.xmlns + value).text)
                except Exception:  # noqa
                    self.logger.exception()
                    self.logger.debug(
                        f"Unable to update device state on server. Device: {dev.name}"
                    )
                    self.logger.debug(f"Key: {key} : Value: Unsupported")
                    dev.updateStateOnServer(key, value="Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0090'] == "C_1":  # Counter 1
                    input_value = ows_sensor.find(self.xmlns + 'Counter').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0090'] == "I_1":  # Input 1 State
                    input_value = ows_sensor.find(self.xmlns + 'DiscreteIO1InputState').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0090'] == "I_2":  # Input 2 State
                    input_value = ows_sensor.find(self.xmlns + 'DiscreteIO2InputState').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0090'] == "I_3":  # Input 3 State
                    input_value = ows_sensor.find(self.xmlns + 'DiscreteIO3InputState').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0090'] == "I_4":  # Input 4 State
                    input_value = ows_sensor.find(self.xmlns + 'DiscreteIO4InputState').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0090'] == "I_5":  # Input 5 State
                    input_value = ows_sensor.find(self.xmlns + 'DiscreteIO5InputState').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0090'] == "I_6":  # Input 6 State
                    input_value = ows_sensor.find(self.xmlns + 'DiscreteIO6InputState').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0090'] == "I_7":  # Input 7 State
                    input_value = ows_sensor.find(self.xmlns + 'DiscreteIO7InputState').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0090'] == "I_8":  # Input 8 State
                    input_value = ows_sensor.find(self.xmlns + 'DiscreteIO8InputState').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0090'] == "LED":  # LED State
                    input_value = ows_sensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0090'] == "Relay":  # Relay State
                    input_value = ows_sensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:  # noqa
                self.logger.exception()
                self.logger.debug(f"Unable to update device state on server. Device: {dev.name}")
                dev.updateStateOnServer('sensorValue', value="Unsupported", uiValue="Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address'] = dev.states['owsRomID']
            new_props['EDS0090DiscreteIO1ActivityLatchReset'] = ows_sensor.find(self.xmlns + 'DiscreteIO1ActivityLatchReset').text
            new_props['EDS0090DiscreteIO1HighAlarmValue']     = ows_sensor.find(self.xmlns + 'DiscreteIO1HighAlarmValue').text
            new_props['EDS0090DiscreteIO1LowAlarmValue']      = ows_sensor.find(self.xmlns + 'DiscreteIO1LowAlarmValue').text
            new_props['EDS0090DiscreteIO1OutputState']        = ows_sensor.find(self.xmlns + 'DiscreteIO1OutputState').text
            new_props['EDS0090DiscreteIO1PulldownState']      = ows_sensor.find(self.xmlns + 'DiscreteIO1PulldownState').text
            new_props['EDS0090DiscreteIO1PulseCounterReset']  = ows_sensor.find(self.xmlns + 'DiscreteIO1PulseCounterReset').text
            new_props['EDS0090DiscreteIO2ActivityLatchReset'] = ows_sensor.find(self.xmlns + 'DiscreteIO2ActivityLatchReset').text
            new_props['EDS0090DiscreteIO2HighAlarmValue']     = ows_sensor.find(self.xmlns + 'DiscreteIO2HighAlarmValue').text
            new_props['EDS0090DiscreteIO2LowAlarmValue']      = ows_sensor.find(self.xmlns + 'DiscreteIO2LowAlarmValue').text
            new_props['EDS0090DiscreteIO2OutputState']        = ows_sensor.find(self.xmlns + 'DiscreteIO2OutputState').text
            new_props['EDS0090DiscreteIO2PulldownState']      = ows_sensor.find(self.xmlns + 'DiscreteIO2PulldownState').text
            new_props['EDS0090DiscreteIO2PulseCounterReset']  = ows_sensor.find(self.xmlns + 'DiscreteIO2PulseCounterReset').text
            new_props['EDS0090DiscreteIO3ActivityLatchReset'] = ows_sensor.find(self.xmlns + 'DiscreteIO3ActivityLatchReset').text
            new_props['EDS0090DiscreteIO3HighAlarmValue']     = ows_sensor.find(self.xmlns + 'DiscreteIO3HighAlarmValue').text
            new_props['EDS0090DiscreteIO3LowAlarmValue']      = ows_sensor.find(self.xmlns + 'DiscreteIO3LowAlarmValue').text
            new_props['EDS0090DiscreteIO3OutputState']        = ows_sensor.find(self.xmlns + 'DiscreteIO3OutputState').text
            new_props['EDS0090DiscreteIO3PulldownState']      = ows_sensor.find(self.xmlns + 'DiscreteIO3PulldownState').text
            new_props['EDS0090DiscreteIO4ActivityLatchReset'] = ows_sensor.find(self.xmlns + 'DiscreteIO4ActivityLatchReset').text
            new_props['EDS0090DiscreteIO4HighAlarmValue']     = ows_sensor.find(self.xmlns + 'DiscreteIO4HighAlarmValue').text
            new_props['EDS0090DiscreteIO4LowAlarmValue']      = ows_sensor.find(self.xmlns + 'DiscreteIO4LowAlarmValue').text
            new_props['EDS0090DiscreteIO4OutputState']        = ows_sensor.find(self.xmlns + 'DiscreteIO4OutputState').text
            new_props['EDS0090DiscreteIO4PulldownState']      = ows_sensor.find(self.xmlns + 'DiscreteIO4PulldownState').text
            new_props['EDS0090DiscreteIO5ActivityLatchReset'] = ows_sensor.find(self.xmlns + 'DiscreteIO5ActivityLatchReset').text
            new_props['EDS0090DiscreteIO5HighAlarmValue']     = ows_sensor.find(self.xmlns + 'DiscreteIO5HighAlarmValue').text
            new_props['EDS0090DiscreteIO5LowAlarmValue']      = ows_sensor.find(self.xmlns + 'DiscreteIO5LowAlarmValue').text
            new_props['EDS0090DiscreteIO5OutputState']        = ows_sensor.find(self.xmlns + 'DiscreteIO5OutputState').text
            new_props['EDS0090DiscreteIO5PulldownState']      = ows_sensor.find(self.xmlns + 'DiscreteIO5PulldownState').text
            new_props['EDS0090DiscreteIO6ActivityLatchReset'] = ows_sensor.find(self.xmlns + 'DiscreteIO6ActivityLatchReset').text
            new_props['EDS0090DiscreteIO6HighAlarmValue']     = ows_sensor.find(self.xmlns + 'DiscreteIO6HighAlarmValue').text
            new_props['EDS0090DiscreteIO6LowAlarmValue']      = ows_sensor.find(self.xmlns + 'DiscreteIO6LowAlarmValue').text
            new_props['EDS0090DiscreteIO6OutputState']        = ows_sensor.find(self.xmlns + 'DiscreteIO6OutputState').text
            new_props['EDS0090DiscreteIO6PulldownState']      = ows_sensor.find(self.xmlns + 'DiscreteIO6PulldownState').text
            new_props['EDS0090DiscreteIO7ActivityLatchReset'] = ows_sensor.find(self.xmlns + 'DiscreteIO7ActivityLatchReset').text
            new_props['EDS0090DiscreteIO7HighAlarmValue']     = ows_sensor.find(self.xmlns + 'DiscreteIO7HighAlarmValue').text
            new_props['EDS0090DiscreteIO7LowAlarmValue']      = ows_sensor.find(self.xmlns + 'DiscreteIO7LowAlarmValue').text
            new_props['EDS0090DiscreteIO7OutputState']        = ows_sensor.find(self.xmlns + 'DiscreteIO7OutputState').text
            new_props['EDS0090DiscreteIO7PulldownState']      = ows_sensor.find(self.xmlns + 'DiscreteIO7PulldownState').text
            new_props['EDS0090DiscreteIO8ActivityLatchReset'] = ows_sensor.find(self.xmlns + 'DiscreteIO8ActivityLatchReset').text
            new_props['EDS0090DiscreteIO8HighAlarmValue']     = ows_sensor.find(self.xmlns + 'DiscreteIO8HighAlarmValue').text
            new_props['EDS0090DiscreteIO8LowAlarmValue']      = ows_sensor.find(self.xmlns + 'DiscreteIO8LowAlarmValue').text
            new_props['EDS0090DiscreteIO8OutputState']        = ows_sensor.find(self.xmlns + 'DiscreteIO8OutputState').text
            new_props['EDS0090DiscreteIO8PulldownState']      = ows_sensor.find(self.xmlns + 'DiscreteIO8PulldownState').text
            new_props['EDS0090LEDFunction']                   = ows_sensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0090RelayFunction']                 = ows_sensor.find(self.xmlns + 'RelayFunction').text
            dev.replacePluginPropsOnServer(new_props)

            self.number_of_sensors += 1

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.logger.debug("Success. Polling next sensor if appropriate.")
            return True

        except Exception:  # noqa
            self.logger.critical("Sensor update failure. Check connection.")
            self.logger.exception()
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    # =============================================================================
    # =========== Server and Sensor Device Config Dialog Button Methods ===========
    # =============================================================================
    # While we are always sending a "0" as the setting value, this may not always
    # be the case. So we keep them separate for this reason.
    def clearAlarms(self, values_dict, type_id, target_id, fltr="indigo.sensor"):  # noqa
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """

        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "clearAlarms",
            "0"
        )
        self.sendToServer(parm_list)

    # TODO: All these callbacks can be combined down to one for each type using the
    #       filter payload value. See Matplotlib Stock Bar as an example.
    # =============================================================================
    def clear_barometric_pressure_hg_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):  # noqa
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "BarometricPressureHgHighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_barometric_pressure_hg_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "BarometricPressureHgLowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_barometric_pressure_mb_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "BarometricPressureMbHighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_barometric_pressure_mb_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "BarometricPressureMbLowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_dewpoint_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "DewpointHighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_dewpoint_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "DewpointLowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_discrete_io1_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "DiscreteIO1HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_discrete_io1_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "DiscreteIO1LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_discrete_io2_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "DiscreteIO2HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_discrete_io2_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "DiscreteIO2LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_discrete_io3_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "DiscreteIO3HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_discrete_io3_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "DiscreteIO3LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_discrete_io4_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "DiscreteIO4HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_discrete_io4_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "DiscreteIO4LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_discrete_io5_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "DiscreteIO5HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_discrete_io5_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "DiscreteIO5LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_discrete_io6_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "DiscreteIO6HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_discrete_io6_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "DiscreteIO6LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_discrete_io7_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "DiscreteIO7HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_discrete_io7_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "DiscreteIO7LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_discrete_io8_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "DiscreteIO8HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_discrete_io8_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "DiscreteIO8LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_heat_index_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "HeatIndexHighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_heat_index_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "HeatIndexLowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_humidex_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "HumidexHighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_humidex_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "HumidexLowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_humidity_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "HumidityHighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_humidity_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "HumidityLowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0_input1_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v0to10VoltInput1HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0_input1_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v0to10VoltInput1LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0_input2_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v0to10VoltInput2HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0_input2_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v0to10VoltInput2LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0_input3_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v0to10VoltInput3HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0_input3_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v0to10VoltInput3LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0_input4_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v0to10VoltInput4HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0_input4_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v0to10VoltInput4LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0_input5_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v0to10VoltInput5HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0_input5_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v0to10VoltInput5LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0_input6_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v0to10VoltInput6HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0_input6_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v0to10VoltInput6LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0_input7_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v0to10VoltInput7HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0_input7_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v0to10VoltInput7LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0_input8_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v0to10VoltInput8HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0_input8_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v0to10VoltInput8LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4_input1_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v4to20mAInput1HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4_input1_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v4to20mAInput1LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4_input2_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v4to20mAInput2HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4_input2_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v4to20mAInput2LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4_input3_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v4to20mAInput3HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4_input3_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v4to20mAInput3LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4_input4_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v4to20mAInput4HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4_input4_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v4to20mAInput4LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4_input5_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v4to20mAInput5HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4_input5_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v4to20mAInput5LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4_input6_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v4to20mAInput6HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4_input6_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v4to20mAInput6LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4_input7_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v4to20mAInput7HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4_input7_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v4to20mAInput7LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4_input8_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v4to20mAInput8HighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4_input8_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "v4to20mAInput8LowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_light_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "LightHighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_light_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "LightLowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_rtd_resistance_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "RTDResistanceHighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_rtd_resistance_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "RTDResistanceLowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_rtd_fault_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "RTDFaultConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_temperature_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "TemperatureHighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_temperature_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "TemperatureLowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_vibration_high_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "VibrationHighConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_vibration_low_conditional_search_state(
            self, values_dict, type_id, target_id, fltr="indigo.sensor"  # noqa
    ):
        """
        Title Placeholder

        Docstring Placeholder

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        parm_list = (
            values_dict['serverList'],
            values_dict['romID'],
            "VibrationLowConditionalSearchState",
            "0"
        )
        self.sendToServer(parm_list)

    # =============================================================================
    def toggle_led(self, values_dict, type_id, target_id, fltr="indigo.sensor"):  # noqa
        """
        Title Placeholder

        The toggle_led() method is used to toggle the LED of the calling device.

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        new_var = ""
        try:
            if indigo.devices[target_id].states['owsLED'] == "1":
                new_var = "0"
            elif indigo.devices[target_id].states['owsLED'] == "0":
                new_var = "1"
            else:
                self.logger.critical("Error toggling sensor LED.")
        except Exception:  # noqa
            self.logger.exception()

        parm_list = (values_dict['serverList'], values_dict['romID'], "LEDState", new_var)
        self.sendToServer(parm_list)

    # =============================================================================
    def toggle_relay(self, values_dict, type_id, target_id, fltr="indigo.sensor"):  # noqa
        """
        Title Placeholder

        The toggle_relay() method is used to toggle the relay of the calling device.

        :param indigo.Dict values_dict:
        :param str type_id:
        :param int target_id:
        :param str fltr:
        :return:
        """
        new_var = ""
        try:
            if indigo.devices[target_id].states['owsRelay'] == "1":
                new_var = "0"
            elif indigo.devices[target_id].states['owsRelay'] == "0":
                new_var = "1"
            else:
                self.logger.critical("Error toggling sensor relay.")
        except Exception:  # noqa
            self.logger.exception()

        parm_list = (values_dict['serverList'], values_dict['romID'], "RelayState", new_var)
        self.sendToServer(parm_list)

    # =============================================================================
    def updateDeviceStatesAction(self, values_dict):  # noqa
        """
        Invoke the updateDeviceStates() method when it is called for from an Action item.

        :param indigo.Dict values_dict:
        :return:
        """
        self.updateDeviceStates()

    # =============================================================================
    def updateDeviceStatesMenu(self):  # noqa
        """
        Invoke the updateDeviceStates() method when it is called for from a Menu item.

        :return:
        """
        self.updateDeviceStates()
        indigo.server.log("Sensors updated.")

    # =============================================================================
    def updateDeviceStates(self):  # noqa
        """
        Initiate an update for each established Indigo device.

        :return:
        """
        self.logger.debug("updateDeviceStates() method called.")

        addr = self.pluginPrefs['OWServerIP']
        split_ip = addr.replace(" ", "").split(",")
        self.number_of_sensors = 0
        self.number_of_servers = 0
        pref_poll = int(self.pluginPrefs.get('configMenuPollInterval', 900))

        if not self.pluginPrefs.get('suppressResultsLogging', False):
            self.logger.info("Getting OWServer data...")

        for server_ip in split_ip:

            try:
                # Grab details.xml
                self.logger.debug(f"Getting details.xml for server {server_ip}")
                ows_xml = self.get_details_xml(server_ip)

                if not ows_xml:
                    raise Exception

                root = eTree.fromstring(ows_xml)

                for dev in indigo.devices.itervalues("self"):
                    if not dev:
                        # There are no devices of type OWServer, so go to sleep.
                        self.logger.debug(
                            "There aren't any servers or sensors to assign yet. Sleeping."
                        )
                        self.sleep(pref_poll)

                    elif not dev.configured:
                        # A device has been created, but hasn't been fully configured.
                        self.logger.warning(
                            "A device has been created, but is not fully  configured. Sleeping "
                            "while you finish."
                        )
                        self.sleep(pref_poll)

                    elif not dev.enabled:
                        # A device has been disabled. Skip it.
                        self.logger.debug(f"{dev.name} is disabled. Skipping.")

                    elif dev.enabled:
                        self.logger.debug(f"Parsing information for device: {dev.name}")

                        try:
                            if (dev.deviceTypeId == "owsOWSServer"
                                    and dev.pluginProps['serverList'] == server_ip):
                                self.updateOWServer(dev, root, server_ip)

                            elif dev.deviceTypeId == 'owsTemperatureSensor':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_DS18B20'):
                                    self.logger.debug("Parsing DS18B20 devices.")
                                    rom_id = owsSensor.find(self.xmlns + 'ROMId').text
                                    if dev.pluginProps['romID'] == rom_id \
                                            and dev.pluginProps['serverList'] == server_ip:
                                        self.updateDS18B20(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsTemperatureSensor_S':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_DS18S20'):
                                    self.logger.debug("Parsing DS18S20 devices.")
                                    rom_id = owsSensor.find(self.xmlns + 'ROMId').text
                                    if dev.pluginProps['romID'] == rom_id \
                                            and dev.pluginProps['serverList'] == server_ip:
                                        self.updateDS18S20(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsDualSwitchPlusMemory':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_DS2406'):
                                    self.logger.debug("Parsing DS2406 devices.")
                                    rom_id = owsSensor.find(self.xmlns + 'ROMId').text
                                    if dev.pluginProps['romID'] == rom_id \
                                            and dev.pluginProps['serverList'] == server_ip:
                                        self.updateDS2406(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsUserSwitch':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_DS2408'):
                                    self.logger.debug("Parsing DS2408 devices.")
                                    rom_id = owsSensor.find(self.xmlns + 'ROMId').text
                                    if dev.pluginProps['romID'] == rom_id \
                                            and dev.pluginProps['serverList'] == server_ip:
                                        self.updateDS2408(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsCounterDevice':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_DS2423'):
                                    self.logger.debug("Parsing DS2423 devices.")
                                    rom_id = owsSensor.find(self.xmlns + 'ROMId').text
                                    if dev.pluginProps['romID'] == rom_id \
                                            and dev.pluginProps['serverList'] == server_ip:
                                        self.updateDS2423(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsSmartBatteryMonitor':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_DS2438'):
                                    self.logger.debug("Parsing DS2438 devices.")
                                    rom_id = owsSensor.find(self.xmlns + 'ROMId').text
                                    if dev.pluginProps['romID'] == rom_id \
                                            and dev.pluginProps['serverList'] == server_ip:
                                        self.updateDS2438(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsQuadConverter':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_DS2450'):
                                    self.logger.debug("Parsing DS2450 devices.")
                                    rom_id = owsSensor.find(self.xmlns + 'ROMId').text
                                    if dev.pluginProps['romID'] == rom_id \
                                            and dev.pluginProps['serverList'] == server_ip:
                                        self.updateDS2450(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsTemperatureSensor64':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0064'):
                                    self.logger.debug("Parsing EDS0064 devices.")
                                    rom_id = owsSensor.find(self.xmlns + 'ROMId').text
                                    if dev.pluginProps['romID'] == rom_id \
                                            and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0064(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsTemperatureHumiditySensor65':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0065'):
                                    self.logger.debug("Parsing EDS0065 devices.")
                                    rom_id = owsSensor.find(self.xmlns + 'ROMId').text
                                    if dev.pluginProps['romID'] == rom_id \
                                            and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0065(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsTemperaturePressureSensor66':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0066'):
                                    self.logger.debug("Parsing EDS0066 devices.")
                                    rom_id = owsSensor.find(self.xmlns + 'ROMId').text
                                    if dev.pluginProps['romID'] == rom_id \
                                            and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0066(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsTemperatureLight':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0067'):
                                    self.logger.debug("Parsing EDS0067 devices.")
                                    rom_id = owsSensor.find(self.xmlns + 'ROMId').text
                                    if dev.pluginProps['romID'] == rom_id \
                                            and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0067(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == \
                                    'owsTemperatureHumidityBarometricPressureLight':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0068'):
                                    self.logger.debug("Parsing EDS0068 devices.")
                                    rom_id = owsSensor.find(self.xmlns + 'ROMId').text
                                    if dev.pluginProps['romID'] == rom_id \
                                            and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0068(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsVibrationSensor':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0070'):
                                    self.logger.debug("Parsing EDS0070 devices.")
                                    rom_id = owsSensor.find(self.xmlns + 'ROMId').text
                                    if dev.pluginProps['romID'] == rom_id \
                                            and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0070(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsRTDinterfaceFourWire71':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0071'):
                                    self.logger.debug("Parsing EDS0071 devices.")
                                    rom_id = owsSensor.find(self.xmlns + 'ROMId').text
                                    if dev.pluginProps['romID'] == rom_id \
                                            and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0071(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsOctalMilliampInput80':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0080'):
                                    self.logger.debug("Parsing EDS0080 devices.")
                                    rom_id = owsSensor.find(self.xmlns + 'ROMId').text
                                    if dev.pluginProps['romID'] == rom_id \
                                            and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0080(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsOctalCurrentDevice':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0082'):
                                    self.logger.debug("Parsing EDS0082 devices.")
                                    rom_id = owsSensor.find(self.xmlns + 'ROMId').text
                                    if dev.pluginProps['romID'] == rom_id \
                                            and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0082(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsOctalCurrentDevice83':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0083'):
                                    self.logger.debug("Parsing EDS0083 devices.")
                                    rom_id = owsSensor.find(self.xmlns + 'ROMId').text
                                    if dev.pluginProps['romID'] == rom_id \
                                            and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0083(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsQuadCurrentDevice':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0085'):
                                    self.logger.debug("Parsing EDS0085 devices.")
                                    rom_id = owsSensor.find(self.xmlns + 'ROMId').text
                                    if dev.pluginProps['romID'] == rom_id \
                                            and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0085(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsOctalDiscreteIO90':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0090'):
                                    self.logger.debug("Parsing EDS0090 devices.")
                                    rom_id = owsSensor.find(self.xmlns + 'ROMId').text
                                    if dev.pluginProps['romID'] == rom_id \
                                            and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0090(dev, owsSensor, server_ip)

                        except Exception:  # noqa
                            self.logger.critical("Error in server parsing routine.")
                            self.logger.exception()

            except Exception:  # noqa
                # There has been a problem reaching the server. "Turn off" all sensors until next
                # successful poll.
                _ = [
                    dev.updateStateOnServer('onOffState', value=False)
                    for dev in indigo.devices.itervalues("self")
                ]
                self.logger.warning("Error parsing sensor states.")
                self.logger.warning(f"Trying again in {pref_poll} seconds.")

        self.logger.debug("  No more sensors to poll.")

        if not self.pluginPrefs.get("suppressResultsLogging", False):
            self.logger.info(f"  Total of {self.number_of_servers} servers polled.")
            self.logger.info(f"  Total of {self.number_of_sensors} devices updated.")
            self.logger.info("OWServer data parsed successfully.")
