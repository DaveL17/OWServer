#! /usr/bin/env python2.6
# -*- coding: utf-8 -*-

"""
OWserver Embedded Data Systems (EDS) 1-Wire Server Plugin
Author: DaveL17

Plugin for Indigo Home Control Server:
    http://www.indigodomo.com
    http://www.edsproducts.com

The OWServer Plugin loads XML data from one or more EDS 1-Wire servers,
interprets the information, and makes it available for plugin-supported
devices. The plugin supports the following server types:

OW-SERVER-ENET
OW-SERVER-WiFi
OW-SERVER-ENET2
OW-SERVER-WiFi-2G

The plugin does _not_ support the HTML-based output of the HA7NET
server.
"""

# ================================== IMPORTS ==================================

# Built-in modules
import datetime as dt
import json
import socket
import traceback
import urllib2
import xml.etree.ElementTree as eTree

# Third-party modules
try:
    import indigo
except ImportError:
    pass
try:
    import pydevd
except ImportError:
    pass

# My modules
import DLFramework.DLFramework as Dave
import stateDict

# =================================== HEADER ==================================

__author__    = Dave.__author__
__copyright__ = Dave.__copyright__
__license__   = Dave.__license__
__build__     = Dave.__build__
__title__     = 'OWServer Plugin for Indigo Home Control'
__version__   = '1.0.10'

# =============================================================================

kDefaultPluginPrefs = {
    u"configMenuDegrees"      : "F",    # Setting for devices that report temperature.
    u"configMenuDegreesDec"   : "1",    # For devices that report temperature.
    u"configMenuHumidexDec"   : "1",    # For devices that report Humidex.
    u"configMenuHumidityDec"  : "1",    # For devices that report Humidity.
    u"configMenuPollInterval" : "900",  # How frequently OWServer will refresh.
    u"configMenuServerTimeout": "15",   # How long to wait for a response.
    u"configMenuServerType"   : "OW",   # What kind of server is it?
    u"OWServerIP"             : "",     # List of server IP address(es).
    u"showDebugInfo"          : False,  # Verbose debug logging?
    u"showDebugLevel"         : "1",    # Low, Medium or High debug output.
    u"suppressResultsLogging" : False,  # Don't log unless there's a problem.
}


class Plugin(indigo.PluginBase):

    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

        self.pluginIsInitializing = True
        self.pluginIsShuttingDown = False

        self.stateDict = stateDict.OWServer(self)
        self.deviceList = []
        self.numberOfSensors = 0
        self.numberOfServers = 0
        self.debug = self.pluginPrefs.get('showDebugInfo', False)
        self.padLog = "\n" + (" " * 34)  # 34 spaces to continue in line with log margin.
        self.xmlns = '{http://www.embeddeddatasystems.com/schema/owserver}'

        # ====================== Initialize DLFramework =======================

        self.Fogbert = Dave.Fogbert(self)

        # Log pluginEnvironment information when plugin is first started
        self.Fogbert.pluginEnvironment()

        # Convert old debugLevel scale (low, medium, high) to new scale (1, 2, 3).
        if not 0 < self.pluginPrefs.get('showDebugLevel', 1) <= 3:
            self.pluginPrefs['showDebugLevel'] = self.Fogbert.convertDebugLevel(self.pluginPrefs['showDebugLevel'])

        # =====================================================================

        if self.pluginPrefs['showDebugLevel'] >= 3:
            self.debugLog(u"=" * 101 + self.padLog +
                          u"Caution! Debug set to high. Output contains sensitive information (MAC address, ROM IDs, email, etc.)"
                          + self.padLog + u"=" * 101)
            self.sleep(3)
        else:
            self.debugLog(u"Debug level set to [Low (1), Medium (2), High (3)]: {0}".format(self.pluginPrefs['showDebugLevel']))

        # Debug output contains sensitive info, show only if debugLevel is high.
        if self.pluginPrefs['showDebugInfo'] and self.pluginPrefs['showDebugLevel'] >= 3:
            self.debugLog(u"{0}".format(pluginPrefs))
        else:
            self.debugLog(u"Plugin preferences suppressed. Set debug level to [High] to write them to the log.")

        # try:
        #     pydevd.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True, suspend=False)
        # except:
        #     pass

        self.pluginIsInitializing = False

    def __del__(self):
        self.debugLog(u"__del__ method called.")
        indigo.PluginBase.__del__(self)

    # =============================================================================
    # ============================== Indigo Methods ===============================
    # =============================================================================
    def closedDeviceConfigUi(self, valuesDict, userCancelled, typeId, devId):

        self.debugLog(u'closedDeviceConfigUi() method called:')

        if userCancelled:
            self.debugLog(u"Device configuration cancelled.")
            return
        else:
            pass

    # =============================================================================
    def closedPrefsConfigUi(self, valuesDict, userCancelled):

        self.debugLog(u"Plugin config dialog window closed.")

        if userCancelled:
            self.debugLog(u"User prefs dialog cancelled.")

        if not userCancelled:
            # If user changed debug setting, update it here.
            self.debug = valuesDict.get('showDebugInfo', False)

            if self.debug:
                self.debugLog(u"Debug logging is on.")
            else:
                self.debugLog(u"Debug logging is off.")

            self.debugLog(u"User prefs saved.")

            # Finally, update all device states upon close
            self.updateDeviceStates()

            return

    # =============================================================================
    def deviceStartComm(self, dev):

        self.debugLog(u"Starting OWServer device: {0}".format(dev.name))
        dev.stateListOrDisplayStateIdChanged()
        dev.updateStateOnServer('onOffState', value=True, uiValue=" ")

    # =============================================================================
    def deviceStopComm(self, dev):

        self.debugLog(u"Stopping OWServer device: {0}".format(dev.name))
        dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

    # =============================================================================
    def runConcurrentThread(self):

        self.debugLog(u"Starting main OWServer thread.")

        self.sleep(5)

        try:
            while True:
                self.spotDeadSensors()
                self.updateDeviceStates()
                sleep_time = int(self.pluginPrefs.get('configMenuPollInterval', 900))
                self.sleep(sleep_time-5)

        except self.StopThread:
            self.debugLog(u"Fatal error. Stopping OWServer thread.")
            pass

    # =============================================================================
    def shutdown(self):

        self.pluginIsShuttingDown = True
        self.debugLog(u"Shutting down OWServer plugin.")

    # =============================================================================
    def startup(self):

        indigo.server.log(u"Starting OWServer.")

        # =========================== Audit Server Version ============================
        self.Fogbert.audit_server_version(min_ver=7)

    # =============================================================================
    def validatePrefsConfigUi(self, valuesDict):

        self.debugLog(u"validatePrefsConfigUi() method called.")

        addr = valuesDict['OWServerIP']
        auto_detect_servers = valuesDict['autoDetectServers']
        error_msg_dict = indigo.Dict()
        split_ip = addr.replace(" ", "").split(",")

        # A valid IP address must be at least 7 characters long.
        if not auto_detect_servers and len(addr) < 7:
            error_msg_dict['OWServerIP'] = u"An IP address is not long enough (at least 0.0.0.0)."
            return False, valuesDict, error_msg_dict

        # Split apart the IP address(es) to ensure that they have at least four parts.
        if not auto_detect_servers:
            for server_ip in split_ip:
                address_parts = server_ip.split(".")
                if len(address_parts) != 4:
                    error_msg_dict['OWServerIP'] = u"Please enter a valid IP address with four valid parts (0.0.0.0)."
                    return False, valuesDict, error_msg_dict

                # Each part must be between the values of 0 and 255 (inclusive).
                for part in address_parts:
                    try:
                        part = int(part)
                        if part < 0 or part > 255:
                            error_msg_dict['OWServerIP'] = u"You have entered a value out of range (not 0-255)."
                            return False, valuesDict, error_msg_dict
                    except ValueError:
                        error_msg_dict['OWServerIP'] = u"You have entered an IP address that contains a non-numeric " \
                                                       u"character."
                        return False, valuesDict, error_msg_dict

        return True

    # =============================================================================
    # ============================== Plugin Methods ===============================
    # =============================================================================
    def sendToServer(self, val):
        """
        Title Placeholder

        The sendToServer() method merely logs the url sent to the server
        for the purposes of confirmation and a signal that the event took
        place.  This is a temporary method which will be removed if it's
        no longer needed.

        -----


        """
        write_url = 'http://{0}/devices.htm?rom={1}&variable={2}&value={3}'.format(val[0], val[1], val[2], val[3])

        try:
            time_out = int(self.pluginPrefs.get('configMenuServerTimeout', 15))
            socket.setdefaulttimeout(time_out)
            f = urllib2.urlopen(write_url)
            f.close()
        except Exception:
            self.Fogbert.pluginErrorHandler(traceback.format_exc())

        self.debugLog(u"Write to server URL: {0}".format(write_url))
        return

    # =============================================================================
    def sendToServerAction(self, val):
        """
        Title Placeholder

        The sendToServerExternal() method is for scripters to be able to
        send individual commands to devices through Indigo Python scripts.
        The syntax for the call is:
        =======================================================================
        pluginId = "com.fogbert.indigoplugin.OWServer"
        plugin = indigo.server.getPlugin(pluginId)
        props = {"server": "10.0.1.44", "romId": "5D000003C74F4528", "variable": "clearAlarms", "value": "0"}
        if plugin.isEnabled():
            plugin.executeAction("sendToServerAction", props)
        =======================================================================

        -----

        """
        parm_list = (val.props.get("server"), val.props.get("romId"), val.props.get("variable"), val.props.get("value"))
        write_url = 'http://{0}/devices.htm?rom={1}&variable={2}&value={3}'.format(*parm_list)
 
        try:
            time_out = int(self.pluginPrefs.get('configMenuServerTimeout', 15))
            socket.setdefaulttimeout(time_out)
            f = urllib2.urlopen(write_url)
            f.close()
        except Exception:
            self.Fogbert.pluginErrorHandler(traceback.format_exc())

        self.debugLog(u"Write to server URL: {0}".format(write_url))
        return

    # =============================================================================
    def toggleDebugEnabled(self):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """

        # Toggle debug on/off.
        self.debugLog(u"toggleDebugEnabled() method called.")

        if not self.debug:
            self.debug = True
            self.pluginPrefs['showDebugInfo'] = True
            indigo.server.log(u"Debugging on.")
            self.debugLog(u"Debug level: {0}".format(self.pluginPrefs.get('showDebugLevel', 1)))
        else:
            self.debug = False
            self.pluginPrefs['showDebugInfo'] = False
            indigo.server.log(u"Debugging off.")

    # =============================================================================
    def actionControlSensor(self, action, dev):
        """
        Title Placeholder

        Get sensor update when user selects 'Send Status Request'. This
        updates all devices.

        -----

        """
        self.debugLog(u"User request for status update.")
        self.debugLog(u"actionControlSensor() method called.")
        self.updateDeviceStates()

    # =============================================================================
    def customWriteToDevice(self, valuesDict, typeId):
        """
        Title Placeholder

        The customWriteToDevice() method is called when a user selects
        the "Write Value to 1-Wire Device" item from the OWServer Plugin
        menu. Selecting this menu item causes a dialog to open which
        asks the user to select the relevant server IP and ROM ID, and
        enter both the variable to change and the value to write. There
        is limited error checking (obvious things) but mostly relies on
        user entering valid information.

        -----

        """
        self.debugLog(u'customWriteToDevice() method called.')

        error_msg_dict    = indigo.Dict()
        write_to_server   = valuesDict['writeToServer']
        write_to_rom      = valuesDict['writeToROM']       # "writeToROM" - alpha must be uppercase
        write_to_variable = valuesDict['writeToVariable']  # "writeToVariable" - must be writeable
        write_to_value    = valuesDict['writeToValue']     # "writeToValue" - must be decimal

        # We can only write decimal values to 1-Wire devices.  So let's check. We won't change the value to something that will work but rather let the user know instead.
        if write_to_variable == "":
            error_msg_dict['writeToVariable'] = u"You must specify a value to write to the 1-Wire device."
            return False, valuesDict, error_msg_dict
        elif " " in write_to_variable:
            error_msg_dict['writeToVariable'] = u"Variable names cannot contain a space."
            return False, valuesDict, error_msg_dict

        if write_to_value == "":
            error_msg_dict['writeToValue'] = u"You must specify a value to write to the 1-Wire device."
            return False, valuesDict, error_msg_dict

        try:
            float(write_to_value)
        except:
            error_msg_dict['writeToValue'] = u"Only decimal values can be written to 1-Wire devices."
            return False, valuesDict, error_msg_dict

        # All tests passed, so construct the URL to send to the server.
        write_to_url = "http://{0}/devices.htm?rom={1}&variable={2}&value={3}".format(write_to_server, write_to_rom, write_to_variable, write_to_value)

        self.debugLog(u"URL constructed to post data to device: {0}".format(write_to_url))

        # Send the URL to the server.
        try:
            time_out = int(self.pluginPrefs.get('configMenuServerTimeout', 15))
            socket.setdefaulttimeout(time_out)
            f = urllib2.urlopen(write_to_url)
            f.close()

            indigo.server.log(u"{0}: {1} written successfully.".format(write_to_variable, write_to_value))
            return True

        # What happens if we're unsuccessful.
        except urllib2.HTTPError as error:
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            self.errorLog(u"HTTP error writing server data.")
            error_msg_dict['writeToServer'] = u"{0}".format(error.reason)
            return False, valuesDict, error_msg_dict
        except IOError as error:  # TODO: Check to see if these are IOErrors.
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            self.errorLog(u"Exception error getting server data.")
            # (no number, timed out)
            # (51, Network is unreachable) - OWServer has no LAN access
            # (50, Network is down) - EDS hardware offline
            # (54, Connection reset by peer) - EDS hardware offline
            error_msg_dict['writeToServer'] = u"{0}".format(error)
            return False, valuesDict, error_msg_dict
        except Exception as error:
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            self.errorLog(u"Misc. error downloading details.xml file. If the problem persists, please enable debugging "
                          u"in the OWServer configuration dialog and check user forum for more information.")
            error_msg_dict['writeToServer'] = u"{0}".format(error)
            return False, valuesDict, error_msg_dict

    # =============================================================================
    def dumpXML(self, valuesDict, typeId):
        """
        Title Placeholder

        dumpXML(self, valuesDict): This method grabs a copy of the
        details.xml file from the server at the specified IP address,
        parses it, and dumps a copy to a log file. The purpose is for
        the user to be able to confirm that the 1-Wire server is online
        and that the plugin can talk to it. Log file is written to the
        Indigo server logs folder.

        -----

        """
        self.debugLog(u"Dumping details.xml file to Indigo log file...")

        addr = valuesDict['writeToServer']
        split_ip = addr.replace(" ", "").split(",")

        for server_ip in split_ip:
            try:
                ows_xml = self.getDetailsXML(server_ip)
                if valuesDict['writeXMLToLog']:
                    file_name = ('{0}/{1} OWServer.txt'.format(indigo.server.getLogsFolderPath(), dt.datetime.today().date()))
                    data = open(file_name, "w")
                    data.write("OWServer details.xml Log\n")
                    data.write("Written at: {0}\n".format(dt.datetime.today()))
                    data.write("=" * 72 + "\n")
                    data.write(str(ows_xml))
                    data.close()

                else:
                    pass

                if not ows_xml:
                    self.errorLog(u"Server IP: {0} failed.".format(server_ip))
                else:
                    indigo.server.log(u"Server IP: {0} passed.".format(server_ip))

                ows_xml = ''

            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.errorLog(u"Can't dump XML to log. Check server connection.")
                pass

        return True

    # =============================================================================
    def getDetailsXML(self, server_ip):
        """
        Title Placeholder

        getDetailsXML(): This method goes out to the 1-Wire server at
        the specified OWServerIP address and pulls in a copy of the
        details.xml file. It doesn't process it any way.

        -----

        """
        self.debugLog(u"getDetailsXML() method called.")

        try:
            url = 'http://{0}/details.xml'.format(server_ip)

            time_out = int(self.pluginPrefs.get('configMenuServerTimeout', 15))
            socket.setdefaulttimeout(time_out)
            f = urllib2.urlopen(url)
            ows_xml = f.read()
            f.close()
            ows_xml = unicode(ows_xml)
            self.debugLog(u"details.xml file retrieved successfully.")
            return ows_xml

        # What happens if we're unsuccessful.
        except urllib2.HTTPError as error:
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            self.errorLog(u"HTTP error getting server data.")
        except IOError:
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            self.errorLog(u"Error getting server data.")
            # (no number, timed out)
            # (51, Network is unreachable) - OWServer has no LAN access
            # (50, Network is down) - EDS hardware offline
            # (54, Connection reset by peer) - EDS hardware offline
        except Exception:
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            self.errorLog(u"Misc. error downloading details.xml file. If the problem persists, please enable debugging "
                          u"in the OWServer configuration dialog and check user forum for more information.")

    # =============================================================================
    def getSensorList(self, filter="indigo.sensor", typeId=0, valuesDict=None, targetId=0):
        """
        Title Placeholder

        getSensorList(): This method constructs a list of 1-Wire
        sensors that have  been added to all servers. It's called when
        the user opens up a device config dialog. If there are no
        sensors left to assign (they have all been assigned to other
        devices) then the user is sent a message 'No sensors to add.'
        This string is necessary to address conditions where the method
        returns a noneType value instead of a list (Indigo throws an
        error when this happens.)

        -----


        """
        self.debugLog(u"getSensorList() method called.")
        self.debugLog(u"Generating list of 1-Wire sensors...")

        server_list        = self.pluginPrefs.get('OWServerIP', None)
        clean_server_list  = server_list.replace(' ', '').split(',')
        sorted_server_list = sorted(clean_server_list)
        sensor_id_list     = []

        for IP in sorted_server_list:
            try:
                ows_xml = self.getDetailsXML(IP)
                root = eTree.fromstring(ows_xml)

                if self.pluginPrefs['showDebugInfo'] and self.pluginPrefs['showDebugLevel'] >= 3:
                    self.debugLog(u"{0}".format(ows_xml))

                # Build a list of ROM IDs for all 1-Wire sensors on the network. We start  by parsing out a list of all ROM IDs in the source details.xml file. The resulting
                # list is called "sensorID_list"
                for child in root:
                    if "owd_" in child.tag:
                        rom_id = child.find(self.xmlns + 'ROMId')
                        sensor_id_list = sensor_id_list + [rom_id.text]

                # If the list is empty, there are no ROM IDs in details.xml. Let's proceed with an empty list.
                if sensor_id_list is None:
                    sensor_id_list = []

                # Sort the list (to make it easy to find the ROM ID needed), and return the list.
                sorted_sensor_list = sorted(sensor_id_list)

            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.debugLog(u"Error reading sensor data from servers.")
                sorted_sensor_list = [u"Error reading data from servers."]

        return sorted_sensor_list

    # =============================================================================
    def getServerList(self, filter="indigo.sensor", typeId=0, valuesDict=None, targetId=0):
        """
        Title Placeholder

        getServerList(): This method provides the callback for defining
        server devices. It obtains its list of server IP addresses from
        one of two distinct procedures: (1) automatic server detection,
        and (2) manual declaration of server IPs. Within the plugin
        configuration dialog, the user either accepts automatic detection
        or else enters a comma delimited list of addresses. Despite
        whichever procedure is used, getServerList() returns a list
        (sorted_server_list) containing the list of IPs. This list is
        used to assign IP addresses when the user creates OWServer
        devices.

        -----

        """
        self.debugLog(u"getServerList() method called.")

        if not self.pluginPrefs.get('autoDetectServers', True):
            server_list        = self.pluginPrefs.get('OWServerIP', None)
            clean_server_list  = server_list.replace(" ", "").split(",")
            sorted_server_list = sorted(clean_server_list)
            return sorted_server_list

        else:
            master_list = []
            # We will ignore everything that responds to our UDP broadcast request unless it has one of the following in it's return.
            server_list = ["OWServer_v2-Enet", "OWServer_v2G-WiFi", "OWServer-Enet", "OW_SERVER-Enet"]

            try:
                socket.setdefaulttimeout(0.5)
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
                s.sendto("D", ('<broadcast>', 30303))

                while True:
                    response = s.recv(2048)
                    if response.find('{') >= 0:
                        response = response[response.find('{'):response.find('}')+1]

                        # This code removes a comma after the last field, which is sent in some older versions of EDS products.
                        comma_err = response.find(',\r\n}')
                        if comma_err > 64:
                            response = response[:comma_err] + '}'

                        # Unpack the response and add it to the server list.
                        j = json.loads(response)
                        master_list.append(j['IP'])

            except socket.timeout:
                s.close()
                sorted_server_list = sorted(master_list)
                return sorted_server_list

            except Exception as e:
                err = e.args
                if err[0] == 51:
                    self.errorLog(u"The network is unreachable.")
                    response = ""
                else:
                    self.Fogbert.pluginErrorHandler(traceback.format_exc())
                    response = ""

    # =============================================================================
    def killAllComms(self):
        """
        Title Placeholder

        killAllComms() sets the enabled status of all plugin devices to
        false.

        -----

        """
        self.debugLog(u"killAllComms() method called.")

        for dev in indigo.devices.itervalues("self"):
            try:
                indigo.device.enable(dev, value=False)
            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.errorLog(u"Unable to kill communication with all devices.")

    # =============================================================================
    def unkillAllComms(self):
        """
        Title Placeholder

        unkillAllComms() sets the enabled status of all plugin devices
        to true.

        -----

        """
        self.debugLog(u"unkillAllComms() method called.")

        for dev in indigo.devices.itervalues("self"):
            try:
                indigo.device.enable(dev, value=True)
            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.errorLog(u"Unable to enable communication with all devices.")

    # =============================================================================
    def romIdGenerator(self, filter="indigo.sensor", valuesDict=None, typeId=0, targetId=0):
        """
        Title Placeholder

        The romIdGenerator() method will return a list of the ROM IDs
        appropriate to the calling device. That is, when the user
        selects an IP address for the appropriate server, the method
        will refresh the ROM ID list to show only those IDs that are
        appropriate to that IP.

        -----

        """
        self.debugLog(u"romIdGenerator() method called.")

        # This is a placeholder for future functionality. Not sure it's possible to return the list of ROM IDs
        # specific to the server IP selected as it hasn't been returned to the device dict yet.

        indigo.server.log(u"{0}".format(indigo.devices[typeId].pluginProps['serverList']))

        # this is not in the dict for a new device. could have the user save the device and then come back, but that's
        # kludgy.

    # =============================================================================
    def spotDeadSensors(self):
        """
        Title Placeholder

        spotDeadSensors(self): This method compares the time each
        plugin device was last updated to the current Indigo time. If
        the difference exceeds a set interval (currently set to 60
        seconds, then the sensor's onOffState is set to false and an
        error is thrown to the log. This condition could be for a
        number of reasons including sensor fail, wiring fail, 1-Wire
        network collisions, etc.

        -----

        """
        self.debugLog(u"spotDeadSensors() method called.")

        for dev in indigo.devices.itervalues("self"):
            if dev.enabled:
                diff_time = indigo.server.getTime() - dev.lastChanged
                pref_poll = int(self.pluginPrefs.get('configMenuPollInterval', 900))
                dead_time = (
                    dt.timedelta(seconds=pref_poll) +
                    dt.timedelta(seconds=60))

                # If a sensor has been offline for more than the specified amount of time, throw a message to the log and mark it offline. Starting with 60 seconds.
                if diff_time <= dead_time:
                    pass

                else:
                    self.errorLog(u"{0} hasn't been updated in {1}. If this condition persists, check it's connection.".format(dev.name, diff_time))
                    try:
                        dev.updateStateOnServer('onOffState', value=False, uiValue="")
                    except Exception:
                        self.Fogbert.pluginErrorHandler(traceback.format_exc())
                        self.errorLog(u"Unable to spot dead sensors.")

    # =============================================================================
    def humidexConvert(self, ows_humidex):
        """
        Title Placeholder

        humidexConvert(self): This method converts any humidex values
        used in the plugin based on user preference:
        self.pluginPrefs[u'configMenuHumidexDec'].

        -----

        """
        self.debugLog(u"  Converting humidex values.")

        try:
            # Format the humidex value to the requested number of decimal places.
            format_humidex = u"%.{0}f".format(self.pluginPrefs.get('configMenuHumidexDec', "1"))
            ows_humidex = float(ows_humidex)
            ows_humidex = (format_humidex % ows_humidex)
            return ows_humidex

        except Exception:
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            self.errorLog(u"Error formatting humidex value. Returning value unchanged.")
            return ows_humidex

    # =============================================================================
    def humidityConvert(self, ows_humidity):
        """
        Title Placeholder

        humidityConvert(self): This method converts any humidity values
        used in the plugin based on user preference:
        self.pluginPrefs[u'configMenuHumidityDec'].

        -----

        """
        self.debugLog(u"  Converting humidity values.")

        try:
            # Format the humidity value to the requested number of decimal places.
            format_humidity = u"%.{0}f".format(self.pluginPrefs.get('configMenuHumidityDec', "1"))
            ows_humidity    = float(ows_humidity)
            ows_humidity    = (format_humidity % ows_humidity)
            return ows_humidity

        except Exception:
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            self.errorLog(u"Error formatting humidity value. Returning value unchanged.")
            return ows_humidity

    # =============================================================================
    def pressureConvert(self, ows_pressure):
        """
        Title Placeholder

        pressureConvert(self): This method converts any pressure values
        used in the plugin based on user preference:
        self.pluginPrefs[u'configMenuPressureDec'].

        -----

        """
        self.debugLog(u"  Converting pressure values.")

        try:
            # Format the pressure value to the requested number of decimal places.
            format_pressure = u"%.{0}f".format(self.pluginPrefs.get('configMenuPressureDec', "1"))
            ows_pressure = float(ows_pressure)
            ows_pressure = (format_pressure % ows_pressure)
            return ows_pressure

        except Exception:
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            self.errorLog(u"Error formatting pressure value. Returning value unchanged.")
            return ows_pressure

    # =============================================================================
    def tempConvert(self, ows_temp):
        """
        Title Placeholder

        tempConvert(self): This method converts any temperature values
        used in the plugin based on user preference:
        self.pluginPrefs[u'configMenuDegreesDec']. This method returns
        a string that is formatted based on user preferences.

        -----

        """
        self.debugLog(u"  Converting temperature values.")

        # Format the temperature value to the requested number of decimal places.
        format_temp = u"%.{0}f".format(self.pluginPrefs.get('configMenuDegreesDec', "1"))

        if self.pluginPrefs.get('configMenuDegrees', 'F') == "C":
            ows_temp = float(ows_temp)
            ows_temp = (format_temp % ows_temp)
            return ows_temp

        elif self.pluginPrefs.get('configMenuDegrees', 'F') != "C":
            ows_temp = float(ows_temp) * 1.8000 + 32.00
            ows_temp = (format_temp % ows_temp)
            return ows_temp

    # =============================================================================
    def voltsConvert(self, ows_volts):
        """
        Title Placeholder

        voltsConvert(self): This method converts any voltages values
        used in the plugin based on user preference:
        self.pluginPrefs[u'configMenuVoltsDec']. This method returns
        a string that is formatted based on user preferences.

        -----

        """
        self.debugLog(u"  Converting volts values.")

        # Format the value to the requested number of decimal places.
        format_volts = u"%.{0}f".format(self.pluginPrefs.get('configMenuVoltsDec', "1"))
        ows_volts    = float(ows_volts)
        ows_volts    = (format_volts % ows_volts)
        return ows_volts

    # =============================================================================
    # ================== Server and Sensor Device Update Methods ==================
    #  =============================================================================
    def updateOWServer(self, dev, root, server_ip):
        """
        Title Placeholder

        Server Type: Covers OWSERVER-ENET Rev. 1 and Rev. 2

        -----

        """
        self.debugLog(u"updateOWServer() method called.")

        try:
            server_state_dict = self.stateDict.serverStateDict()

            for key, value in server_state_dict.iteritems():
                try:
                    dev.updateStateOnServer(key, value=root.find(self.xmlns + value).text)
                except AttributeError:
                    dev.updateStateOnServer(key, value=u"Unsupported")

            try:
                devices_connected = root.find(self.xmlns + 'DevicesConnected').text
                if devices_connected == "1":
                    input_value = u"{0} sensor".format(devices_connected)
                else:
                    input_value = u"{0} sensors".format(devices_connected)
                dev.updateStateOnServer('onOffState', value=True, uiValue=input_value)
                dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
                dev.updateStateOnServer('onOffState', value=False, uiValue=" ")

            new_props = dev.pluginProps
            new_props['address'] = dev.states['owsMACAddress']
            dev.replacePluginPropsOnServer(new_props)

            self.numberOfServers += 1
            server_state_dict = {}

            self.debugLog(u"Success. Polling next server if appropriate.")
            return True

        except Exception:
            self.errorLog(u"Server update failure. Check settings.")
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateDS18B20(self, dev, owsSensor, server_ip):
        """
        Title Placeholder

        DS18B20 Description = "Programmable resolution thermometer"

        -----

        """
        self.debugLog(u"updateDS18B20() method called.")

        try:
            DS18B20_state_dict = self.stateDict.DS18B20StateDict()

            for key, value in DS18B20_state_dict.iteritems():
                try:
                    if key == "owsTemperature":
                        ows_temp    = owsSensor.find(self.xmlns + 'Temperature').text
                        comp_val    = dev.pluginProps.get('DS18B20TempComp', '0.0')
                        input_value = float(ows_temp) + float(comp_val)
                        input_value = self.tempConvert(input_value)
                        dev.updateStateOnServer(key, value=input_value)
                    else:
                        dev.updateStateOnServer(key, value=owsSensor.find(self.xmlns + value).text)
                except Exception:
                    self.Fogbert.pluginErrorHandler(traceback.format_exc())
                    self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                    self.debugLog(u"Key: {0} : Value: Unsupported".format(key))
                    dev.updateStateOnServer(key, value=u"Unsupported")

            try:
                ows_temp    = owsSensor.find(self.xmlns + 'Temperature').text
                comp_val    = dev.pluginProps.get('DS18B20TempComp', '0.0')
                input_value = float(ows_temp) + float(comp_val)
                input_value = self.tempConvert(input_value)
                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)
            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                dev.updateStateOnServer('sensorValue', value=u"Unsupported", uiValue=u"Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']          = dev.states['owsRomID']
            new_props['DS18B20UserByte1'] = owsSensor.find(self.xmlns + 'UserByte1').text
            new_props['DS18B20UserByte2'] = owsSensor.find(self.xmlns + 'UserByte2').text
            dev.replacePluginPropsOnServer(new_props)

            self.numberOfSensors += 1
            DS18B20_state_dict = {}

            dev.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)
            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.debugLog(u"Success. Polling next sensor if appropriate.")
            return True

        except Exception:
            self.errorLog(u"Sensor update failure. Check connection.")
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateDS18S20(self, dev, owsSensor, server_ip):
        """
        Title Placeholder

        DS18S20 Description = "Parasite Power Thermometer"

        -----

        """
        self.debugLog(u"updateDS18S20() method called.")

        try:
            DS18S20_state_dict = self.stateDict.DS18S20StateDict()

            for key, value in DS18S20_state_dict.iteritems():
                try:
                    if key == "owsTemperature":
                        ows_temp    = owsSensor.find(self.xmlns + 'Temperature').text
                        comp_val    = dev.pluginProps.get('DS18S20TempComp', '0.0')
                        input_value = float(ows_temp) + float(comp_val)
                        input_value = self.tempConvert(input_value)
                        dev.updateStateOnServer(key, value=input_value)
                    else:
                        dev.updateStateOnServer(key, value=owsSensor.find(self.xmlns + value).text)
                except Exception:
                    self.Fogbert.pluginErrorHandler(traceback.format_exc())
                    self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                    self.debugLog(u"Key: {0} : Value: Unsupported".format(key))
                    dev.updateStateOnServer(key, value=u"Unsupported")

            try:
                ows_temp    = owsSensor.find(self.xmlns + 'Temperature').text
                comp_val    = dev.pluginProps.get('DS18S20TempComp', '0.0')
                input_value = float(ows_temp) + float(comp_val)
                input_value = self.tempConvert(input_value)
                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)
            except Exception:
                self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                dev.updateStateOnServer('sensorValue', value=u"Unsupported", uiValue=u"Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']          = dev.states['owsRomID']
            new_props['DS18S20UserByte1'] = owsSensor.find(self.xmlns + 'UserByte1').text
            new_props['DS18S20UserByte2'] = owsSensor.find(self.xmlns + 'UserByte2').text
            dev.replacePluginPropsOnServer(new_props)

            self.numberOfSensors += 1
            DS18S20_state_dict = {}

            dev.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)
            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.debugLog(u"Success. Polling next sensor if appropriate.")
            return True

        except Exception:
            self.errorLog(u"Sensor update failure. Check connection.")
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateDS2406(self, dev, owsSensor, server_ip):
        """
        Title Placeholder

        DS2406 Description = "Dual Addressable Switch Plus Memory"

        -----

        """
        self.debugLog(u"updateDS2406() method called.")

        try:
            DS2406_state_dict = self.stateDict.DS2406StateDict()

            for key, value in DS2406_state_dict.iteritems():
                try:
                    dev.updateStateOnServer(key, value=owsSensor.find(self.xmlns + value).text)
                except Exception:
                    self.Fogbert.pluginErrorHandler(traceback.format_exc())
                    self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                    self.debugLog(u"Key: {0} : Value: Unsupported".format(key))
                    dev.updateStateOnServer(key, value=u"Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue2406'] == "I_A":  # Input Level A
                    input_value = owsSensor.find(self.xmlns + 'InputLevel_A').text
                    if input_value == "0":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue2406'] == "I_B":  # Input Level B
                    input_value = owsSensor.find(self.xmlns + 'InputLevel_B').text
                    if input_value == "0":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                dev.updateStateOnServer('sensorValue', value=u"Unsupported", uiValue=u"Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address'] = dev.states['owsRomID']
            new_props['DS2406ActivityLatchReset'] = owsSensor.find(self.xmlns + 'ActivityLatchReset').text
            dev.replacePluginPropsOnServer(new_props)

            self.numberOfSensors += 1
            DS2406_state_dict = {}

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.debugLog(u"Success. Polling next sensor if appropriate.")
            return True

        except Exception:
            self.errorLog(u"Sensor update failure. Check connection.")
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateDS2408(self, dev, owsSensor, server_ip):
        """
        Title Placeholder

        DS2408 Description = "8-Channel Addressable Switch"

        -----

        """
        self.debugLog(u"updateDS2408() method called.")

        try:
            DS2408_state_dict = self.stateDict.DS2408StateDict()

            for key, value in DS2408_state_dict.iteritems():
                try:
                    dev.updateStateOnServer(key, value=owsSensor.find(self.xmlns + value).text)
                except Exception:
                    self.Fogbert.pluginErrorHandler(traceback.format_exc())
                    self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                    self.debugLog(u"Key: {0} : Value: Unsupported".format(key))
                    dev.updateStateOnServer(key, value=u"Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                # We need to parse the switch state out of the binary number stored in PIOOutputLatchState.
                latch_state     = float(dev.states['owsPIOOutputLatchState'])
                latch_state_int = int(latch_state)
                latch_state_bin = int(bin(latch_state_int)[2:])
                latch_state_str = str(latch_state_bin)
                latch_state_str = latch_state_str.zfill(8)

                # These states don't exist in the details.xml file. We impute them from <PIOOutputLatchState>.
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

            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                dev.updateStateOnServer('sensorValue', value=u"Unsupported", uiValue=u"Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']                     = dev.states['owsRomID']
            new_props['DS2408PIOActivityLatchState'] = owsSensor.find(self.xmlns + 'PIOActivityLatchState').text
            new_props['DS2408PIOOutputLatchState']   = owsSensor.find(self.xmlns + 'PIOOutputLatchState').text
            new_props['DS2408PowerOnResetLatch']     = owsSensor.find(self.xmlns + 'PowerOnResetLatch').text
            new_props['DS2408RSTZconfiguration']     = owsSensor.find(self.xmlns + 'RSTZconfiguration').text
            dev.replacePluginPropsOnServer(new_props)

            self.numberOfSensors += 1
            DS2408_state_dict = {}

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.debugLog(u"Success. Polling next sensor if appropriate.")
            return True

        except Exception:
            self.errorLog(u"Sensor update failure. Check connection.")
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateDS2423(self, dev, owsSensor, server_ip):
        """
        Title Placeholder

        DS2423 Description = "RAM with Counters"

        -----

        """
        self.debugLog(u"updateDS2423() method called.")

        try:
            DS2423_state_dict = self.stateDict.DS2423StateDict()

            for key, value in DS2423_state_dict.iteritems():
                try:
                    dev.updateStateOnServer(key, value=owsSensor.find(self.xmlns + value).text)
                except Exception:
                    self.Fogbert.pluginErrorHandler(traceback.format_exc())
                    self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                    self.debugLog(u"Key: {0} : Value: Unsupported".format(key))
                    dev.updateStateOnServer(key, value=u"Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue2423'] == "C_A":  # Counter A
                    input_value = owsSensor.find(self.xmlns + 'Counter_A').text
                if dev.pluginProps['prefSensorValue2423'] == "C_B":  # Counter B
                    input_value = owsSensor.find(self.xmlns + 'Counter_B').text

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)
                dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                dev.updateStateOnServer('sensorValue', value=u"Unsupported", uiValue=u"Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            # The DS2423 does not have any writable parameters.
            new_props = dev.pluginProps
            new_props['address'] = dev.states['owsRomID']
            dev.replacePluginPropsOnServer(new_props)

            self.numberOfSensors += 1
            DS2423_state_dict = {}

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
            self.debugLog(u"Success. Polling next sensor if appropriate.")
            return True

        except Exception:
            self.errorLog(u"Sensor update failure. Check connection.")
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateDS2438(self, dev, owsSensor, server_ip):
        """
        Title Placeholder

        DS2438 Description = "Smart battery monitor"

        -----

        """
        self.debugLog(u"updateDS2438() method called.")

        try:
            DS2438_state_dict = self.stateDict.DS2438StateDict()

            for key, value in DS2438_state_dict.iteritems():
                try:
                    if key == "owsTemperature":
                        ows_temp = owsSensor.find(self.xmlns + 'Temperature').text
                        comp_val = dev.pluginProps.get('DS2438TempComp', '0.0')
                        input_value = float(ows_temp) + float(comp_val)
                        input_value = self.tempConvert(input_value)
                        dev.updateStateOnServer(key, value=input_value)
                    else:
                        dev.updateStateOnServer(key, value=owsSensor.find(self.xmlns + value).text)
                except Exception:
                    self.Fogbert.pluginErrorHandler(traceback.format_exc())
                    self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                    self.debugLog(u"Key: {0} : Value: Unsupported".format(key))
                    dev.updateStateOnServer(key, value=u"Unsupported")

            try:
                ows_temp = owsSensor.find(self.xmlns + 'Temperature').text
                comp_val = dev.pluginProps.get('DS2438TempComp', '0.0')
                input_value = float(ows_temp) + float(comp_val)
                input_value = self.tempConvert(input_value)
                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)
            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                dev.updateStateOnServer('sensorValue', value=u"Unsupported", uiValue=u"Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            # The DS2438 does not have any writable parameters.
            new_props = dev.pluginProps
            new_props['address'] = dev.states['owsRomID']
            dev.replacePluginPropsOnServer(new_props)

            self.numberOfSensors += 1
            DS2438_state_dict = {}

            dev.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)
            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.debugLog(u"Success. Polling next sensor if appropriate.")
            return True

        except Exception:
            self.errorLog(u"Sensor update failure. Check connection.")
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateDS2450(self, dev, owsSensor, server_ip):
        """
        Title Placeholder

        DS2450 Description = "Quad A/D Converter"

        -----

        """
        self.debugLog(u"updateDS2450() method called.")

        try:
            DS2450_state_dict = self.stateDict.DS2450StateDict()

            for key, value in DS2450_state_dict.iteritems():
                try:
                    dev.updateStateOnServer(key, value=owsSensor.find(self.xmlns + value).text)
                except Exception:
                    self.Fogbert.pluginErrorHandler(traceback.format_exc())
                    self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                    self.debugLog(u"Key: {0} : Value: Unsupported".format(key))
                    dev.updateStateOnServer(key, value=u"Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue2450'] == "C_A":  # Counter A
                    input_value = owsSensor.find(self.xmlns + 'ChannelAConversionValue').text
                elif dev.pluginProps['prefSensorValue2450'] == "C_B":  # Counter B
                    input_value = owsSensor.find(self.xmlns + 'ChannelBConversionValue').text
                elif dev.pluginProps['prefSensorValue2450'] == "C_C":  # Counter C
                    input_value = owsSensor.find(self.xmlns + 'ChannelCConversionValue').text
                elif dev.pluginProps['prefSensorValue2450'] == "C_D":  # Counter D
                    input_value = owsSensor.find(self.xmlns + 'ChannelDConversionValue').text

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)
                dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                dev.updateStateOnServer('sensorValue', value=u"Unsupported", uiValue=u"Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']                            = dev.states['owsRomID']
            new_props['DS2450ChannelAConversionRange']      = owsSensor.find(self.xmlns + 'ChannelAConversionRange').text
            new_props['DS2450ChannelAConversionResolution'] = owsSensor.find(self.xmlns + 'ChannelAConversionResolution').text
            new_props['DS2450ChannelAOutputControl']        = owsSensor.find(self.xmlns + 'ChannelAOutputControl').text
            new_props['DS2450ChannelAOutputEnable']         = owsSensor.find(self.xmlns + 'ChannelAOutputEnable').text
            new_props['DS2450ChannelBConversionRange']      = owsSensor.find(self.xmlns + 'ChannelBConversionRange').text
            new_props['DS2450ChannelBConversionResolution'] = owsSensor.find(self.xmlns + 'ChannelBConversionResolution').text
            new_props['DS2450ChannelBOutputControl']        = owsSensor.find(self.xmlns + 'ChannelBOutputControl').text
            new_props['DS2450ChannelBOutputEnable']         = owsSensor.find(self.xmlns + 'ChannelBOutputEnable').text
            new_props['DS2450ChannelCConversionRange']      = owsSensor.find(self.xmlns + 'ChannelCConversionRange').text
            new_props['DS2450ChannelCConversionResolution'] = owsSensor.find(self.xmlns + 'ChannelCConversionResolution').text
            new_props['DS2450ChannelCOutputControl']        = owsSensor.find(self.xmlns + 'ChannelCOutputControl').text
            new_props['DS2450ChannelCOutputEnable']         = owsSensor.find(self.xmlns + 'ChannelCOutputEnable').text
            new_props['DS2450ChannelDConversionRange']      = owsSensor.find(self.xmlns + 'ChannelDConversionRange').text
            new_props['DS2450ChannelDConversionResolution'] = owsSensor.find(self.xmlns + 'ChannelDConversionResolution').text
            new_props['DS2450ChannelDOutputControl']        = owsSensor.find(self.xmlns + 'ChannelDOutputControl').text
            new_props['DS2450ChannelDOutputEnable']         = owsSensor.find(self.xmlns + 'ChannelDOutputEnable').text
            new_props['DS2450PowerOnReset']                 = owsSensor.find(self.xmlns + 'PowerOnReset').text
            new_props['DS2450VCCControl']                   = owsSensor.find(self.xmlns + 'VCCControl').text
            dev.replacePluginPropsOnServer(new_props)

            self.numberOfSensors += 1
            DS2450_state_dict = {}

            dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.debugLog(u"Success. Polling next sensor if appropriate.")
            return True

        except Exception:
            self.errorLog(u"Sensor update failure. Check connection.")
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0064(self, dev, owsSensor, server_ip):
        """
        Title Placeholder

        EDS0064 Description = "Octal Current Input Device"

        _____

        """
        self.debugLog(u"updateEDS0064() method called.")

        try:
            EDS0064_state_dict = self.stateDict.EDS0064StateDict()

            for key, value in EDS0064_state_dict.iteritems():
                try:
                    if key == "owsTemperature":
                        ows_temp = owsSensor.find(self.xmlns + 'Temperature').text
                        comp_val = dev.pluginProps.get('EDS0064TempComp', '0.0')
                        input_value = float(ows_temp) + float(comp_val)
                        input_value = self.tempConvert(input_value)
                        dev.updateStateOnServer(key, value=input_value)
                    else:
                        dev.updateStateOnServer(key, value=owsSensor.find(self.xmlns + value).text)
                except Exception:
                    self.Fogbert.pluginErrorHandler(traceback.format_exc())
                    self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                    self.debugLog(u"Key: {0} : Value: Unsupported".format(key))
                    dev.updateStateOnServer(key, value=u"Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0064'] == "C_1":  # Counter 1
                    input_value = owsSensor.find(self.xmlns + 'Counter1').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0064'] == "C_2":  # Counter 2
                    input_value = owsSensor.find(self.xmlns + 'Counter2').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0064'] == "LED":  # LED
                    input_value = owsSensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0064'] == "Relay":  # Relay
                    input_value = owsSensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0064'] == "T":  # Temperature
                    ows_temp = owsSensor.find(self.xmlns + 'Temperature').text
                    comp_val = dev.pluginProps.get('EDS0064TempComp', '0.0')
                    input_value = float(ows_temp) + float(comp_val)
                    input_value = self.tempConvert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                dev.updateStateOnServer('sensorValue', value=u"Unsupported", uiValue=u"Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']                          = dev.states['owsRomID']
            new_props['EDS0064LEDFunction']               = owsSensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0064RelayFunction']             = owsSensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0064TemperatureHighAlarmValue'] = owsSensor.find(self.xmlns + 'TemperatureHighAlarmValue').text
            new_props['EDS0064TemperatureLowAlarmValue']  = owsSensor.find(self.xmlns + 'TemperatureLowAlarmValue').text
            dev.replacePluginPropsOnServer(new_props)

            self.numberOfSensors += 1
            EDS0064_state_dict = {}

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.debugLog(u"Success. Polling next sensor if appropriate.")
            return True

        except Exception:
            self.errorLog(u"Sensor update failure. Check connection.")
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0065(self, dev, owsSensor, server_ip):
        """
        Title Placeholder

        EDS0065 Description = "Temperature and Humidity Sensor"

        -----

        """
        self.debugLog(u"updateEDS0065() method called.")

        try:
            EDS0065_state_dict = self.stateDict.EDS0065StateDict()

            for key, value in EDS0065_state_dict.iteritems():
                try:
                    if key == "owsTemperature":
                        ows_temp = owsSensor.find(self.xmlns + 'Temperature').text
                        comp_val = dev.pluginProps.get('EDS0065TempComp', '0.0')
                        input_value = float(ows_temp) + float(comp_val)
                        input_value = self.tempConvert(input_value)
                        dev.updateStateOnServer(key, value=input_value)
                    else:
                        dev.updateStateOnServer(key, value=owsSensor.find(self.xmlns + value).text)
                except Exception:
                    self.Fogbert.pluginErrorHandler(traceback.format_exc())
                    self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                    self.debugLog(u"Key: {0} : Value: Unsupported".format(key))
                    dev.updateStateOnServer(key, value=u"Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0065'] == "C_1":  # Counter 1
                    input_value = owsSensor.find(self.xmlns + 'Counter1').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0065'] == "C_2":  # Counter 2
                    input_value = owsSensor.find(self.xmlns + 'Counter2').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0065'] == "DP":  # Dew Point
                    dew_point = owsSensor.find(self.xmlns + 'DewPoint').text
                    input_value = self.tempConvert(dew_point)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0065'] == "Hu":  # Humidity
                    humidity = owsSensor.find(self.xmlns + 'Humidity').text
                    input_value = self.humidityConvert(humidity)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0065'] == "Hx":  # Humidex
                    humidex = owsSensor.find(self.xmlns + 'Humidex').text
                    input_value = self.humidexConvert(humidex)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0065'] == "HI":  # Heat Index
                    heat_index = owsSensor.find(self.xmlns + 'HeatIndex').text
                    input_value = self.tempConvert(heat_index)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0065'] == "LED":  # LED
                    input_value = owsSensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0065'] == "Relay":  # Relay
                    input_value = owsSensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0065'] == "T":  # Temperature
                    ows_temp = owsSensor.find(self.xmlns + 'Temperature').text
                    comp_val = dev.pluginProps.get('EDS0065TempComp', '0.0')
                    input_value = float(ows_temp) + float(comp_val)
                    input_value = self.tempConvert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                dev.updateStateOnServer('sensorValue', value=u"Unsupported", uiValue=u"Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address'] = dev.states['owsRomID']
            new_props['EDS0065DewPointHighAlarmValue']    = owsSensor.find(self.xmlns + 'DewPointHighAlarmValue').text
            new_props['EDS0065DewPointLowAlarmValue']     = owsSensor.find(self.xmlns + 'DewPointLowAlarmValue').text
            new_props['EDS0065HeatIndexHighAlarmValue']   = owsSensor.find(self.xmlns + 'HeatIndexHighAlarmValue').text
            new_props['EDS0065HeatIndexLowAlarmValue']    = owsSensor.find(self.xmlns + 'HeatIndexLowAlarmValue').text
            new_props['EDS0065HumidexHighAlarmValue']     = owsSensor.find(self.xmlns + 'HumidexHighAlarmValue').text
            new_props['EDS0065HumidexLowAlarmValue']      = owsSensor.find(self.xmlns + 'HumidexLowAlarmValue').text
            new_props['EDS0065HumidityHighAlarmValue']    = owsSensor.find(self.xmlns + 'HumidityHighAlarmValue').text
            new_props['EDS0065HumidityLowAlarmValue']     = owsSensor.find(self.xmlns + 'HumidityLowAlarmValue').text
            new_props['EDS0065LEDFunction']               = owsSensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0065RelayFunction']             = owsSensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0065TemperatureHighAlarmValue'] = owsSensor.find(self.xmlns + 'TemperatureHighAlarmValue').text
            new_props['EDS0065TemperatureLowAlarmValue']  = owsSensor.find(self.xmlns + 'TemperatureLowAlarmValue').text
            dev.replacePluginPropsOnServer(new_props)

            self.numberOfSensors += 1
            EDS0065_state_dict = {}

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.debugLog(u"Success. Polling next sensor if appropriate.")
            return True

        except Exception:
            self.errorLog(u"Sensor update failure. Check connection.")
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0066(self, dev, owsSensor, server_ip):
        """
        Title Placeholder

        EDS0066 Description = "Temperature and Barometric Pressure Sensor"

        -----

        """
        self.debugLog(u"updateEDS0066() method called.")

        try:
            EDS0066_state_dict = self.stateDict.EDS0066StateDict()

            for key, value in EDS0066_state_dict.iteritems():
                try:
                    if key == "owsTemperature":
                        ows_temp = owsSensor.find(self.xmlns + 'Temperature').text
                        comp_val = dev.pluginProps.get('EDS0066TempComp', '0.0')
                        input_value = float(ows_temp) + float(comp_val)
                        input_value = self.tempConvert(input_value)
                        dev.updateStateOnServer(key, value=input_value)
                    else:
                        dev.updateStateOnServer(key, value=owsSensor.find(self.xmlns + value).text)
                except Exception:
                    self.Fogbert.pluginErrorHandler(traceback.format_exc())
                    self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                    self.debugLog(u"Key: {0} : Value: Unsupported".format(key))
                    dev.updateStateOnServer(key, value=u"Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0066'] == "C_1":  # Counter 1
                    input_value = owsSensor.find(self.xmlns + 'Counter1').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0066'] == "C_2":  # Counter 2
                    input_value = owsSensor.find(self.xmlns + 'Counter2').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0066'] == "BPH":  # Barometric Pressure (Mb)
                    bph = owsSensor.find(self.xmlns + 'BarometricPressureHg').text
                    input_value = self.pressureConvert(bph)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.LightSensor)
                elif dev.pluginProps['prefSensorValue0066'] == "BPM":  # Barometric Pressure (Hg)
                    bpm = owsSensor.find(self.xmlns + 'BarometricPressureMb').text
                    input_value = self.pressureConvert(bpm)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0066'] == "LED":  # LED
                    input_value = owsSensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0066'] == "Relay":  # Relay
                    input_value = owsSensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0066'] == "T":  # Temperature
                    ows_temp = owsSensor.find(self.xmlns + 'Temperature').text
                    comp_val = dev.pluginProps.get('EDS0066TempComp', '0.0')
                    input_value = float(ows_temp) + float(comp_val)
                    input_value = self.tempConvert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                dev.updateStateOnServer('sensorValue', value=u"Unsupported", uiValue=u"Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']                                   = dev.states['owsRomID']
            new_props['EDS0066BarometricPressureHgHighAlarmValue'] = owsSensor.find(self.xmlns + 'BarometricPressureHgHighAlarmValue').text
            new_props['EDS0066BarometricPressureHgLowAlarmValue']  = owsSensor.find(self.xmlns + 'BarometricPressureHgLowAlarmValue').text
            new_props['EDS0066BarometricPressureMbHighAlarmValue'] = owsSensor.find(self.xmlns + 'BarometricPressureMbHighAlarmValue').text
            new_props['EDS0066BarometricPressureMbLowAlarmValue']  = owsSensor.find(self.xmlns + 'BarometricPressureMbLowAlarmValue').text
            new_props['EDS0066LEDFunction']                        = owsSensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0066RelayFunction']                      = owsSensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0066TemperatureHighAlarmValue']          = owsSensor.find(self.xmlns + 'TemperatureHighAlarmValue').text
            new_props['EDS0066TemperatureLowAlarmValue']           = owsSensor.find(self.xmlns + 'TemperatureLowAlarmValue').text
            dev.replacePluginPropsOnServer(new_props)

            self.numberOfSensors += 1
            EDS0066_state_dict = {}

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.debugLog(u"Success. Polling next sensor if appropriate.")
            return True

        except Exception:
            self.errorLog(u"Sensor update failure. Check connection.")
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0067(self, dev, owsSensor, server_ip):
        """
        Title Placeholder

        EDS0067 Description = "Temperature and Light Sensor"

        -----

        """
        self.debugLog(u"updateEDS0067() method called.")

        try:
            EDS0067_state_dict = self.stateDict.EDS0067StateDict()

            for key, value in EDS0067_state_dict.iteritems():
                try:
                    if key == "owsTemperature":
                        ows_temp = owsSensor.find(self.xmlns + 'Temperature').text
                        comp_val = dev.pluginProps.get('EDS0067TempComp', '0.0')
                        input_value = float(ows_temp) + float(comp_val)
                        input_value = self.tempConvert(input_value)
                        dev.updateStateOnServer(key, value=input_value)
                    else:
                        dev.updateStateOnServer(key, value=owsSensor.find(self.xmlns + value).text)
                except Exception:
                    self.Fogbert.pluginErrorHandler(traceback.format_exc())
                    self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                    self.debugLog(u"Key: {0} : Value: Unsupported".format(key))
                    dev.updateStateOnServer(key, value=u"Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0067'] == "C_1":  # Counter 1
                    input_value = owsSensor.find(self.xmlns + 'Counter1').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0067'] == "C_2":  # Counter 2
                    input_value = owsSensor.find(self.xmlns + 'Counter2').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0067'] == "IL":  # Illumination
                    input_value = owsSensor.find(self.xmlns + 'Light').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.LightSensor)
                elif dev.pluginProps['prefSensorValue0067'] == "LED":  # LED
                    input_value = owsSensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0067'] == "Relay":  # Relay
                    input_value = owsSensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0067'] == "T":  # Temperature
                    ows_temp = owsSensor.find(self.xmlns + 'Temperature').text
                    comp_val = dev.pluginProps.get('EDS0067TempComp', '0.0')
                    input_value = float(ows_temp) + float(comp_val)
                    input_value = self.tempConvert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                dev.updateStateOnServer('sensorValue', value=u"Unsupported", uiValue=u"Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']                          = dev.states['owsRomID']
            new_props['EDS0067LEDFunction']               = owsSensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0067LightHighAlarmValue']       = owsSensor.find(self.xmlns + 'LightHighAlarmValue').text
            new_props['EDS0067LightLowAlarmValue']        = owsSensor.find(self.xmlns + 'LightLowAlarmValue').text
            new_props['EDS0067RelayFunction']             = owsSensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0067TemperatureHighAlarmValue'] = owsSensor.find(self.xmlns + 'TemperatureHighAlarmValue').text
            new_props['EDS0067TemperatureLowAlarmValue']  = owsSensor.find(self.xmlns + 'TemperatureLowAlarmValue').text
            dev.replacePluginPropsOnServer(new_props)

            self.numberOfSensors += 1
            EDS0067_state_dict = {}

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.debugLog(u"Success. Polling next sensor if appropriate.")
            return True

        except Exception:
            self.errorLog(u"Sensor update failure. Check connection.")
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0068(self, dev, owsSensor, server_ip):
        """
        Title Placeholder

        EDS0068 Description = "Temperature, Humidity,Barometric
        Pressure and Light Sensor"

        -----

        """
        self.debugLog(u"updateEDS0068() method called.")

        try:
            EDS0068_state_dict = self.stateDict.EDS0068StateDict()

            for key, value in EDS0068_state_dict.iteritems():
                try:
                    if key == "owsTemperature":
                        ows_temp = owsSensor.find(self.xmlns + 'Temperature').text
                        comp_val = dev.pluginProps.get('EDS0068TempComp', '0.0')
                        input_value = float(ows_temp) + float(comp_val)
                        input_value = self.tempConvert(input_value)
                        dev.updateStateOnServer(key, value=input_value)
                    else:
                        dev.updateStateOnServer(key, value=owsSensor.find(self.xmlns + value).text)
                except Exception:
                    self.Fogbert.pluginErrorHandler(traceback.format_exc())
                    self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                    self.debugLog(u"Key: {0} : Value: Unsupported".format(key))
                    dev.updateStateOnServer(key, value=u"Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0068'] == "BH":  # Barometric pressure HG
                    ows_baro_hg = float(owsSensor.find(self.xmlns + 'BarometricPressureHg').text)
                    input_value = self.pressureConvert(ows_baro_hg)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0068'] == "BM":  # Barometric pressure MB
                    ows_baro_mb = float(owsSensor.find(self.xmlns + 'BarometricPressureMb').text)
                    input_value = self.pressureConvert(ows_baro_mb)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0068'] == "C_1":  # Counter 1
                    input_value = owsSensor.find(self.xmlns + 'Counter1').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0068'] == "C_2":  # Counter 2
                    input_value = owsSensor.find(self.xmlns + 'Counter2').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0068'] == "DP":  # Dewpoint
                    dewpoint = owsSensor.find(self.xmlns + 'DewPoint').text
                    input_value = self.tempConvert(dewpoint)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0068'] == "HI":  # Heat Index
                    heat_index = owsSensor.find(self.xmlns + 'HeatIndex').text
                    input_value = self.tempConvert(heat_index)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0068'] == "HX":  # Humidex
                    ows_humidex = owsSensor.find(self.xmlns + 'Humidex').text
                    input_value = self.humidexConvert(ows_humidex)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0068'] == "HY":  # Humidity
                    ows_humidity = owsSensor.find(self.xmlns + 'Humidity').text
                    input_value = self.humidityConvert(ows_humidity)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0068'] == "IL":  # Illumination
                    input_value = owsSensor.find(self.xmlns + 'Light').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.LightSensor)
                elif dev.pluginProps['prefSensorValue0068'] == "LED":  # LED
                    input_value = owsSensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0068'] == "Relay":  # Relay
                    input_value = owsSensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0068'] == "T":  # Temperature
                    ows_temp = owsSensor.find(self.xmlns + 'Temperature').text
                    comp_val = dev.pluginProps.get('EDS0068TempComp', '0.0')
                    input_value = float(ows_temp) + float(comp_val)
                    input_value = self.tempConvert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                dev.updateStateOnServer('sensorValue', value=u"Unsupported", uiValue=u"Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            # This code ensures that the device's props are up to date and in line with what they are on the server.
            new_props = dev.pluginProps
            new_props['address']                                       = dev.states['owsRomID']
            new_props['EDS0068barometricHgHighAlarmValue']             = owsSensor.find(self.xmlns + 'BarometricPressureHgHighAlarmValue').text
            new_props['EDS0068barometricHgHighConditionalSearchState'] = owsSensor.find(self.xmlns + 'BarometricPressureHgHighConditionalSearchState').text
            new_props['EDS0068barometricHgLowAlarmValue']              = owsSensor.find(self.xmlns + 'BarometricPressureHgLowAlarmValue').text
            new_props['EDS0068barometricHgLowConditionalSearchState']  = owsSensor.find(self.xmlns + 'BarometricPressureHgLowConditionalSearchState').text
            new_props['EDS0068barometricMbHighAlarmValue']             = owsSensor.find(self.xmlns + 'BarometricPressureMbHighAlarmValue').text
            new_props['EDS0068barometricMbHighConditionalSearchState'] = owsSensor.find(self.xmlns + 'BarometricPressureMbHighConditionalSearchState').text
            new_props['EDS0068barometricMbLowAlarmValue']              = owsSensor.find(self.xmlns + 'BarometricPressureMbLowAlarmValue').text
            new_props['EDS0068barometricMbLowConditionalSearchState']  = owsSensor.find(self.xmlns + 'BarometricPressureMbLowConditionalSearchState').text
            new_props['EDS0068dewpointHighAlarmValue']                 = owsSensor.find(self.xmlns + 'DewPointHighAlarmValue').text
            new_props['EDS0068dewpointHighConditionalSearchState']     = owsSensor.find(self.xmlns + 'DewPointHighConditionalSearchState').text
            new_props['EDS0068dewpointLowAlarmValue']                  = owsSensor.find(self.xmlns + 'DewPointLowAlarmValue').text
            new_props['EDS0068dewpointLowConditionalSearchState']      = owsSensor.find(self.xmlns + 'DewPointLowConditionalSearchState').text
            new_props['EDS0068heatIndexHighAlarmValue']                = owsSensor.find(self.xmlns + 'HeatIndexHighAlarmValue').text
            new_props['EDS0068heatIndexHighConditionalSearchState']    = owsSensor.find(self.xmlns + 'HeatIndexHighConditionalSearchState').text
            new_props['EDS0068heatIndexLowAlarmValue']                 = owsSensor.find(self.xmlns + 'HeatIndexLowAlarmValue').text
            new_props['EDS0068heatIndexLowConditionalSearchState']     = owsSensor.find(self.xmlns + 'HeatIndexLowConditionalSearchState').text
            new_props['EDS0068humidexHighAlarmValue']                  = owsSensor.find(self.xmlns + 'HumidexHighAlarmValue').text
            new_props['EDS0068humidexHighConditionalSearchState']      = owsSensor.find(self.xmlns + 'HumidexHighConditionalSearchState').text
            new_props['EDS0068humidexLowAlarmValue']                   = owsSensor.find(self.xmlns + 'HumidexLowAlarmValue').text
            new_props['EDS0068humidexLowConditionalSearchState']       = owsSensor.find(self.xmlns + 'HumidexLowConditionalSearchState').text
            new_props['EDS0068humidityHighAlarmValue']                 = owsSensor.find(self.xmlns + 'HumidityHighAlarmValue').text
            new_props['EDS0068humidityHighConditionalSearchState']     = owsSensor.find(self.xmlns + 'HumidityHighConditionalSearchState').text
            new_props['EDS0068humidityLowAlarmValue']                  = owsSensor.find(self.xmlns + 'HumidityLowAlarmValue').text
            new_props['EDS0068humidityLowConditionalSearchState']      = owsSensor.find(self.xmlns + 'HumidityLowConditionalSearchState').text
            new_props['EDS0068ledFunction']                            = owsSensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0068lightHighAlarmValue']                    = owsSensor.find(self.xmlns + 'LightHighAlarmValue').text
            new_props['EDS0068lightHighConditionalSearchState']        = owsSensor.find(self.xmlns + 'LightHighConditionalSearchState').text
            new_props['EDS0068lightLowAlarmValue']                     = owsSensor.find(self.xmlns + 'LightLowAlarmValue').text
            new_props['EDS0068lightLowConditionalSearchState']         = owsSensor.find(self.xmlns + 'LightLowConditionalSearchState').text
            new_props['EDS0068relayFunction']                          = owsSensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0068temperatureHighAlarmValue']              = owsSensor.find(self.xmlns + 'TemperatureHighAlarmValue').text
            new_props['EDS0068temperatureHighConditionalSearchState']  = owsSensor.find(self.xmlns + 'TemperatureHighConditionalSearchState').text
            new_props['EDS0068temperatureLowAlarmValue']               = owsSensor.find(self.xmlns + 'TemperatureLowAlarmValue').text
            new_props['EDS0068temperatureLowConditionalSearchState']   = owsSensor.find(self.xmlns + 'TemperatureLowConditionalSearchState').text
            dev.replacePluginPropsOnServer(new_props)

            self.numberOfSensors += 1
            EDS0068_state_dict = {}

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.debugLog(u"Success. Polling next sensor if appropriate.")
            return True

        except Exception:
            self.errorLog(u"Sensor update failure. Check connection.")
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0070(self, dev, owsSensor, server_ip):
        """
        Title Placeholder

        EDS0070 Description = "Vibration Sensor"

        -----

        """
        self.debugLog(u"updateEDS0070() method called.")

        try:
            EDS0070_state_dict = self.stateDict.EDS0070StateDict()

            for key, value in EDS0070_state_dict.iteritems():
                try:
                    dev.updateStateOnServer(key, value=owsSensor.find(self.xmlns + value).text)
                except Exception:
                    self.Fogbert.pluginErrorHandler(traceback.format_exc())
                    self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                    self.debugLog(u"Key: {0} : Value: Unsupported".format(key))
                    dev.updateStateOnServer(key, value=u"Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0070'] == "C_1":  # Counter
                    input_value = owsSensor.find(self.xmlns + 'Counter').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0070'] == "LED":  # LED State
                    input_value = owsSensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0070'] == "Relay":  # Relay State
                    input_value = owsSensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0070'] == "V":  # Vibration
                    input_value = owsSensor.find(self.xmlns + 'VibrationInstant').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                dev.updateStateOnServer('sensorValue', value=u"Unsupported", uiValue=u"Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']                        = dev.states['owsRomID']
            new_props['EDS0070LEDFunction']             = owsSensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0070RelayFunction']           = owsSensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0070VibrationHighAlarmValue'] = owsSensor.find(self.xmlns + 'VibrationHighAlarmValue').text
            new_props['EDS0070VibrationLowAlarmValue']  = owsSensor.find(self.xmlns + 'VibrationLowAlarmValue').text
            dev.replacePluginPropsOnServer(new_props)

            self.numberOfSensors += 1
            EDS0070_state_dict = {}

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.debugLog(u"Success. Polling next sensor if appropriate.")
            return True

        except Exception:
            self.errorLog(u"Sensor update failure. Check connection.")
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0071(self, dev, owsSensor, server_ip):
        """
        Title Placeholder

        EDS0071 Description = "RTD Interface, 4 Wire"

        -----

        """
        self.debugLog(u"updateEDS0071() method called.")

        try:
            EDS0071_state_dict = self.stateDict.EDS0071StateDict()

            for key, value in EDS0071_state_dict.iteritems():
                try:
                    dev.updateStateOnServer(key, value=owsSensor.find(self.xmlns + value).text)
                except Exception:
                    self.Fogbert.pluginErrorHandler(traceback.format_exc())
                    self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                    self.debugLog(u"Key: {0} : Value: Unsupported".format(key))
                    dev.updateStateOnServer(key, value=u"Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0071'] == "C_1":  # Counter
                    input_value = owsSensor.find(self.xmlns + 'Counter').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0071'] == "LED":  # LED State
                    input_value = owsSensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0071'] == "Relay":  # Relay State
                    input_value = owsSensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0071'] == "RTD":  # RTD
                    conversion_value = owsSensor.find(self.xmlns + 'RTDOhms').text
                    input_value = self.voltsConvert(conversion_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0071'] == "T":  # Temperature
                    input_value = owsSensor.find(self.xmlns + 'Temperature').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                dev.updateStateOnServer('sensorValue', value=u"Unsupported", uiValue=u"Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']                            = dev.states['owsRomID']
            new_props['EDS0071CalibrationKey']              = owsSensor.find(self.xmlns + 'CalibrationKey').text
            new_props['EDS0071LEDFunction']                 = owsSensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0071RelayFunction']               = owsSensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0071RTDReadDelay']                = owsSensor.find(self.xmlns + 'RTDReadDelay').text
            new_props['EDS0071RTDResistanceHighAlarmValue'] = owsSensor.find(self.xmlns + 'RTDResistanceHighAlarmValue').text
            new_props['EDS0071RTDResistanceLowAlarmValue']  = owsSensor.find(self.xmlns + 'RTDResistanceLowAlarmValue').text
            new_props['EDS0071TemperatureHighAlarmValue']   = owsSensor.find(self.xmlns + 'TemperatureHighAlarmValue').text
            new_props['EDS0071TemperatureLowAlarmValue']    = owsSensor.find(self.xmlns + 'TemperatureLowAlarmValue').text
            dev.replacePluginPropsOnServer(new_props)

            self.numberOfSensors += 1
            EDS0071_state_dict = {}

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.debugLog(u"Success. Polling next sensor if appropriate.")
            return True

        except Exception:
            self.errorLog(u"Sensor update failure. Check connection.")
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0080(self, dev, owsSensor, server_ip):
        """
        Title Placeholder

        EDS0080 Description = "Octal 4-20 Milliamp Input"

        -----

        """
        self.debugLog(u"updateEDS0080() method called.")

        try:
            EDS0080_state_dict = self.stateDict.EDS0080StateDict()

            for key, value in EDS0080_state_dict.iteritems():
                try:
                    dev.updateStateOnServer(key, value=owsSensor.find(self.xmlns + value).text)
                except Exception:
                    self.Fogbert.pluginErrorHandler(traceback.format_exc())
                    self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                    self.debugLog(u"Key: {0} : Value: Unsupported".format(key))
                    dev.updateStateOnServer(key, value=u"Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0080'] == "I_1":  # Input 1
                    conversion_value = owsSensor.find(self.xmlns + 'v4to20mAInput1Instant').text
                    input_value = self.voltsConvert(conversion_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0080'] == "I_2":  # Input 2
                    conversion_value = owsSensor.find(self.xmlns + 'v4to20mAInput2Instant').text
                    input_value = self.voltsConvert(conversion_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0080'] == "I_3":  # Input 3
                    conversion_value = owsSensor.find(self.xmlns + 'v4to20mAInput3Instant').text
                    input_value = self.voltsConvert(conversion_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0080'] == "I_4":  # Input 4
                    conversion_value = owsSensor.find(self.xmlns + 'v4to20mAInput4Instant').text
                    input_value = self.voltsConvert(conversion_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0080'] == "I_5":  # Input 5
                    conversion_value = owsSensor.find(self.xmlns + 'v4to20mAInput5Instant').text
                    input_value = self.voltsConvert(conversion_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0080'] == "I_6":  # Input 6
                    conversion_value = owsSensor.find(self.xmlns + 'v4to20mAInput6Instant').text
                    input_value = self.voltsConvert(conversion_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0080'] == "I_7":  # Input 7
                    conversion_value = owsSensor.find(self.xmlns + 'v4to20mAInput7Instant').text
                    input_value = self.voltsConvert(conversion_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0080'] == "I_8":  # Input 8
                    conversion_value = owsSensor.find(self.xmlns + 'v4to20mAInput8Instant').text
                    input_value = self.voltsConvert(conversion_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0080'] == "LED":  # LED State
                    input_value = owsSensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0080'] == "Relay":  # Relay State
                    input_value = owsSensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0080'] == "C_1":  # Counter 1
                    conversion_value = owsSensor.find(self.xmlns + 'Counter').text

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                dev.updateStateOnServer('sensorValue', value=u"Unsupported", uiValue=u"Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']                              = dev.states['owsRomID']
            new_props['EDS0080LEDFunction']                  = owsSensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0080RelayFunction']                = owsSensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0080v4to20mAInput1HighAlarmValue'] = owsSensor.find(self.xmlns + 'v4to20mAInput1HighAlarmValue').text
            new_props['EDS0080v4to20mAInput1LowAlarmValue']  = owsSensor.find(self.xmlns + 'v4to20mAInput1LowAlarmValue').text
            new_props['EDS0080v4to20mAInput2HighAlarmValue'] = owsSensor.find(self.xmlns + 'v4to20mAInput2HighAlarmValue').text
            new_props['EDS0080v4to20mAInput2LowAlarmValue']  = owsSensor.find(self.xmlns + 'v4to20mAInput2LowAlarmValue').text
            new_props['EDS0080v4to20mAInput3HighAlarmValue'] = owsSensor.find(self.xmlns + 'v4to20mAInput3HighAlarmValue').text
            new_props['EDS0080v4to20mAInput3LowAlarmValue']  = owsSensor.find(self.xmlns + 'v4to20mAInput3LowAlarmValue').text
            new_props['EDS0080v4to20mAInput4HighAlarmValue'] = owsSensor.find(self.xmlns + 'v4to20mAInput4HighAlarmValue').text
            new_props['EDS0080v4to20mAInput4LowAlarmValue']  = owsSensor.find(self.xmlns + 'v4to20mAInput4LowAlarmValue').text
            new_props['EDS0080v4to20mAInput5HighAlarmValue'] = owsSensor.find(self.xmlns + 'v4to20mAInput5HighAlarmValue').text
            new_props['EDS0080v4to20mAInput5LowAlarmValue']  = owsSensor.find(self.xmlns + 'v4to20mAInput5LowAlarmValue').text
            new_props['EDS0080v4to20mAInput6HighAlarmValue'] = owsSensor.find(self.xmlns + 'v4to20mAInput6HighAlarmValue').text
            new_props['EDS0080v4to20mAInput6LowAlarmValue']  = owsSensor.find(self.xmlns + 'v4to20mAInput6LowAlarmValue').text
            new_props['EDS0080v4to20mAInput7HighAlarmValue'] = owsSensor.find(self.xmlns + 'v4to20mAInput7HighAlarmValue').text
            new_props['EDS0080v4to20mAInput7LowAlarmValue']  = owsSensor.find(self.xmlns + 'v4to20mAInput7LowAlarmValue').text
            new_props['EDS0080v4to20mAInput8HighAlarmValue'] = owsSensor.find(self.xmlns + 'v4to20mAInput8HighAlarmValue').text
            new_props['EDS0080v4to20mAInput8LowAlarmValue']  = owsSensor.find(self.xmlns + 'v4to20mAInput8LowAlarmValue').text
            dev.replacePluginPropsOnServer(new_props)

            self.numberOfSensors += 1
            EDS0080_state_dict = {}

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.debugLog(u"Success. Polling next sensor if appropriate.")
            return True

        except Exception:
            self.errorLog(u"Sensor update failure. Check connection.")
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0082(self, dev, owsSensor, server_ip):
        """
        Title Placeholder

        EDS0082 Description = "Octal Current Input Device"

        -----

        """
        self.debugLog(u"updateEDS0082() method called.")

        try:
            EDS0082_state_dict = self.stateDict.EDS0082StateDict()

            for key, value in EDS0082_state_dict.iteritems():
                try:
                    dev.updateStateOnServer(key, value=owsSensor.find(self.xmlns + value).text)
                except Exception:
                    self.Fogbert.pluginErrorHandler(traceback.format_exc())
                    self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                    self.debugLog(u"Key: {0} : Value: Unsupported".format(key))
                    dev.updateStateOnServer(key, value=u"Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0082'] == "I_1":  # Input 1 Instant
                    input_value = owsSensor.find(self.xmlns + 'v0to10VoltInput1Instant').text
                    input_value = self.voltsConvert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0082'] == "I_2":  # Input 2 Instant
                    input_value = owsSensor.find(self.xmlns + 'v0to10VoltInput2Instant').text
                    input_value = self.voltsConvert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0082'] == "I_3":  # Input 3 Instant
                    input_value = owsSensor.find(self.xmlns + 'v0to10VoltInput3Instant').text
                    input_value = self.voltsConvert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0082'] == "I_4":  # Input 4 Instant
                    input_value = owsSensor.find(self.xmlns + 'v0to10VoltInput4Instant').text
                    input_value = self.voltsConvert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0082'] == "I_5":  # Input 5 Instant
                    input_value = owsSensor.find(self.xmlns + 'v0to10VoltInput5Instant').text
                    input_value = self.voltsConvert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0082'] == "I_6":  # Input 6 Instant
                    input_value = owsSensor.find(self.xmlns + 'v0to10VoltInput6Instant').text
                    input_value = self.voltsConvert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0082'] == "I_7":  # Input 7 Instant
                    input_value = owsSensor.find(self.xmlns + 'v0to10VoltInput7Instant').text
                    input_value = self.voltsConvert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0082'] == "I_8":  # Input 8 Instant
                    input_value = owsSensor.find(self.xmlns + 'v0to10VoltInput8Instant').text
                    input_value = self.voltsConvert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0082'] == "LED":  # LED State
                    input_value = owsSensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0082'] == "Relay":  # Relay State
                    input_value = owsSensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                dev.updateStateOnServer('sensorValue', value=u"Unsupported", uiValue=u"Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']                               = dev.states['owsRomID']
            new_props['EDS0082LEDFunction']                    = owsSensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0082RelayFunction']                  = owsSensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0082v0to10VoltInput1HighAlarmValue'] = owsSensor.find(self.xmlns + 'v0to10VoltInput1HighAlarmValue').text
            new_props['EDS0082v0to10VoltInput1LowAlarmValue']  = owsSensor.find(self.xmlns + 'v0to10VoltInput1LowAlarmValue').text
            new_props['EDS0082v0to10VoltInput2HighAlarmValue'] = owsSensor.find(self.xmlns + 'v0to10VoltInput2HighAlarmValue').text
            new_props['EDS0082v0to10VoltInput2LowAlarmValue']  = owsSensor.find(self.xmlns + 'v0to10VoltInput2LowAlarmValue').text
            new_props['EDS0082v0to10VoltInput3HighAlarmValue'] = owsSensor.find(self.xmlns + 'v0to10VoltInput3HighAlarmValue').text
            new_props['EDS0082v0to10VoltInput3LowAlarmValue']  = owsSensor.find(self.xmlns + 'v0to10VoltInput3LowAlarmValue').text
            new_props['EDS0082v0to10VoltInput4HighAlarmValue'] = owsSensor.find(self.xmlns + 'v0to10VoltInput4HighAlarmValue').text
            new_props['EDS0082v0to10VoltInput4LowAlarmValue']  = owsSensor.find(self.xmlns + 'v0to10VoltInput4LowAlarmValue').text
            new_props['EDS0082v0to10VoltInput5HighAlarmValue'] = owsSensor.find(self.xmlns + 'v0to10VoltInput5HighAlarmValue').text
            new_props['EDS0082v0to10VoltInput5LowAlarmValue']  = owsSensor.find(self.xmlns + 'v0to10VoltInput5LowAlarmValue').text
            new_props['EDS0082v0to10VoltInput6HighAlarmValue'] = owsSensor.find(self.xmlns + 'v0to10VoltInput6HighAlarmValue').text
            new_props['EDS0082v0to10VoltInput6LowAlarmValue']  = owsSensor.find(self.xmlns + 'v0to10VoltInput6LowAlarmValue').text
            new_props['EDS0082v0to10VoltInput7HighAlarmValue'] = owsSensor.find(self.xmlns + 'v0to10VoltInput7HighAlarmValue').text
            new_props['EDS0082v0to10VoltInput7LowAlarmValue']  = owsSensor.find(self.xmlns + 'v0to10VoltInput7LowAlarmValue').text
            new_props['EDS0082v0to10VoltInput8HighAlarmValue'] = owsSensor.find(self.xmlns + 'v0to10VoltInput8HighAlarmValue').text
            new_props['EDS0082v0to10VoltInput8LowAlarmValue']  = owsSensor.find(self.xmlns + 'v0to10VoltInput8LowAlarmValue').text
            dev.replacePluginPropsOnServer(new_props)

            self.numberOfSensors += 1
            EDS0082_state_dict = {}

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.debugLog(u"Success. Polling next sensor if appropriate.")
            return True

        except Exception:
            self.errorLog(u"Sensor update failure. Check connection.")
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0083(self, dev, owsSensor, server_ip):
        """
        Title Placeholder

        EDS0083 Description = "Octal Current Input Device"

        -----

        """
        self.debugLog(u"updateEDS0083() method called.")

        try:
            EDS0083_state_dict = self.stateDict.EDS0083StateDict()

            for key, value in EDS0083_state_dict.iteritems():
                try:
                    dev.updateStateOnServer(key, value=owsSensor.find(self.xmlns + value).text)
                except Exception:
                    self.Fogbert.pluginErrorHandler(traceback.format_exc())
                    self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                    self.debugLog(u"Key: {0} : Value: Unsupported".format(key))
                    dev.updateStateOnServer(key, value=u"Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0083'] == "I_1":  # Input 1 Instant
                    input_value = owsSensor.find(self.xmlns + 'v4to20mAInput1Instant').text
                    input_value = self.voltsConvert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0083'] == "I_2":  # Input 2 Instant
                    input_value = owsSensor.find(self.xmlns + 'v4to20mAInput2Instant').text
                    input_value = self.voltsConvert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0083'] == "I_3":  # Input 3 Instant
                    input_value = owsSensor.find(self.xmlns + 'v4to20mAInput3Instant').text
                    input_value = self.voltsConvert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0083'] == "I_4":  # Input 4 Instant
                    input_value = owsSensor.find(self.xmlns + 'v4to20mAInput4Instant').text
                    input_value = self.voltsConvert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0083'] == "LED":  # LED State
                    input_value = owsSensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0083'] == "Relay":  # Relay State
                    input_value = owsSensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                dev.updateStateOnServer('sensorValue', value=u"Unsupported", uiValue=u"Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']                             = dev.states['owsRomID']
            new_props['EDS0083LEDFunction']                  = owsSensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0083RelayFunction']                = owsSensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0083v4to20mAInput1HighAlarmValue'] = owsSensor.find(self.xmlns + 'v4to20mAInput1HighAlarmValue').text
            new_props['EDS0083v4to20mAInput1LowAlarmValue']  = owsSensor.find(self.xmlns + 'v4to20mAInput1LowAlarmValue').text
            new_props['EDS0083v4to20mAInput2HighAlarmValue'] = owsSensor.find(self.xmlns + 'v4to20mAInput2HighAlarmValue').text
            new_props['EDS0083v4to20mAInput2LowAlarmValue']  = owsSensor.find(self.xmlns + 'v4to20mAInput2LowAlarmValue').text
            new_props['EDS0083v4to20mAInput3HighAlarmValue'] = owsSensor.find(self.xmlns + 'v4to20mAInput3HighAlarmValue').text
            new_props['EDS0083v4to20mAInput3LowAlarmValue']  = owsSensor.find(self.xmlns + 'v4to20mAInput3LowAlarmValue').text
            new_props['EDS0083v4to20mAInput4HighAlarmValue'] = owsSensor.find(self.xmlns + 'v4to20mAInput4HighAlarmValue').text
            new_props['EDS0083v4to20mAInput4LowAlarmValue']  = owsSensor.find(self.xmlns + 'v4to20mAInput4LowAlarmValue').text
            dev.replacePluginPropsOnServer(new_props)

            self.numberOfSensors += 1
            EDS0083_state_dict = {}

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.debugLog(u"Success. Polling next sensor if appropriate.")
            return True

        except Exception:
            self.errorLog(u"Sensor update failure. Check connection.")
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    #  =============================================================================
    def updateEDS0085(self, dev, owsSensor, server_ip):
        """
        Title Placeholder

        EDS0085 Description = "Octal Current Input Device"

        -----

        """
        self.debugLog(u"updateEDS0085() method called.")

        try:
            EDS0085_state_dict = self.stateDict.EDS0085StateDict()

            for key, value in EDS0085_state_dict.iteritems():
                try:
                    dev.updateStateOnServer(key, value=owsSensor.find(self.xmlns + value).text)
                except Exception:
                    self.Fogbert.pluginErrorHandler(traceback.format_exc())
                    self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                    self.debugLog(u"Key: {0} : Value: Unsupported".format(key))
                    dev.updateStateOnServer(key, value=u"Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0085'] == "I_1":  # Input 1 Instant
                    input_value = owsSensor.find(self.xmlns + 'v0to10VoltInput1Instant').text
                    input_value = self.voltsConvert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0085'] == "I_2":  # Input 2 Instant
                    input_value = owsSensor.find(self.xmlns + 'v0to10VoltInput2Instant').text
                    input_value = self.voltsConvert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0085'] == "I_3":  # Input 3 Instant
                    input_value = owsSensor.find(self.xmlns + 'v0to10VoltInput3Instant').text
                    input_value = self.voltsConvert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0085'] == "I_4":  # Input 4 Instant
                    input_value = owsSensor.find(self.xmlns + 'v0to10VoltInput4Instant').text
                    input_value = self.voltsConvert(input_value)
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0085'] == "LED":  # LED State
                    input_value = owsSensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0085'] == "Relay":  # Relay State
                    input_value = owsSensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                dev.updateStateOnServer('sensorValue', value=u"Unsupported", uiValue=u"Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address']                               = dev.states['owsRomID']
            new_props['EDS0085LEDFunction']                    = owsSensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0085RelayFunction']                  = owsSensor.find(self.xmlns + 'RelayFunction').text
            new_props['EDS0085v0to10VoltInput1HighAlarmValue'] = owsSensor.find(self.xmlns + 'v0to10VoltInput1HighAlarmValue').text
            new_props['EDS0085v0to10VoltInput1LowAlarmValue']  = owsSensor.find(self.xmlns + 'v0to10VoltInput1LowAlarmValue').text
            new_props['EDS0085v0to10VoltInput2HighAlarmValue'] = owsSensor.find(self.xmlns + 'v0to10VoltInput2HighAlarmValue').text
            new_props['EDS0085v0to10VoltInput2LowAlarmValue']  = owsSensor.find(self.xmlns + 'v0to10VoltInput2LowAlarmValue').text
            new_props['EDS0085v0to10VoltInput3HighAlarmValue'] = owsSensor.find(self.xmlns + 'v0to10VoltInput3HighAlarmValue').text
            new_props['EDS0085v0to10VoltInput3LowAlarmValue']  = owsSensor.find(self.xmlns + 'v0to10VoltInput3LowAlarmValue').text
            new_props['EDS0085v0to10VoltInput4HighAlarmValue'] = owsSensor.find(self.xmlns + 'v0to10VoltInput4HighAlarmValue').text
            new_props['EDS0085v0to10VoltInput4LowAlarmValue']  = owsSensor.find(self.xmlns + 'v0to10VoltInput4LowAlarmValue').text
            dev.replacePluginPropsOnServer(new_props)

            self.numberOfSensors += 1
            EDS0085_state_dict = {}

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.debugLog(u"Success. Polling next sensor if appropriate.")
            return True

        except Exception:
            self.errorLog(u"Sensor update failure. Check connection.")
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    # =============================================================================
    def updateEDS0090(self, dev, owsSensor, server_ip):
        """
        Title Placeholder

        EDS0090 Description = "Octal Discrete IO"

        -----

        """
        self.debugLog(u"updateEDS0090() method called.")

        try:
            EDS0090_state_dict = self.stateDict.EDS0090StateDict()

            for key, value in EDS0090_state_dict.iteritems():
                try:
                    dev.updateStateOnServer(key, value=owsSensor.find(self.xmlns + value).text)
                except Exception:
                    self.Fogbert.pluginErrorHandler(traceback.format_exc())
                    self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                    self.debugLog(u"Key: {0} : Value: Unsupported".format(key))
                    dev.updateStateOnServer(key, value=u"Unsupported")

            # The user can select which of the following values become the main sensorValue.
            try:
                if dev.pluginProps['prefSensorValue0090'] == "C_1":  # Counter 1
                    input_value = owsSensor.find(self.xmlns + 'Counter').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0090'] == "I_1":  # Input 1 State
                    input_value = owsSensor.find(self.xmlns + 'DiscreteIO1InputState').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0090'] == "I_2":  # Input 2 State
                    input_value = owsSensor.find(self.xmlns + 'DiscreteIO2InputState').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0090'] == "I_3":  # Input 3 State
                    input_value = owsSensor.find(self.xmlns + 'DiscreteIO3InputState').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0090'] == "I_4":  # Input 4 State
                    input_value = owsSensor.find(self.xmlns + 'DiscreteIO4InputState').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0090'] == "I_5":  # Input 5 State
                    input_value = owsSensor.find(self.xmlns + 'DiscreteIO5InputState').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0090'] == "I_6":  # Input 6 State
                    input_value = owsSensor.find(self.xmlns + 'DiscreteIO6InputState').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0090'] == "I_7":  # Input 7 State
                    input_value = owsSensor.find(self.xmlns + 'DiscreteIO7InputState').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0090'] == "I_8":  # Input 8 State
                    input_value = owsSensor.find(self.xmlns + 'DiscreteIO8InputState').text
                    dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0090'] == "LED":  # LED State
                    input_value = owsSensor.find(self.xmlns + 'LED').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
                elif dev.pluginProps['prefSensorValue0090'] == "Relay":  # Relay State
                    input_value = owsSensor.find(self.xmlns + 'Relay').text
                    if input_value == "1":
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
                    else:
                        dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

                dev.updateStateOnServer('sensorValue', value=input_value, uiValue=input_value)

            except Exception:
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.debugLog(u"Unable to update device state on server. Device: {0}".format(dev.name))
                dev.updateStateOnServer('sensorValue', value=u"Unsupported", uiValue=u"Unsupported")
                dev.updateStateImageOnServer(indigo.kStateImageSel.Error)

            new_props = dev.pluginProps
            new_props['address'] = dev.states['owsRomID']
            new_props['EDS0090DiscreteIO1ActivityLatchReset'] = owsSensor.find(self.xmlns + 'DiscreteIO1ActivityLatchReset').text
            new_props['EDS0090DiscreteIO1HighAlarmValue']     = owsSensor.find(self.xmlns + 'DiscreteIO1HighAlarmValue').text
            new_props['EDS0090DiscreteIO1LowAlarmValue']      = owsSensor.find(self.xmlns + 'DiscreteIO1LowAlarmValue').text
            new_props['EDS0090DiscreteIO1OutputState']        = owsSensor.find(self.xmlns + 'DiscreteIO1OutputState').text
            new_props['EDS0090DiscreteIO1PulldownState']      = owsSensor.find(self.xmlns + 'DiscreteIO1PulldownState').text
            new_props['EDS0090DiscreteIO1PulseCounterReset']  = owsSensor.find(self.xmlns + 'DiscreteIO1PulseCounterReset').text
            new_props['EDS0090DiscreteIO2ActivityLatchReset'] = owsSensor.find(self.xmlns + 'DiscreteIO2ActivityLatchReset').text
            new_props['EDS0090DiscreteIO2HighAlarmValue']     = owsSensor.find(self.xmlns + 'DiscreteIO2HighAlarmValue').text
            new_props['EDS0090DiscreteIO2LowAlarmValue']      = owsSensor.find(self.xmlns + 'DiscreteIO2LowAlarmValue').text
            new_props['EDS0090DiscreteIO2OutputState']        = owsSensor.find(self.xmlns + 'DiscreteIO2OutputState').text
            new_props['EDS0090DiscreteIO2PulldownState']      = owsSensor.find(self.xmlns + 'DiscreteIO2PulldownState').text
            new_props['EDS0090DiscreteIO2PulseCounterReset']  = owsSensor.find(self.xmlns + 'DiscreteIO2PulseCounterReset').text
            new_props['EDS0090DiscreteIO3ActivityLatchReset'] = owsSensor.find(self.xmlns + 'DiscreteIO3ActivityLatchReset').text
            new_props['EDS0090DiscreteIO3HighAlarmValue']     = owsSensor.find(self.xmlns + 'DiscreteIO3HighAlarmValue').text
            new_props['EDS0090DiscreteIO3LowAlarmValue']      = owsSensor.find(self.xmlns + 'DiscreteIO3LowAlarmValue').text
            new_props['EDS0090DiscreteIO3OutputState']        = owsSensor.find(self.xmlns + 'DiscreteIO3OutputState').text
            new_props['EDS0090DiscreteIO3PulldownState']      = owsSensor.find(self.xmlns + 'DiscreteIO3PulldownState').text
            new_props['EDS0090DiscreteIO4ActivityLatchReset'] = owsSensor.find(self.xmlns + 'DiscreteIO4ActivityLatchReset').text
            new_props['EDS0090DiscreteIO4HighAlarmValue']     = owsSensor.find(self.xmlns + 'DiscreteIO4HighAlarmValue').text
            new_props['EDS0090DiscreteIO4LowAlarmValue']      = owsSensor.find(self.xmlns + 'DiscreteIO4LowAlarmValue').text
            new_props['EDS0090DiscreteIO4OutputState']        = owsSensor.find(self.xmlns + 'DiscreteIO4OutputState').text
            new_props['EDS0090DiscreteIO4PulldownState']      = owsSensor.find(self.xmlns + 'DiscreteIO4PulldownState').text
            new_props['EDS0090DiscreteIO5ActivityLatchReset'] = owsSensor.find(self.xmlns + 'DiscreteIO5ActivityLatchReset').text
            new_props['EDS0090DiscreteIO5HighAlarmValue']     = owsSensor.find(self.xmlns + 'DiscreteIO5HighAlarmValue').text
            new_props['EDS0090DiscreteIO5LowAlarmValue']      = owsSensor.find(self.xmlns + 'DiscreteIO5LowAlarmValue').text
            new_props['EDS0090DiscreteIO5OutputState']        = owsSensor.find(self.xmlns + 'DiscreteIO5OutputState').text
            new_props['EDS0090DiscreteIO5PulldownState']      = owsSensor.find(self.xmlns + 'DiscreteIO5PulldownState').text
            new_props['EDS0090DiscreteIO6ActivityLatchReset'] = owsSensor.find(self.xmlns + 'DiscreteIO6ActivityLatchReset').text
            new_props['EDS0090DiscreteIO6HighAlarmValue']     = owsSensor.find(self.xmlns + 'DiscreteIO6HighAlarmValue').text
            new_props['EDS0090DiscreteIO6LowAlarmValue']      = owsSensor.find(self.xmlns + 'DiscreteIO6LowAlarmValue').text
            new_props['EDS0090DiscreteIO6OutputState']        = owsSensor.find(self.xmlns + 'DiscreteIO6OutputState').text
            new_props['EDS0090DiscreteIO6PulldownState']      = owsSensor.find(self.xmlns + 'DiscreteIO6PulldownState').text
            new_props['EDS0090DiscreteIO7ActivityLatchReset'] = owsSensor.find(self.xmlns + 'DiscreteIO7ActivityLatchReset').text
            new_props['EDS0090DiscreteIO7HighAlarmValue']     = owsSensor.find(self.xmlns + 'DiscreteIO7HighAlarmValue').text
            new_props['EDS0090DiscreteIO7LowAlarmValue']      = owsSensor.find(self.xmlns + 'DiscreteIO7LowAlarmValue').text
            new_props['EDS0090DiscreteIO7OutputState']        = owsSensor.find(self.xmlns + 'DiscreteIO7OutputState').text
            new_props['EDS0090DiscreteIO7PulldownState']      = owsSensor.find(self.xmlns + 'DiscreteIO7PulldownState').text
            new_props['EDS0090DiscreteIO8ActivityLatchReset'] = owsSensor.find(self.xmlns + 'DiscreteIO8ActivityLatchReset').text
            new_props['EDS0090DiscreteIO8HighAlarmValue']     = owsSensor.find(self.xmlns + 'DiscreteIO8HighAlarmValue').text
            new_props['EDS0090DiscreteIO8LowAlarmValue']      = owsSensor.find(self.xmlns + 'DiscreteIO8LowAlarmValue').text
            new_props['EDS0090DiscreteIO8OutputState']        = owsSensor.find(self.xmlns + 'DiscreteIO8OutputState').text
            new_props['EDS0090DiscreteIO8PulldownState']      = owsSensor.find(self.xmlns + 'DiscreteIO8PulldownState').text
            new_props['EDS0090LEDFunction']                   = owsSensor.find(self.xmlns + 'LEDFunction').text
            new_props['EDS0090RelayFunction']                 = owsSensor.find(self.xmlns + 'RelayFunction').text
            dev.replacePluginPropsOnServer(new_props)

            self.numberOfSensors += 1
            EDS0090_state_dict = {}

            dev.updateStateOnServer('onOffState', value=True, uiValue=" ")
            self.debugLog(u"Success. Polling next sensor if appropriate.")
            return True

        except Exception:
            self.errorLog(u"Sensor update failure. Check connection.")
            self.Fogbert.pluginErrorHandler(traceback.format_exc())
            dev.updateStateOnServer('onOffState', value=False, uiValue=" ")
            dev.updateStateImageOnServer(indigo.kStateImageSel.Error)
            return False

    # =============================================================================
    # =========== Server and Sensor Device Config Dialog Button Methods ===========    
    # =============================================================================
    # While we are always sending a "0" as the setting value, this may not always
    # be the case. So we keep them separate for this reason.
    def clearAlarms(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """

        parm_list = (valuesDict['serverList'], valuesDict['romID'], "clearAlarms", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearBarometricPressureHgHighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "BarometricPressureHgHighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearBarometricPressureHgLowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "BarometricPressureHgLowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearBarometricPressureMbHighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "BarometricPressureMbHighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearBarometricPressureMbLowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "BarometricPressureMbLowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearDewpointHighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "DewpointHighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearDewpointLowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "DewpointLowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearDiscreteIO1HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "DiscreteIO1HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearDiscreteIO1LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "DiscreteIO1LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearDiscreteIO2HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "DiscreteIO2HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearDiscreteIO2LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "DiscreteIO2LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearDiscreteIO3HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "DiscreteIO3HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearDiscreteIO3LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "DiscreteIO3LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearDiscreteIO4HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "DiscreteIO4HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearDiscreteIO4LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "DiscreteIO4LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearDiscreteIO5HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "DiscreteIO5HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearDiscreteIO5LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "DiscreteIO5LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearDiscreteIO6HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "DiscreteIO6HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearDiscreteIO6LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "DiscreteIO6LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearDiscreteIO7HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "DiscreteIO7HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearDiscreteIO7LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "DiscreteIO7LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearDiscreteIO8HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "DiscreteIO8HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearDiscreteIO8LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "DiscreteIO8LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearHeatIndexHighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "HeatIndexHighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearHeatIndexLowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "HeatIndexLowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearHumidexHighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "HumidexHighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearHumidexLowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "HumidexLowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearHumidityHighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "HumidityHighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearHumidityLowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "HumidityLowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0Input1HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v0to10VoltInput1HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0Input1LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v0to10VoltInput1LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0Input2HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v0to10VoltInput2HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0Input2LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v0to10VoltInput2LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0Input3HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v0to10VoltInput3HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0Input3LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v0to10VoltInput3LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0Input4HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v0to10VoltInput4HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0Input4LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v0to10VoltInput4LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0Input5HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v0to10VoltInput5HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0Input5LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v0to10VoltInput5LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0Input6HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v0to10VoltInput6HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0Input6LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v0to10VoltInput6LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0Input7HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v0to10VoltInput7HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0Input7LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v0to10VoltInput7LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0Input8HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v0to10VoltInput8HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v0Input8LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v0to10VoltInput8LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4Input1HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v4to20mAInput1HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4Input1LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v4to20mAInput1LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4Input2HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v4to20mAInput2HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4Input2LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v4to20mAInput2LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4Input3HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v4to20mAInput3HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4Input3LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v4to20mAInput3LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4Input4HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v4to20mAInput4HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4Input4LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v4to20mAInput4LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4Input5HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v4to20mAInput5HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4Input5LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v4to20mAInput5LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4Input6HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v4to20mAInput6HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4Input6LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v4to20mAInput6LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4Input7HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v4to20mAInput7HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4Input7LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v4to20mAInput7LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4Input8HighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v4to20mAInput8HighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clear_v4Input8LowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "v4to20mAInput8LowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearLightHighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "LightHighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearLightLowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "LightLowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearRTDResistanceHighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "RTDResistanceHighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearRTDResistanceLowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "RTDResistanceLowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearRTDFaultConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "RTDFaultConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearTemperatureHighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "TemperatureHighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearTemperatureLowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "TemperatureLowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearVibrationHighConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "VibrationHighConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def clearVibrationLowConditionalSearchState(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        Docstring Placeholder

        -----

        :return:
        """
        parm_list = (valuesDict['serverList'], valuesDict['romID'], "VibrationLowConditionalSearchState", "0")
        self.sendToServer(parm_list)

    # =============================================================================
    def toggleLED(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        The toggleLED() method is used to toggle the LED of the calling device.

        -----

        """
        new_var = ""
        try:
            if indigo.devices[targetId].states['owsLED'] == "1":
                new_var = "0"
            elif indigo.devices[targetId].states['owsLED'] == "0":
                new_var = "1"
            else:
                self.errorLog(u"Error toggling sensor LED.")
        except Exception:
            self.Fogbert.pluginErrorHandler(traceback.format_exc())

        parm_list = (valuesDict['serverList'], valuesDict['romID'], "LEDState", new_var)
        self.sendToServer(parm_list)

    # =============================================================================
    def toggleRelay(self, valuesDict, typeId, targetId, filter="indigo.sensor"):
        """
        Title Placeholder

        The toggleRelay() method is used to toggle the relay of the calling device.

        -----

        """
        new_var = ""
        try:
            if indigo.devices[targetId].states['owsRelay'] == "1":
                new_var = "0"
            elif indigo.devices[targetId].states['owsRelay'] == "0":
                new_var = "1"
            else:
                self.errorLog(u"Error toggling sensor relay.")
        except Exception:
            self.Fogbert.pluginErrorHandler(traceback.format_exc())

        parm_list = (valuesDict['serverList'], valuesDict['romID'], "RelayState", new_var)
        self.sendToServer(parm_list)

    # =============================================================================
    def updateDeviceStatesAction(self, valuesDict):
        """
        Title Placeholder

        The updateDeviceStatesAction() method is used to invoke the
        updateDeviceStates() method when it is called for from an Action item.

        -----

        """
        self.updateDeviceStates()
        return

    # =============================================================================
    def updateDeviceStates(self):
        """
        Title Placeholder

        The updateDeviceStates() method initiates an update for each
        established Indigo device.

        -----


    """
        self.debugLog(u"updateDeviceStates() method called.")

        addr = self.pluginPrefs['OWServerIP']
        split_ip = addr.replace(" ", "").split(",")
        self.numberOfSensors = 0
        self.numberOfServers = 0
        pref_poll = int(self.pluginPrefs.get('configMenuPollInterval', 900))

        if not self.pluginPrefs.get('suppressResultsLogging', False):
            indigo.server.log(u"Getting OWServer data...")

        for server_ip in split_ip:

            try:
                # Grab details.xml
                self.debugLog(u"Getting details.xml for server {0}".format(server_ip))
                ows_xml = self.getDetailsXML(server_ip)
                root = eTree.fromstring(ows_xml)

                for dev in indigo.devices.itervalues("self"):
                    if not dev:
                        # There are no devices of type OWServer, so go to sleep.
                        self.debugLog(u"There aren't any servers or sensors to assign yet. Sleeping.")
                        self.sleep(pref_poll)

                    elif not dev.configured:
                        # A device has been created, but hasn't been fully configured.
                        self.errorLog(
                            u"A device has been created, but is not fully "
                            "configured. Sleeping while you finish.")
                        self.sleep(pref_poll)

                    elif not dev.enabled:
                        # A device has been disabled. Skip it.
                        self.debugLog(u"{0} is disabled. Skipping.".format(dev.name))
                        pass

                    elif dev.enabled:
                        self.debugLog(u"Parsing information for device: {0}".format(dev.name))

                        try:
                            if dev.deviceTypeId == "owsOWSServer" and dev.pluginProps['serverList'] == server_ip:
                                self.updateOWServer(dev, root, server_ip)

                            elif dev.deviceTypeId == 'owsTemperatureSensor':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_DS18B20'):
                                    self.debugLog(u"Parsing DS18B20 devices.")
                                    if dev.pluginProps['romID'] == owsSensor.find(self.xmlns + 'ROMId').text and dev.pluginProps['serverList'] == server_ip:
                                        self.updateDS18B20(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsTemperatureSensor_S':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_DS18S20'):
                                    self.debugLog(u"Parsing DS18S20 devices.")
                                    if dev.pluginProps['romID'] == owsSensor.find(self.xmlns + 'ROMId').text and dev.pluginProps['serverList'] == server_ip:
                                        self.updateDS18S20(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsDualSwitchPlusMemory':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_DS2406'):
                                    self.debugLog(u"Parsing DS2406 devices.")
                                    if dev.pluginProps['romID'] == owsSensor.find(self.xmlns + 'ROMId').text and dev.pluginProps['serverList'] == server_ip:
                                        self.updateDS2406(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsUserSwitch':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_DS2408'):
                                    self.debugLog(u"Parsing DS2408 devices.")
                                    if dev.pluginProps['romID'] == owsSensor.find(self.xmlns + 'ROMId').text and dev.pluginProps['serverList'] == server_ip:
                                        self.updateDS2408(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsCounterDevice':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_DS2423'):
                                    self.debugLog(u"Parsing DS2423 devices.")
                                    if dev.pluginProps['romID'] == owsSensor.find(self.xmlns + 'ROMId').text and dev.pluginProps['serverList'] == server_ip:
                                        self.updateDS2423(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsSmartBatteryMonitor':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_DS2438'):
                                    self.debugLog(u"Parsing DS2438 devices.")
                                    if dev.pluginProps['romID'] == owsSensor.find(self.xmlns + 'ROMId').text and dev.pluginProps['serverList'] == server_ip:
                                        self.updateDS2438(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsQuadConverter':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_DS2450'):
                                    self.debugLog(u"Parsing DS2450 devices.")
                                    if dev.pluginProps['romID'] == owsSensor.find(self.xmlns + 'ROMId').text and dev.pluginProps['serverList'] == server_ip:
                                        self.updateDS2450(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsTemperatureSensor64':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0064'):
                                    self.debugLog(u"Parsing EDS0064 devices.")
                                    if dev.pluginProps['romID'] == owsSensor.find(self.xmlns + 'ROMId').text and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0064(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsTemperatureHumiditySensor65':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0065'):
                                    self.debugLog(u"Parsing EDS0065 devices.")
                                    if dev.pluginProps['romID'] == owsSensor.find(self.xmlns + 'ROMId').text and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0065(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsTemperaturePressureSensor66':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0066'):
                                    self.debugLog(u"Parsing EDS0066 devices.")
                                    if dev.pluginProps['romID'] == owsSensor.find(self.xmlns + 'ROMId').text and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0066(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsTemperatureLight':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0067'):
                                    self.debugLog(u"Parsing EDS0067 devices.")
                                    if dev.pluginProps['romID'] == owsSensor.find(self.xmlns + 'ROMId').text and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0067(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsTemperatureHumidityBarometricPressureLight':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0068'):
                                    self.debugLog(u"Parsing EDS0068 devices.")
                                    if dev.pluginProps['romID'] == owsSensor.find(self.xmlns + 'ROMId').text and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0068(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsVibrationSensor':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0070'):
                                    self.debugLog(u"Parsing EDS0070 devices.")
                                    if dev.pluginProps['romID'] == owsSensor.find(self.xmlns + 'ROMId').text and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0070(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsRTDinterfaceFourWire71':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0071'):
                                    self.debugLog(u"Parsing EDS0071 devices.")
                                    if dev.pluginProps['romID'] == owsSensor.find(self.xmlns + 'ROMId').text and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0071(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsOctalMilliampInput80':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0080'):
                                    self.debugLog(u"Parsing EDS0080 devices.")
                                    if dev.pluginProps['romID'] == owsSensor.find(self.xmlns + 'ROMId').text and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0080(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsOctalCurrentDevice':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0082'):
                                    self.debugLog(u"Parsing EDS0082 devices.")
                                    if dev.pluginProps['romID'] == owsSensor.find(self.xmlns + 'ROMId').text and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0082(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsOctalCurrentDevice83':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0083'):
                                    self.debugLog(u"Parsing EDS0083 devices.")
                                    if dev.pluginProps['romID'] == owsSensor.find(self.xmlns + 'ROMId').text and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0083(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsQuadCurrentDevice':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0085'):
                                    self.debugLog(u"Parsing EDS0085 devices.")
                                    if dev.pluginProps['romID'] == owsSensor.find(self.xmlns + 'ROMId').text and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0085(dev, owsSensor, server_ip)

                            elif dev.deviceTypeId == 'owsOctalDiscreteIO90':
                                for owsSensor in root.findall('./' + self.xmlns + 'owd_EDS0090'):
                                    self.debugLog(u"Parsing EDS0090 devices.")
                                    if dev.pluginProps['romID'] == owsSensor.find(self.xmlns + 'ROMId').text and dev.pluginProps['serverList'] == server_ip:
                                        self.updateEDS0090(dev, owsSensor, server_ip)

                            else:
                                pass

                        except Exception:
                            self.errorLog(u"Error in server parsing routine.")
                            self.Fogbert.pluginErrorHandler(traceback.format_exc())
                            pass

            except Exception:
                # There has been a problem reaching the server. "Turn off" all sensors until next successful poll.
                [dev.updateStateOnServer('onOffState', value=False) for dev in indigo.devices.itervalues("self")]
                self.Fogbert.pluginErrorHandler(traceback.format_exc())
                self.errorLog(u"Error parsing sensor states.")
                self.errorLog(u"Trying again in {0} seconds.".format(pref_poll))

        self.debugLog(u"  No more sensors to poll.")

        if not self.pluginPrefs.get("suppressResultsLogging", False):
            indigo.server.log(u"  Total of {0} servers polled.".format(self.numberOfServers))
            indigo.server.log(u"  Total of {0} devices updated.".format(self.numberOfSensors))
            indigo.server.log(u"OWServer data parsed successfully.")

        ows_xml = ''  # Empty the variable to conserve memory resources.
        return
