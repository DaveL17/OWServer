# pylint: disable=too-many-lines, line-too-long, invalid-name

"""
filename: stateDict.py
author: DaveL17

stateDict.py is a module designed to support the OWServer plugin for Indigo Home Control Server.
The module contains a series of dictionaries that contain {'Indigo Device States': 'details.xml
key'}. These dictionaries are returned to the host plugin for iteration and device state value
assignment.
"""

try:
    import indigo  # noqa  pylint: disable=unused-import
except ImportError:
    pass


class OWServer():
    """
    Title Placeholder

    Body placeholder
    """
    def __init__(self, plugin):
        self.plugin = plugin

    @staticmethod
    def server_state_dict():
        """
        Title Placeholder

        Body placeholder
        """
        server_state_dict = {
            'owsDataErrors': 'DataErrors',
            'owsDataErrorsChannel1': 'DataErrorsChannel1',
            'owsDataErrorsChannel2': 'DataErrorsChannel2',
            'owsDataErrorsChannel3': 'DataErrorsChannel3',
            'owsDateTime': 'DateTime',
            'owsDeviceName': 'DeviceName',
            'owsDevicesConnected': 'DevicesConnected',
            'owsDevicesConnectedChannel1': 'DevicesConnectedChannel1',
            'owsDevicesConnectedChannel2': 'DevicesConnectedChannel2',
            'owsDevicesConnectedChannel3': 'DevicesConnectedChannel3',
            'owsHostName': 'HostName',
            'owsLoopTime': 'LoopTime',
            'owsMACAddress': 'MACAddress',
            'owsPollCount': 'PollCount',
            'owsRomID': 'HostName',
            'owsVoltageChannel1': 'VoltageChannel1',
            'owsVoltageChannel2': 'VoltageChannel2',
            'owsVoltageChannel3': 'VoltageChannel3',
            'owsVoltagePower': 'VoltagePower'
        }
        return server_state_dict

    @staticmethod
    def ds18b20_state_dict():
        """
        Title Placeholder

        Body placeholder
        """

        ds18b20_state_dict = {
            'owsChannel': 'Channel',
            'owsFamily': 'Family',
            'owsHealth': 'Health',
            'owsPowerSource': 'PowerSource',
            'owsPrimaryValue': 'PrimaryValue',
            'owsRawData': 'RawData',
            'owsResolution': 'Resolution',
            'owsRomID': 'ROMId',
            'owsTemperature': 'Temperature',
            'owsType': 'Name',
            'owsUserByte1': 'UserByte1',
            'owsUserByte2': 'UserByte2'
        }

        return ds18b20_state_dict

    @staticmethod
    def ds18s20_state_dict():
        """
        Title Placeholder

        Body placeholder
        """

        ds18s20_state_dict = {
            'owsChannel': 'Channel',
            'owsFamily': 'Family',
            'owsHealth': 'Health',
            'owsPrimaryValue': 'PrimaryValue',
            'owsRawData': 'RawData',
            'owsRomID': 'ROMId',
            'owsTemperature': 'Temperature',
            'owsType': 'Name',
            'owsUserByte1': 'UserByte1',
            'owsUserByte2': 'UserByte2'
        }

        return ds18s20_state_dict

    @staticmethod
    def ds2406_state_dict():
        """
        Title Placeholder

        Body placeholder
        """

        ds2406_state_dict = {
            'owsActivityLatch_A': 'ActivityLatch_A',
            'owsActivityLatch_B': 'ActivityLatch_B',
            'owsActivityLatchReset': 'ActivityLatchReset',
            'owsChannel': 'Channel',
            'owsFamily': 'Family',
            'owsFlipFlop_A': 'FlipFlop_A',
            'owsFlipFlop_B': 'FlipFlop_B',
            'owsHealth': 'Health',
            'owsInputLevel_A': 'InputLevel_A',
            'owsInputLevel_B': 'InputLevel_B',
            'owsNumberOfChannels': 'NumberOfChannels',
            'owsPowerSource': 'PowerSource',
            'owsPrimaryValue': 'PrimaryValue',
            'owsRawData': 'RawData',
            'owsRomID': 'ROMId',
            'owsType': 'Name'
        }

        return ds2406_state_dict

    @staticmethod
    def ds2408_state_dict():
        """
        Title Placeholder

        Body placeholder
        """

        ds2408_state_dict = {
            'owsChannel': 'Channel',
            'owsFamily': 'Family',
            'owsHealth': 'Health',
            'owsPIOActivityLatchState': 'PIOActivityLatchState',
            'owsPIOLogicState': 'PIOLogicState',
            'owsPIOOutputLatchState': 'PIOOutputLatchState',
            'owsPowerOnResetLatch': 'PowerOnResetLatch',
            'owsPrimaryValue': 'PrimaryValue',
            'owsRawData': 'RawData',
            'owsRomID': 'ROMId',
            'owsRSTZConfiguration': 'RSTZconfiguration',
            'owsType': 'Name',
            'owsVccPowerStatus': 'VccPowerStatus'
        }

        return ds2408_state_dict

    @staticmethod
    def ds2423_state_dict():
        """
        Title Placeholder

        Body placeholder
        """

        ds2423_state_dict = {
            'owsChannel': 'Channel',
            'owsCounterA': 'Counter_A',
            'owsCounterB': 'Counter_B',
            'owsFamily': 'Family',
            'owsHealth': 'Health',
            'owsPrimaryValue': 'PrimaryValue',
            'owsRawData': 'RawData',
            'owsRomID': 'ROMId',
            'owsType': 'Name'
        }

        return ds2423_state_dict

    @staticmethod
    def ds2438_state_dict():
        """
        Title Placeholder

        Body placeholder
        """

        ds2438_state_dict = {
            'owsChannel': 'Channel',
            'owsFamily': 'Family',
            'owsHealth': 'Health',
            'owsHumidity': 'Humidity',
            'owsPrimaryValue': 'PrimaryValue',
            'owsRawData': 'RawData',
            'owsRomID': 'ROMId',
            'owsTemperature': 'Temperature',
            'owsType': 'Name',
            'owsVad': 'Vad',
            'owsVdd': 'Vdd',
            'owsVsense': 'Vsense'
        }

        return ds2438_state_dict

    @staticmethod
    def ds2450_state_dict():
        """
        Title Placeholder

        Body placeholder
        """

        ds2450_state_dict = {
        'owsChannel': 'Channel',
        'owsChannelAConversionRange': 'ChannelAConversionRange',
        'owsChannelAConversionResolution': 'ChannelAConversionResolution',
        'owsChannelAConversionValue': 'ChannelAConversionValue',
        'owsChannelAOutputControl': 'ChannelAOutputControl',
        'owsChannelAOutputEnable': 'ChannelAOutputEnable',
        'owsChannelBConversionRange': 'ChannelBConversionRange',
        'owsChannelBConversionResolution': 'ChannelBConversionResolution',
        'owsChannelBConversionValue': 'ChannelBConversionValue',
        'owsChannelBOutputControl': 'ChannelBOutputControl',
        'owsChannelBOutputEnable': 'ChannelBOutputEnable',
        'owsChannelCConversionRange': 'ChannelCConversionRange',
        'owsChannelCConversionResolution': 'ChannelCConversionResolution',
        'owsChannelCConversionValue': 'ChannelCConversionValue',
        'owsChannelCOutputControl': 'ChannelCOutputControl',
        'owsChannelCOutputEnable': 'ChannelCOutputEnable',
        'owsChannelDConversionRange': 'ChannelDConversionRange',
        'owsChannelDConversionResolution': 'ChannelDConversionResolution',
        'owsChannelDConversionValue': 'ChannelDConversionValue',
        'owsChannelDOutputControl': 'ChannelDOutputControl',
        'owsChannelDOutputEnable': 'ChannelDOutputEnable',
        'owsFamily': 'Family',
        'owsHealth': 'Health',
        'owsPrimaryValue': 'PrimaryValue',
        'owsPowerOnReset': 'PowerOnReset',
        'owsRawData': 'RawData',
        'owsRomID': 'ROMId',
        'owsType': 'Name',
        'owsVCCControl': 'VCCControl',
        }

        return ds2450_state_dict

    @staticmethod
    def eds0064_state_dict():
        """
        Title Placeholder

        Body placeholder
        """

        eds0064_state_dict = {
            'owsChannel': 'Channel',
            'owsClearAlarms': 'ClearAlarms',
            'owsCounter1': 'Counter1',
            'owsCounter2': 'Counter2',
            'owsFamily': 'Family',
            'owsHealth': 'Health',
            'owsLED': 'LED',
            'owsLEDFunction': 'LEDFunction',
            'owsLEDState': 'LEDState',
            'owsPrimaryValue': 'PrimaryValue',
            'owsRawData': 'RawData',
            'owsRelay': 'Relay',
            'owsRelayFunction': 'RelayFunction',
            'owsRelayState': 'RelayState',
            'owsRomID': 'ROMId',
            'owsTemperature': 'Temperature',
            'owsTemperatureHighAlarmState': 'TemperatureHighAlarmState',
            'owsTemperatureHighAlarmValue': 'TemperatureHighAlarmValue',
            'owsTemperatureHighConditionalSearchState': 'TemperatureHighConditionalSearchState',
            'owsTemperatureLowAlarmState': 'TemperatureLowAlarmState',
            'owsTemperatureLowAlarmValue': 'TemperatureLowAlarmValue',
            'owsTemperatureLowConditionalSearchState': 'TemperatureLowConditionalSearchState',
            'owsType': 'Name',
            'owsVersion': 'Version',
        }

        return eds0064_state_dict

    @staticmethod
    def eds0065_state_dict():
        """
        Title Placeholder

        Body placeholder
        """

        eds0065_state_dict = {
            'owsChannel': 'Channel',
            'owsClearAlarms': 'ClearAlarms',
            'owsCounter1': 'Counter1',
            'owsCounter2': 'Counter2',
            'owsDewPoint': 'DewPoint',
            'owsDewPointHighAlarmState': 'DewPointHighAlarmState',
            'owsDewPointHighAlarmValue': 'DewPointHighAlarmValue',
            'owsDewPointHighConditionalSearchState': 'DewPointHighConditionalSearchState',
            'owsDewPointLowAlarmState': 'DewPointLowAlarmState',
            'owsDewPointLowAlarmValue': 'DewPointLowAlarmValue',
            'owsDewPointLowConditionalSearchState': 'DewPointLowConditionalSearchState',
            'owsFamily': 'Family',
            'owsHealth': 'Health',
            'owsHeatIndex': 'HeatIndex',
            'owsHeatIndexHighAlarmState': 'HeatIndexHighAlarmState',
            'owsHeatIndexHighAlarmValue': 'HeatIndexHighAlarmValue',
            'owsHeatIndexHighConditionalSearchState': 'HeatIndexHighConditionalSearchState',
            'owsHeatIndexLowAlarmState': 'HeatIndexLowAlarmState',
            'owsHeatIndexLowAlarmValue': 'HeatIndexLowAlarmValue',
            'owsHeatIndexLowConditionalSearchState': 'HeatIndexLowConditionalSearchState',
            'owsHumidex': 'Humidex',
            'owsHumidexHighAlarmState': 'HumidexHighAlarmState',
            'owsHumidexHighAlarmValue': 'HumidexHighAlarmValue',
            'owsHumidexHighConditionalSearchState': 'HumidexHighConditionalSearchState',
            'owsHumidexLowAlarmState': 'HumidexLowAlarmState',
            'owsHumidexLowAlarmValue': 'HumidexLowAlarmValue',
            'owsHumidexLowConditionalSearchState': 'HumidexLowConditionalSearchState',
            'owsHumidity': 'Humidity',
            'owsHumidityHighAlarmState': 'HumidityHighAlarmState',
            'owsHumidityHighAlarmValue': 'HumidityHighAlarmValue',
            'owsHumidityHighConditionalSearchState': 'HumidityHighConditionalSearchState',
            'owsHumidityLowAlarmState': 'HumidityLowAlarmState',
            'owsHumidityLowAlarmValue': 'HumidityLowAlarmValue',
            'owsHumidityLowConditionalSearchState': 'HumidityLowConditionalSearchState',
            'owsLED': 'LED',
            'owsLEDFunction': 'LEDFunction',
            'owsLEDState': 'LEDState',
            'owsPrimaryValue': 'PrimaryValue',
            'owsRawData': 'RawData',
            'owsRelay': 'Relay',
            'owsRelayFunction': 'RelayFunction',
            'owsRelayState': 'RelayState',
            'owsRomID': 'ROMId',
            'owsTemperature': 'Temperature',
            'owsTemperatureHighAlarmState': 'TemperatureHighAlarmState',
            'owsTemperatureHighAlarmValue': 'TemperatureHighAlarmValue',
            'owsTemperatureHighConditionalSearchState': 'TemperatureHighConditionalSearchState',
            'owsTemperatureLowAlarmState': 'TemperatureLowAlarmState',
            'owsTemperatureLowAlarmValue': 'TemperatureLowAlarmValue',
            'owsTemperatureLowConditionalSearchState': 'TemperatureLowConditionalSearchState',
            'owsType': 'Name',
            'owsVersion': 'Version',
        }

        return eds0065_state_dict

    @staticmethod
    def eds0066_state_dict():
        """
        Title Placeholder

        Body placeholder
        """

        eds0066_state_dict = {
            'owsBarometricPressureHg': 'BarometricPressureHg',
            'owsBarometricPressureHgHighAlarmState': 'BarometricPressureHgHighAlarmState',
            'owsBarometricPressureHgHighAlarmValue': 'BarometricPressureHgHighAlarmValue',
            'owsBarometricPressureHgHighConditionalSearchState': 'BarometricPressureHgHighConditionalSearchState',
            'owsBarometricPressureHgLowAlarmState': 'BarometricPressureHgLowAlarmState',
            'owsBarometricPressureHgLowAlarmValue': 'BarometricPressureHgLowAlarmValue',
            'owsBarometricPressureHgLowConditionalSearchState': 'BarometricPressureHgLowConditionalSearchState',
            'owsBarometricPressureMb': 'BarometricPressureMb',
            'owsBarometricPressureMbHighAlarmState': 'BarometricPressureMbHighAlarmState',
            'owsBarometricPressureMbHighAlarmValue': 'BarometricPressureMbHighAlarmValue',
            'owsBarometricPressureMbHighConditionalSearchState': 'BarometricPressureMbHighConditionalSearchState',
            'owsBarometricPressureMbLowAlarmState': 'BarometricPressureMbLowAlarmState',
            'owsBarometricPressureMbLowAlarmValue': 'BarometricPressureMbLowAlarmValue',
            'owsBarometricPressureMbLowConditionalSearchState': 'BarometricPressureMbLowConditionalSearchState',
            'owsChannel': 'Channel',
            'owsClearAlarms': 'ClearAlarms',
            'owsCounter1': 'Counter1',
            'owsCounter2': 'Counter2',
            'owsFamily': 'Family',
            'owsHealth': 'Health',
            'owsLED': 'LED',
            'owsLEDFunction': 'LEDFunction',
            'owsLEDState': 'LEDState',
            'owsPrimaryValue': 'PrimaryValue',
            'owsRawData': 'RawData',
            'owsRelay': 'Relay',
            'owsRelayFunction': 'RelayFunction',
            'owsRelayState': 'RelayState',
            'owsRomID': 'ROMId',
            'owsTemperature': 'Temperature',
            'owsTemperatureHighAlarmState': 'TemperatureHighAlarmState',
            'owsTemperatureHighAlarmValue': 'TemperatureHighAlarmValue',
            'owsTemperatureHighConditionalSearchState': 'TemperatureHighConditionalSearchState',
            'owsTemperatureLowAlarmState': 'TemperatureLowAlarmState',
            'owsTemperatureLowAlarmValue': 'TemperatureLowAlarmValue',
            'owsTemperatureLowConditionalSearchState': 'TemperatureLowConditionalSearchState',
            'owsType': 'Name',
            'owsVersion': 'Version',
        }

        return eds0066_state_dict

    @staticmethod
    def eds0067_state_dict():
        """
        Title Placeholder

        Body placeholder
        """

        eds0067_state_dict = {
            'owsChannel': 'Channel',
            'owsClearAlarms': 'ClearAlarms',
            'owsCounter1': 'Counter1',
            'owsCounter2': 'Counter2',
            'owsFamily': 'Family',
            'owsHealth': 'Health',
            'owsLED': 'LED',
            'owsLEDFunction': 'LEDFunction',
            'owsLEDState': 'LEDState',
            'owsLight': 'Light',
            'owsLightHighAlarmState': 'LightHighAlarmState',
            'owsLightHighAlarmValue': 'LightHighAlarmValue',
            'owsLightHighConditionalSearchState': 'LightHighConditionalSearchState',
            'owsLightLowAlarmState': 'LightLowAlarmState',
            'owsLightLowAlarmValue': 'LightLowAlarmValue',
            'owsLightLowConditionalSearchState': 'LightLowConditionalSearchState',
            'owsPrimaryValue': 'PrimaryValue',
            'owsRawData': 'RawData',
            'owsRelay': 'Relay',
            'owsRelayFunction': 'RelayFunction',
            'owsRelayState': 'RelayState',
            'owsRomID': 'ROMId',
            'owsTemperature': 'Temperature',
            'owsTemperatureHighAlarmState': 'TemperatureHighAlarmState',
            'owsTemperatureHighAlarmValue': 'TemperatureHighAlarmValue',
            'owsTemperatureHighConditionalSearchState': 'TemperatureHighConditionalSearchState',
            'owsTemperatureLowAlarmState': 'TemperatureLowAlarmState',
            'owsTemperatureLowAlarmValue': 'TemperatureLowAlarmValue',
            'owsTemperatureLowConditionalSearchState': 'TemperatureLowConditionalSearchState',
            'owsType': 'Name',
            'owsVersion': 'Version',
        }

        return eds0067_state_dict

    @staticmethod
    def eds0068_state_dict():
        """
        Title Placeholder

        Body placeholder
        """

        eds0068_state_dict = {
            'owsBarometricPressureHg': 'BarometricPressureHg',
            'owsBarometricPressureHgHighAlarmState': 'BarometricPressureHgHighAlarmState',
            'owsBarometricPressureHgHighAlarmValue': 'BarometricPressureHgHighAlarmValue',
            'owsBarometricPressureHgHighConditionalSearchState': 'BarometricPressureHgHighConditionalSearchState',
            'owsBarometricPressureHgLowAlarmState': 'BarometricPressureHgLowAlarmState',
            'owsBarometricPressureHgLowAlarmValue': 'BarometricPressureHgLowAlarmValue',
            'owsBarometricPressureHgLowConditionalSearchState': 'BarometricPressureHgLowConditionalSearchState',
            'owsBarometricPressureMb': 'BarometricPressureMb',
            'owsBarometricPressureMbHighAlarmState': 'BarometricPressureMbHighAlarmState',
            'owsBarometricPressureMbHighAlarmValue': 'BarometricPressureMbHighAlarmValue',
            'owsBarometricPressureMbHighConditionalSearchState': 'BarometricPressureMbHighConditionalSearchState',
            'owsBarometricPressureMbLowAlarmState': 'BarometricPressureMbLowAlarmState',
            'owsBarometricPressureMbLowAlarmValue': 'BarometricPressureMbLowAlarmValue',
            'owsBarometricPressureMbLowConditionalSearchState': 'BarometricPressureMbLowConditionalSearchState',
            'owsChannel': 'Channel',
            'owsClearAlarms': 'ClearAlarms',
            'owsCounter1': 'Counter1',
            'owsCounter2': 'Counter2',
            'owsDewPoint': 'DewPoint',
            'owsDewPointHighAlarmState': 'DewPointHighAlarmState',
            'owsDewPointHighAlarmValue': 'DewPointHighAlarmValue',
            'owsDewPointHighConditionalSearchState': 'DewPointHighConditionalSearchState',
            'owsDewPointLowAlarmState': 'DewPointLowAlarmState',
            'owsDewPointLowAlarmValue': 'DewPointLowAlarmValue',
            'owsDewPointLowConditionalSearchState': 'DewPointLowConditionalSearchState',
            'owsFamily': 'Family',
            'owsHealth': 'Health',
            'owsHeatIndex': 'HeatIndex',
            'owsHeatIndexHighAlarmState': 'HeatIndexHighAlarmState',
            'owsHeatIndexHighAlarmValue': 'HeatIndexHighAlarmValue',
            'owsHeatIndexHighConditionalSearchState': 'HeatIndexHighConditionalSearchState',
            'owsHeatIndexLowAlarmState': 'HeatIndexLowAlarmState',
            'owsHeatIndexLowAlarmValue': 'HeatIndexLowAlarmValue',
            'owsHeatIndexLowConditionalSearchState': 'HeatIndexLowConditionalSearchState',
            'owsHumidex': 'Humidex',
            'owsHumidexHighAlarmState': 'HumidexHighAlarmState',
            'owsHumidexHighAlarmValue': 'HumidexHighAlarmValue',
            'owsHumidexHighConditionalSearchState': 'HumidexHighConditionalSearchState',
            'owsHumidexLowAlarmState': 'HumidexLowAlarmState',
            'owsHumidexLowAlarmValue': 'HumidexLowAlarmValue',
            'owsHumidexLowConditionalSearchState': 'HumidexLowConditionalSearchState',
            'owsHumidity': 'Humidity',
            'owsHumidityHighAlarmState': 'HumidityHighAlarmState',
            'owsHumidityHighAlarmValue': 'HumidityHighAlarmValue',
            'owsHumidityHighConditionalSearchState': 'HumidityHighConditionalSearchState',
            'owsHumidityLowAlarmState': 'HumidityLowAlarmState',
            'owsHumidityLowAlarmValue': 'HumidityLowAlarmValue',
            'owsHumidityLowConditionalSearchState': 'HumidityLowConditionalSearchState',
            'owsLED': 'LED',
            'owsLEDFunction': 'LEDFunction',
            'owsLEDState': 'LEDState',
            'owsLight': 'Light',
            'owsLightHighAlarmState': 'LightHighAlarmState',
            'owsLightHighAlarmValue': 'LightHighAlarmValue',
            'owsLightHighConditionalSearchState': 'LightHighConditionalSearchState',
            'owsLightLowAlarmState': 'LightLowAlarmState',
            'owsLightLowAlarmValue': 'LightLowAlarmValue',
            'owsLightLowConditionalSearchState': 'LightLowConditionalSearchState',
            'owsPrimaryValue': 'PrimaryValue',
            'owsRawData': 'RawData',
            'owsRelay': 'Relay',
            'owsRelayFunction': 'RelayFunction',
            'owsRelayState': 'RelayState',
            'owsRomID': 'ROMId',
            'owsTemperature': 'Temperature',
            'owsTemperatureHighAlarmState': 'TemperatureHighAlarmState',
            'owsTemperatureHighAlarmValue': 'TemperatureHighAlarmValue',
            'owsTemperatureHighConditionalSearchState': 'TemperatureHighConditionalSearchState',
            'owsTemperatureLowAlarmState': 'TemperatureLowAlarmState',
            'owsTemperatureLowAlarmValue': 'TemperatureLowAlarmValue',
            'owsTemperatureLowConditionalSearchState': 'TemperatureLowConditionalSearchState',
            'owsType': 'Name',
            'owsVersion': 'Version'
        }

        return eds0068_state_dict

    @staticmethod
    def eds0070_state_dict():
        """
        Title Placeholder

        Body placeholder
        """

        eds0070_state_dict = {
            'owsChannel': 'Channel',
            'owsClearAlarms': 'ClearAlarms',
            'owsCounter': 'Counter',
            'owsFamily': 'Family',
            'owsHealth': 'Health',
            'owsLED': 'LED',
            'owsLEDFunction': 'LEDFunction',
            'owsLEDState': 'LEDState',
            'owsPrimaryValue': 'PrimaryValue',
            'owsRawData': 'RawData',
            'owsRelay': 'Relay',
            'owsRelayFunction': 'RelayFunction',
            'owsRelayState': 'RelayState',
            'owsRomID': 'ROMId',
            'owsType': 'Name',
            'owsVersion': 'Version',
            'owsVibrationHighAlarmState': 'VibrationHighAlarmState',
            'owsVibrationHighAlarmValue': 'VibrationHighAlarmValue',
            'owsVibrationHighConditionalSearchState': 'VibrationHighConditionalSearchState',
            'owsVibrationInstant': 'VibrationInstant',
            'owsVibrationLowAlarmState': 'VibrationLowAlarmState',
            'owsVibrationLowAlarmValue': 'VibrationLowAlarmValue',
            'owsVibrationLowConditionalSearchState': 'VibrationLowConditionalSearchState',
            'owsVibrationMaximum': 'VibrationMaximum',
            'owsVibrationMinimum': 'VibrationMinimum',
            'owsVibrationPeak': 'VibrationPeak',
        }

        return eds0070_state_dict

    @staticmethod
    def eds0071_state_dict():
        """
        Title Placeholder

        Body placeholder
        """

        eds0071_state_dict = {
            'owsCalibrationKey': 'CalibrationKey',
            'owsCalibrationValue': 'CalibrationValue',
            'owsChannel': 'Channel',
            'owsClearAlarms': 'ClearAlarms',
            'owsConversionCounter': 'ConversionCounter',
            'owsCounter': 'Counter',
            'owsFamily': 'Family',
            'owsHealth': 'Health',
            'owsLED': 'LED',
            'owsLEDFunction': 'LEDFunction',
            'owsLEDState': 'LEDState',
            'owsPrimaryValue': 'PrimaryValue',
            'owsRawData': 'RawData',
            'owsRelay': 'Relay',
            'owsRelayFunction': 'RelayFunction',
            'owsRelayState': 'RelayState',
            'owsRomID': 'ROMId',
            'owsRTDFault': 'RTDFault',
            'owsRTDFaultConditionalSearchState': 'RTDFaultConditionalSearchState',
            'owsRTDOhms': 'RTDOhms',
            'owsRTDReadDelay': 'RTDReadDelay',
            'owsRTDResistanceHighAlarmState': 'RTDResistanceHighAlarmState',
            'owsRTDResistanceHighAlarmValue': 'RTDResistanceHighAlarmValue',
            'owsRTDResistanceHighConditionalSearchState': 'RTDResistanceHighConditionalSearchState',
            'owsRTDResistanceLowAlarmState': 'RTDResistanceLowAlarmState',
            'owsRTDResistanceLowAlarmValue': 'RTDResistanceLowAlarmValue',
            'owsRTDResistanceLowConditionalSearchState': 'RTDResistanceLowConditionalSearchState',
            'owsTemperature': 'Temperature',
            'owsTemperatureHighAlarmState': 'TemperatureHighAlarmState',
            'owsTemperatureHighAlarmValue': 'TemperatureHighAlarmValue',
            'owsTemperatureHighConditionalSearchState': 'TemperatureHighConditionalSearchState',
            'owsTemperatureLowAlarmState': 'TemperatureLowAlarmState',
            'owsTemperatureLowAlarmValue': 'TemperatureLowAlarmValue',
            'owsTemperatureLowConditionalSearchState': 'TemperatureLowConditionalSearchState',
            'owsType': 'Name',
            'owsVersion': 'Version',
        }

        return eds0071_state_dict

    @staticmethod
    def eds0080_state_dict():
        """
        Title Placeholder

        Body placeholder
        """

        eds0080_state_dict = {
            'owsChannel': 'Channel',
            'owsClearAlarms': 'ClearAlarms',
            'owsCounter': 'Counter',
            'owsFamily': 'Family',
            'owsHealth': 'Health',
            'owsLED': 'LED',
            'owsLEDFunction': 'LEDFunction',
            'owsLEDState': 'LEDState',
            'owsPrimaryValue': 'PrimaryValue',
            'owsRawData': 'RawData',
            'owsRelay': 'Relay',
            'owsRelayFunction': 'RelayFunction',
            'owsRelayState': 'RelayState',
            'owsRomID': 'ROMId',
            'owsType': 'Name',
            'owsv4to20mAInput1HighAlarmState': 'v4to20mAInput1HighAlarmState',
            'owsv4to20mAInput1HighAlarmValue': 'v4to20mAInput1HighAlarmValue',
            'owsv4to20mAInput1HighConditionalSearchState': 'v4to20mAInput1HighConditionalSearchState',
            'owsv4to20mAInput1Instant': 'v4to20mAInput1Instant',
            'owsv4to20mAInput1LowAlarmState': 'v4to20mAInput1LowAlarmState',
            'owsv4to20mAInput1LowAlarmValue': 'v4to20mAInput1LowAlarmValue',
            'owsv4to20mAInput1LowConditionalSearchState': 'v4to20mAInput1LowConditionalSearchState',
            'owsv4to20mAInput1Maximum': 'v4to20mAInput1Maximum',
            'owsv4to20mAInput1Minimum': 'v4to20mAInput1Minimum',
            'owsv4to20mAInput2HighAlarmState': 'v4to20mAInput2HighAlarmState',
            'owsv4to20mAInput2HighAlarmValue': 'v4to20mAInput2HighAlarmValue',
            'owsv4to20mAInput2HighConditionalSearchState': 'v4to20mAInput2HighConditionalSearchState',
            'owsv4to20mAInput2Instant': 'v4to20mAInput2Instant',
            'owsv4to20mAInput2LowAlarmState': 'v4to20mAInput2LowAlarmState',
            'owsv4to20mAInput2LowAlarmValue': 'v4to20mAInput2LowAlarmValue',
            'owsv4to20mAInput2LowConditionalSearchState': 'v4to20mAInput2LowConditionalSearchState',
            'owsv4to20mAInput2Maximum': 'v4to20mAInput2Maximum',
            'owsv4to20mAInput2Minimum': 'v4to20mAInput2Minimum',
            'owsv4to20mAInput3HighAlarmState': 'v4to20mAInput3HighAlarmState',
            'owsv4to20mAInput3HighAlarmValue': 'v4to20mAInput3HighAlarmValue',
            'owsv4to20mAInput3HighConditionalSearchState': 'v4to20mAInput3HighConditionalSearchState',
            'owsv4to20mAInput3Instant': 'v4to20mAInput3Instant',
            'owsv4to20mAInput3LowAlarmState': 'v4to20mAInput3LowAlarmState',
            'owsv4to20mAInput3LowAlarmValue': 'v4to20mAInput3LowAlarmValue',
            'owsv4to20mAInput3LowConditionalSearchState': 'v4to20mAInput3LowConditionalSearchState',
            'owsv4to20mAInput3Maximum': 'v4to20mAInput3Maximum',
            'owsv4to20mAInput3Minimum': 'v4to20mAInput3Minimum',
            'owsv4to20mAInput4HighAlarmState': 'v4to20mAInput4HighAlarmState',
            'owsv4to20mAInput4HighAlarmValue': 'v4to20mAInput4HighAlarmValue',
            'owsv4to20mAInput4HighConditionalSearchState': 'v4to20mAInput4HighConditionalSearchState',
            'owsv4to20mAInput4Instant': 'v4to20mAInput4Instant',
            'owsv4to20mAInput4LowAlarmState': 'v4to20mAInput4LowAlarmState',
            'owsv4to20mAInput4LowAlarmValue': 'v4to20mAInput4LowAlarmValue',
            'owsv4to20mAInput4LowConditionalSearchState': 'v4to20mAInput4LowConditionalSearchState',
            'owsv4to20mAInput4Maximum': 'v4to20mAInput4Maximum',
            'owsv4to20mAInput4Minimum': 'v4to20mAInput4Minimum',
            'owsv4to20mAInput5HighAlarmState': 'v4to20mAInput5HighAlarmState',
            'owsv4to20mAInput5HighAlarmValue': 'v4to20mAInput5HighAlarmValue',
            'owsv4to20mAInput5HighConditionalSearchState': 'v4to20mAInput5HighConditionalSearchState',
            'owsv4to20mAInput5Instant': 'v4to20mAInput5Instant',
            'owsv4to20mAInput5LowAlarmState': 'v4to20mAInput5LowAlarmState',
            'owsv4to20mAInput5LowAlarmValue': 'v4to20mAInput5LowAlarmValue',
            'owsv4to20mAInput5LowConditionalSearchState': 'v4to20mAInput5LowConditionalSearchState',
            'owsv4to20mAInput5Maximum': 'v4to20mAInput5Maximum',
            'owsv4to20mAInput5Minimum': 'v4to20mAInput5Minimum',
            'owsv4to20mAInput6HighAlarmState': 'v4to20mAInput6HighAlarmState',
            'owsv4to20mAInput6HighAlarmValue': 'v4to20mAInput6HighAlarmValue',
            'owsv4to20mAInput6HighConditionalSearchState': 'v4to20mAInput6HighConditionalSearchState',
            'owsv4to20mAInput6Instant': 'v4to20mAInput6Instant',
            'owsv4to20mAInput6LowAlarmState': 'v4to20mAInput6LowAlarmState',
            'owsv4to20mAInput6LowAlarmValue': 'v4to20mAInput6LowAlarmValue',
            'owsv4to20mAInput6LowConditionalSearchState': 'v4to20mAInput6LowConditionalSearchState',
            'owsv4to20mAInput6Maximum': 'v4to20mAInput6Maximum',
            'owsv4to20mAInput6Minimum': 'v4to20mAInput6Minimum',
            'owsv4to20mAInput7HighAlarmState': 'v4to20mAInput7HighAlarmState',
            'owsv4to20mAInput7HighAlarmValue': 'v4to20mAInput7HighAlarmValue',
            'owsv4to20mAInput7HighConditionalSearchState': 'v4to20mAInput7HighConditionalSearchState',
            'owsv4to20mAInput7Instant': 'v4to20mAInput7Instant',
            'owsv4to20mAInput7LowAlarmState': 'v4to20mAInput7LowAlarmState',
            'owsv4to20mAInput7LowAlarmValue': 'v4to20mAInput7LowAlarmValue',
            'owsv4to20mAInput7LowConditionalSearchState': 'v4to20mAInput7LowConditionalSearchState',
            'owsv4to20mAInput7Maximum': 'v4to20mAInput7Maximum',
            'owsv4to20mAInput7Minimum': 'v4to20mAInput7Minimum',
            'owsv4to20mAInput8HighAlarmState': 'v4to20mAInput8HighAlarmState',
            'owsv4to20mAInput8HighAlarmValue': 'v4to20mAInput8HighAlarmValue',
            'owsv4to20mAInput8HighConditionalSearchState': 'v4to20mAInput8HighConditionalSearchState',
            'owsv4to20mAInput8Instant': 'v4to20mAInput8Instant',
            'owsv4to20mAInput8LowAlarmState': 'v4to20mAInput8LowAlarmState',
            'owsv4to20mAInput8LowAlarmValue': 'v4to20mAInput8LowAlarmValue',
            'owsv4to20mAInput8LowConditionalSearchState': 'v4to20mAInput8LowConditionalSearchState',
            'owsv4to20mAInput8Maximum': 'v4to20mAInput8Maximum',
            'owsv4to20mAInput8Minimum': 'v4to20mAInput8Minimum',
            'owsVersion': 'Version',
        }

        return eds0080_state_dict

    @staticmethod
    def eds0082_state_dict():
        """
        Title Placeholder

        Body placeholder
        """

        eds0082_state_dict = {
            'owsChannel': 'Channel',
            'owsClearAlarms': 'ClearAlarms',
            'owsCounter': 'Counter',
            'owsFamily': 'Family',
            'owsHealth': 'Health',
            'owsLED': 'LED',
            'owsLEDFunction': 'LEDFunction',
            'owsLEDState': 'LEDState',
            'owsPrimaryValue': 'PrimaryValue',
            'owsRawData': 'RawData',
            'owsRelay': 'Relay',
            'owsRelayFunction': 'RelayFunction',
            'owsRelayState': 'RelayState',
            'owsRomID': 'ROMId',
            'owsType': 'Name',
            'owsv0to10VoltInput1HighAlarmState': 'v0to10VoltInput1HighAlarmState',
            'owsv0to10VoltInput1HighAlarmValue': 'v0to10VoltInput1HighAlarmValue',
            'owsv0to10VoltInput1HighConditionalSearchState': 'v0to10VoltInput1HighConditionalSearchState',
            'owsv0to10VoltInput1Instant': 'v0to10VoltInput1Instant',
            'owsv0to10VoltInput1LowAlarmState': 'v0to10VoltInput1LowAlarmState',
            'owsv0to10VoltInput1LowAlarmValue': 'v0to10VoltInput1LowAlarmValue',
            'owsv0to10VoltInput1LowConditionalSearchState': 'v0to10VoltInput1LowConditionalSearchState',
            'owsv0to10VoltInput1Maximum': 'v0to10VoltInput1Maximum',
            'owsv0to10VoltInput1Minimum': 'v0to10VoltInput1Minimum',
            'owsv0to10VoltInput2HighAlarmState': 'v0to10VoltInput2HighAlarmState',
            'owsv0to10VoltInput2HighAlarmValue': 'v0to10VoltInput2HighAlarmValue',
            'owsv0to10VoltInput2HighConditionalSearchState': 'v0to10VoltInput2HighConditionalSearchState',
            'owsv0to10VoltInput2Instant': 'v0to10VoltInput2Instant',
            'owsv0to10VoltInput2LowAlarmState': 'v0to10VoltInput2LowAlarmState',
            'owsv0to10VoltInput2LowAlarmValue': 'v0to10VoltInput2LowAlarmValue',
            'owsv0to10VoltInput2LowConditionalSearchState': 'v0to10VoltInput2LowConditionalSearchState',
            'owsv0to10VoltInput2Maximum': 'v0to10VoltInput2Maximum',
            'owsv0to10VoltInput2Minimum': 'v0to10VoltInput2Minimum',
            'owsv0to10VoltInput3HighAlarmState': 'v0to10VoltInput3HighAlarmState',
            'owsv0to10VoltInput3HighAlarmValue': 'v0to10VoltInput3HighAlarmValue',
            'owsv0to10VoltInput3HighConditionalSearchState': 'v0to10VoltInput3HighConditionalSearchState',
            'owsv0to10VoltInput3Instant': 'v0to10VoltInput3Instant',
            'owsv0to10VoltInput3LowAlarmState': 'v0to10VoltInput3LowAlarmState',
            'owsv0to10VoltInput3LowAlarmValue': 'v0to10VoltInput3LowAlarmValue',
            'owsv0to10VoltInput3LowConditionalSearchState': 'v0to10VoltInput3LowConditionalSearchState',
            'owsv0to10VoltInput3Maximum': 'v0to10VoltInput3Maximum',
            'owsv0to10VoltInput3Minimum': 'v0to10VoltInput3Minimum',
            'owsv0to10VoltInput4HighAlarmState': 'v0to10VoltInput4HighAlarmState',
            'owsv0to10VoltInput4HighAlarmValue': 'v0to10VoltInput4HighAlarmValue',
            'owsv0to10VoltInput4HighConditionalSearchState': 'v0to10VoltInput4HighConditionalSearchState',
            'owsv0to10VoltInput4Instant': 'v0to10VoltInput4Instant',
            'owsv0to10VoltInput4LowAlarmState': 'v0to10VoltInput4LowAlarmState',
            'owsv0to10VoltInput4LowAlarmValue': 'v0to10VoltInput4LowAlarmValue',
            'owsv0to10VoltInput4LowConditionalSearchState': 'v0to10VoltInput4LowConditionalSearchState',
            'owsv0to10VoltInput4Maximum': 'v0to10VoltInput4Maximum',
            'owsv0to10VoltInput4Minimum': 'v0to10VoltInput4Minimum',
            'owsv0to10VoltInput5HighAlarmState': 'v0to10VoltInput5HighAlarmState',
            'owsv0to10VoltInput5HighAlarmValue': 'v0to10VoltInput5HighAlarmValue',
            'owsv0to10VoltInput5HighConditionalSearchState': 'v0to10VoltInput5HighConditionalSearchState',
            'owsv0to10VoltInput5Instant': 'v0to10VoltInput5Instant',
            'owsv0to10VoltInput5LowAlarmState': 'v0to10VoltInput5LowAlarmState',
            'owsv0to10VoltInput5LowAlarmValue': 'v0to10VoltInput5LowAlarmValue',
            'owsv0to10VoltInput5LowConditionalSearchState': 'v0to10VoltInput5LowConditionalSearchState',
            'owsv0to10VoltInput5Maximum': 'v0to10VoltInput5Maximum',
            'owsv0to10VoltInput5Minimum': 'v0to10VoltInput5Minimum',
            'owsv0to10VoltInput6HighAlarmState': 'v0to10VoltInput6HighAlarmState',
            'owsv0to10VoltInput6HighAlarmValue': 'v0to10VoltInput6HighAlarmValue',
            'owsv0to10VoltInput6HighConditionalSearchState': 'v0to10VoltInput6HighConditionalSearchState',
            'owsv0to10VoltInput6Instant': 'v0to10VoltInput6Instant',
            'owsv0to10VoltInput6LowAlarmState': 'v0to10VoltInput6LowAlarmState',
            'owsv0to10VoltInput6LowAlarmValue': 'v0to10VoltInput6LowAlarmValue',
            'owsv0to10VoltInput6LowConditionalSearchState': 'v0to10VoltInput6LowConditionalSearchState',
            'owsv0to10VoltInput6Maximum': 'v0to10VoltInput6Maximum',
            'owsv0to10VoltInput6Minimum': 'v0to10VoltInput6Minimum',
            'owsv0to10VoltInput7HighAlarmState': 'v0to10VoltInput7HighAlarmState',
            'owsv0to10VoltInput7HighAlarmValue': 'v0to10VoltInput7HighAlarmValue',
            'owsv0to10VoltInput7HighConditionalSearchState': 'v0to10VoltInput7HighConditionalSearchState',
            'owsv0to10VoltInput7Instant': 'v0to10VoltInput7Instant',
            'owsv0to10VoltInput7LowAlarmState': 'v0to10VoltInput7LowAlarmState',
            'owsv0to10VoltInput7LowAlarmValue': 'v0to10VoltInput7LowAlarmValue',
            'owsv0to10VoltInput7LowConditionalSearchState': 'v0to10VoltInput7LowConditionalSearchState',
            'owsv0to10VoltInput7Maximum': 'v0to10VoltInput7Maximum',
            'owsv0to10VoltInput7Minimum': 'v0to10VoltInput7Minimum',
            'owsv0to10VoltInput8HighAlarmState': 'v0to10VoltInput8HighAlarmState',
            'owsv0to10VoltInput8HighAlarmValue': 'v0to10VoltInput8HighAlarmValue',
            'owsv0to10VoltInput8HighConditionalSearchState': 'v0to10VoltInput8HighConditionalSearchState',
            'owsv0to10VoltInput8Instant': 'v0to10VoltInput8Instant',
            'owsv0to10VoltInput8LowAlarmState': 'v0to10VoltInput8LowAlarmState',
            'owsv0to10VoltInput8LowAlarmValue': 'v0to10VoltInput8LowAlarmValue',
            'owsv0to10VoltInput8LowConditionalSearchState': 'v0to10VoltInput8LowConditionalSearchState',
            'owsv0to10VoltInput8Maximum': 'v0to10VoltInput8Maximum',
            'owsv0to10VoltInput8Minimum': 'v0to10VoltInput8Minimum',
            'owsVersion': 'Version'
        }

        return eds0082_state_dict

    @staticmethod
    def eds0083_state_dict():
        """
        Title Placeholder

        Body placeholder
        """

        eds0083_state_dict = {
            'owsChannel': 'Channel',
            'owsClearAlarms': 'ClearAlarms',
            'owsCounter': 'Counter',
            'owsFamily': 'Family',
            'owsHealth': 'Health',
            'owsLED': 'LED',
            'owsLEDFunction': 'LEDFunction',
            'owsLEDState': 'LEDState',
            'owsPrimaryValue': 'PrimaryValue',
            'owsRawData': 'RawData',
            'owsRelay': 'Relay',
            'owsRelayFunction': 'RelayFunction',
            'owsRelayState': 'RelayState',
            'owsRomID': 'ROMId',
            'owsType': 'Name',
            'owsv4to20mAInput1HighAlarmState': 'v4to20mAInput1HighAlarmState',
            'owsv4to20mAInput1HighAlarmValue': 'v4to20mAInput1HighAlarmValue',
            'owsv4to20mAInput1HighConditionalSearchState': 'v4to20mAInput1HighConditionalSearchState',
            'owsv4to20mAInput1Instant': 'v4to20mAInput1Instant',
            'owsv4to20mAInput1LowAlarmState': 'v4to20mAInput1LowAlarmState',
            'owsv4to20mAInput1LowAlarmValue': 'v4to20mAInput1LowAlarmValue',
            'owsv4to20mAInput1LowConditionalSearchState': 'v4to20mAInput1LowConditionalSearchState',
            'owsv4to20mAInput1Maximum': 'v4to20mAInput1Maximum',
            'owsv4to20mAInput1Minimum': 'v4to20mAInput1Minimum',
            'owsv4to20mAInput2HighAlarmState': 'v4to20mAInput2HighAlarmState',
            'owsv4to20mAInput2HighAlarmValue': 'v4to20mAInput2HighAlarmValue',
            'owsv4to20mAInput2HighConditionalSearchState': 'v4to20mAInput2HighConditionalSearchState',
            'owsv4to20mAInput2Instant': 'v4to20mAInput2Instant',
            'owsv4to20mAInput2LowAlarmState': 'v4to20mAInput2LowAlarmState',
            'owsv4to20mAInput2LowAlarmValue': 'v4to20mAInput2LowAlarmValue',
            'owsv4to20mAInput2LowConditionalSearchState': 'v4to20mAInput2LowConditionalSearchState',
            'owsv4to20mAInput2Maximum': 'v4to20mAInput2Maximum',
            'owsv4to20mAInput2Minimum': 'v4to20mAInput2Minimum',
            'owsv4to20mAInput3HighAlarmState': 'v4to20mAInput3HighAlarmState',
            'owsv4to20mAInput3HighAlarmValue': 'v4to20mAInput3HighAlarmValue',
            'owsv4to20mAInput3HighConditionalSearchState': 'v4to20mAInput3HighConditionalSearchState',
            'owsv4to20mAInput3Instant': 'v4to20mAInput3Instant',
            'owsv4to20mAInput3LowAlarmState': 'v4to20mAInput3LowAlarmState',
            'owsv4to20mAInput3LowAlarmValue': 'v4to20mAInput3LowAlarmValue',
            'owsv4to20mAInput3LowConditionalSearchState': 'v4to20mAInput3LowConditionalSearchState',
            'owsv4to20mAInput3Maximum': 'v4to20mAInput3Maximum',
            'owsv4to20mAInput3Minimum': 'v4to20mAInput3Minimum',
            'owsv4to20mAInput4HighAlarmState': 'v4to20mAInput4HighAlarmState',
            'owsv4to20mAInput4HighAlarmValue': 'v4to20mAInput4HighAlarmValue',
            'owsv4to20mAInput4HighConditionalSearchState': 'v4to20mAInput4HighConditionalSearchState',
            'owsv4to20mAInput4Instant': 'v4to20mAInput4Instant',
            'owsv4to20mAInput4LowAlarmState': 'v4to20mAInput4LowAlarmState',
            'owsv4to20mAInput4LowAlarmValue': 'v4to20mAInput4LowAlarmValue',
            'owsv4to20mAInput4LowConditionalSearchState': 'v4to20mAInput4LowConditionalSearchState',
            'owsv4to20mAInput4Maximum': 'v4to20mAInput4Maximum',
            'owsv4to20mAInput4Minimum': 'v4to20mAInput4Minimum',
            'owsVersion': 'Version',
        }

        return eds0083_state_dict

    @staticmethod
    def eds0085_state_dict():
        """
        Title Placeholder

        Body placeholder
        """

        eds0085_state_dict = {
            'owsChannel': 'Channel',
            'owsClearAlarms': 'ClearAlarms',
            'owsCounter': 'Counter',
            'owsFamily': 'Family',
            'owsHealth': 'Health',
            'owsLED': 'LED',
            'owsLEDFunction': 'LEDFunction',
            'owsLEDState': 'LEDState',
            'owsPrimaryValue': 'PrimaryValue',
            'owsRawData': 'RawData',
            'owsRelay': 'Relay',
            'owsRelayFunction': 'RelayFunction',
            'owsRelayState': 'RelayState',
            'owsRomID': 'ROMId',
            'owsType': 'Name',
            'owsv0to10VoltInput1HighAlarmState': 'v0to10VoltInput1HighAlarmState',
            'owsv0to10VoltInput1HighAlarmValue': 'v0to10VoltInput1HighAlarmValue',
            'owsv0to10VoltInput1HighConditionalSearchState': 'v0to10VoltInput1HighConditionalSearchState',
            'owsv0to10VoltInput1Instant': 'v0to10VoltInput1Instant',
            'owsv0to10VoltInput1LowAlarmState': 'v0to10VoltInput1LowAlarmState',
            'owsv0to10VoltInput1LowAlarmValue': 'v0to10VoltInput1LowAlarmValue',
            'owsv0to10VoltInput1LowConditionalSearchState': 'v0to10VoltInput1LowConditionalSearchState',
            'owsv0to10VoltInput1Maximum': 'v0to10VoltInput1Maximum',
            'owsv0to10VoltInput1Minimum': 'v0to10VoltInput1Minimum',
            'owsv0to10VoltInput2HighAlarmState': 'v0to10VoltInput2HighAlarmState',
            'owsv0to10VoltInput2HighAlarmValue': 'v0to10VoltInput2HighAlarmValue',
            'owsv0to10VoltInput2HighConditionalSearchState': 'v0to10VoltInput2HighConditionalSearchState',
            'owsv0to10VoltInput2Instant': 'v0to10VoltInput2Instant',
            'owsv0to10VoltInput2LowAlarmState': 'v0to10VoltInput2LowAlarmState',
            'owsv0to10VoltInput2LowAlarmValue': 'v0to10VoltInput2LowAlarmValue',
            'owsv0to10VoltInput2LowConditionalSearchState': 'v0to10VoltInput2LowConditionalSearchState',
            'owsv0to10VoltInput2Maximum': 'v0to10VoltInput2Maximum',
            'owsv0to10VoltInput2Minimum': 'v0to10VoltInput2Minimum',
            'owsv0to10VoltInput3HighAlarmState': 'v0to10VoltInput3HighAlarmState',
            'owsv0to10VoltInput3HighAlarmValue': 'v0to10VoltInput3HighAlarmValue',
            'owsv0to10VoltInput3HighConditionalSearchState': 'v0to10VoltInput3HighConditionalSearchState',
            'owsv0to10VoltInput3Instant': 'v0to10VoltInput3Instant',
            'owsv0to10VoltInput3LowAlarmState': 'v0to10VoltInput3LowAlarmState',
            'owsv0to10VoltInput3LowAlarmValue': 'v0to10VoltInput3LowAlarmValue',
            'owsv0to10VoltInput3LowConditionalSearchState': 'v0to10VoltInput3LowConditionalSearchState',
            'owsv0to10VoltInput3Maximum': 'v0to10VoltInput3Maximum',
            'owsv0to10VoltInput3Minimum': 'v0to10VoltInput3Minimum',
            'owsv0to10VoltInput4HighAlarmState': 'v0to10VoltInput4HighAlarmState',
            'owsv0to10VoltInput4HighAlarmValue': 'v0to10VoltInput4HighAlarmValue',
            'owsv0to10VoltInput4HighConditionalSearchState': 'v0to10VoltInput4HighConditionalSearchState',
            'owsv0to10VoltInput4Instant': 'v0to10VoltInput4Instant',
            'owsv0to10VoltInput4LowAlarmState': 'v0to10VoltInput4LowAlarmState',
            'owsv0to10VoltInput4LowAlarmValue': 'v0to10VoltInput4LowAlarmValue',
            'owsv0to10VoltInput4LowConditionalSearchState': 'v0to10VoltInput4LowConditionalSearchState',
            'owsv0to10VoltInput4Maximum': 'v0to10VoltInput4Maximum',
            'owsv0to10VoltInput4Minimum': 'v0to10VoltInput4Minimum',
            'owsVersion': 'Version',
        }

        return eds0085_state_dict

    @staticmethod
    def eds0090_state_dict():
        """
        Title Placeholder

        Body placeholder
        """

        eds0090_state_dict = {
                'owsChannel': 'Channel',
                'owsClearAlarms': 'ClearAlarms',
                'owsCounter': 'Counter',
                'owsDiscreteIO1ActivityLatch': 'DiscreteIO1ActivityLatch',
                'owsDiscreteIO1ActivityLatchReset': 'DiscreteIO1ActivityLatchReset',
                'owsDiscreteIO1HighAlarmState': 'DiscreteIO1HighAlarmState',
                'owsDiscreteIO1HighAlarmValue': 'DiscreteIO1HighAlarmValue',
                'owsDiscreteIO1HighConditionalSearchState': 'DiscreteIO1HighConditionalSearchState',
                'owsDiscreteIO1InputState': 'DiscreteIO1InputState',
                'owsDiscreteIO1LowAlarmState': 'DiscreteIO1LowAlarmState',
                'owsDiscreteIO1LowAlarmValue': 'DiscreteIO1LowAlarmValue',
                'owsDiscreteIO1LowConditionalSearchState': 'DiscreteIO1LowConditionalSearchState',
                'owsDiscreteIO1OutputState': 'DiscreteIO1OutputState',
                'owsDiscreteIO1OutputValue': 'DiscreteIO1OutputValue',
                'owsDiscreteIO1PulldownState': 'DiscreteIO1PulldownState',
                'owsDiscreteIO1PulldownValue': 'DiscreteIO1PulldownValue',
                'owsDiscreteIO1PulseCounter': 'DiscreteIO1PulseCounter',
                'owsDiscreteIO1PulseCounterReset': 'DiscreteIO1PulseCounterReset',
                'owsDiscreteIO2ActivityLatch': 'DiscreteIO2ActivityLatch',
                'owsDiscreteIO2ActivityLatchReset': 'DiscreteIO2ActivityLatchReset',
                'owsDiscreteIO2HighAlarmState': 'DiscreteIO2HighAlarmState',
                'owsDiscreteIO2HighAlarmValue': 'DiscreteIO2HighAlarmValue',
                'owsDiscreteIO2HighConditionalSearchState': 'DiscreteIO2HighConditionalSearchState',
                'owsDiscreteIO2InputState': 'DiscreteIO2InputState',
                'owsDiscreteIO2LowAlarmState': 'DiscreteIO2LowAlarmState',
                'owsDiscreteIO2LowAlarmValue': 'DiscreteIO2LowAlarmValue',
                'owsDiscreteIO2LowConditionalSearchState': 'DiscreteIO2LowConditionalSearchState',
                'owsDiscreteIO2OutputState': 'DiscreteIO2OutputState',
                'owsDiscreteIO2OutputValue': 'DiscreteIO2OutputValue',
                'owsDiscreteIO2PulldownState': 'DiscreteIO2PulldownState',
                'owsDiscreteIO2PulldownValue': 'DiscreteIO2PulldownValue',
                'owsDiscreteIO2PulseCounter': 'DiscreteIO2PulseCounter',
                'owsDiscreteIO2PulseCounterReset': 'DiscreteIO2PulseCounterReset',
                'owsDiscreteIO3ActivityLatch': 'DiscreteIO3ActivityLatch',
                'owsDiscreteIO3ActivityLatchReset': 'DiscreteIO3ActivityLatchReset',
                'owsDiscreteIO3HighAlarmState': 'DiscreteIO3HighAlarmState',
                'owsDiscreteIO3HighAlarmValue': 'DiscreteIO3HighAlarmValue',
                'owsDiscreteIO3HighConditionalSearchState': 'DiscreteIO3HighConditionalSearchState',
                'owsDiscreteIO3InputState': 'DiscreteIO3InputState',
                'owsDiscreteIO3LowAlarmState': 'DiscreteIO3LowAlarmState',
                'owsDiscreteIO3LowAlarmValue': 'DiscreteIO3LowAlarmValue',
                'owsDiscreteIO3LowConditionalSearchState': 'DiscreteIO3LowConditionalSearchState',
                'owsDiscreteIO3OutputState': 'DiscreteIO3OutputState',
                'owsDiscreteIO3OutputValue': 'DiscreteIO3OutputValue',
                'owsDiscreteIO3PulldownState': 'DiscreteIO3PulldownState',
                'owsDiscreteIO3PulldownValue': 'DiscreteIO3PulldownValue',
                'owsDiscreteIO4ActivityLatch': 'DiscreteIO4ActivityLatch',
                'owsDiscreteIO4ActivityLatchReset': 'DiscreteIO4ActivityLatchReset',
                'owsDiscreteIO4HighAlarmState': 'DiscreteIO4HighAlarmState',
                'owsDiscreteIO4HighAlarmValue': 'DiscreteIO4HighAlarmValue',
                'owsDiscreteIO4HighConditionalSearchState': 'DiscreteIO4HighConditionalSearchState',
                'owsDiscreteIO4InputState': 'DiscreteIO4InputState',
                'owsDiscreteIO4LowAlarmState': 'DiscreteIO4LowAlarmState',
                'owsDiscreteIO4LowAlarmValue': 'DiscreteIO4LowAlarmValue',
                'owsDiscreteIO4LowConditionalSearchState': 'DiscreteIO4LowConditionalSearchState',
                'owsDiscreteIO4OutputState': 'DiscreteIO4OutputState',
                'owsDiscreteIO4OutputValue': 'DiscreteIO4OutputValue',
                'owsDiscreteIO4PulldownState': 'DiscreteIO4PulldownState',
                'owsDiscreteIO4PulldownValue': 'DiscreteIO4PulldownValue',
                'owsDiscreteIO5ActivityLatch': 'DiscreteIO5ActivityLatch',
                'owsDiscreteIO5ActivityLatchReset': 'DiscreteIO5ActivityLatchReset',
                'owsDiscreteIO5HighAlarmState': 'DiscreteIO5HighAlarmState',
                'owsDiscreteIO5HighAlarmValue': 'DiscreteIO5HighAlarmValue',
                'owsDiscreteIO5HighConditionalSearchState': 'DiscreteIO5HighConditionalSearchState',
                'owsDiscreteIO5InputState': 'DiscreteIO5InputState',
                'owsDiscreteIO5LowAlarmState': 'DiscreteIO5LowAlarmState',
                'owsDiscreteIO5LowAlarmValue': 'DiscreteIO5LowAlarmValue',
                'owsDiscreteIO5LowConditionalSearchState': 'DiscreteIO5LowConditionalSearchState',
                'owsDiscreteIO5OutputState': 'DiscreteIO5OutputState',
                'owsDiscreteIO5OutputValue': 'DiscreteIO5OutputValue',
                'owsDiscreteIO5PulldownState': 'DiscreteIO5PulldownState',
                'owsDiscreteIO5PulldownValue': 'DiscreteIO5PulldownValue',
                'owsDiscreteIO6ActivityLatch': 'DiscreteIO6ActivityLatch',
                'owsDiscreteIO6ActivityLatchReset': 'DiscreteIO6ActivityLatchReset',
                'owsDiscreteIO6HighAlarmState': 'DiscreteIO6HighAlarmState',
                'owsDiscreteIO6HighAlarmValue': 'DiscreteIO6HighAlarmValue',
                'owsDiscreteIO6HighConditionalSearchState': 'DiscreteIO6HighConditionalSearchState',
                'owsDiscreteIO6InputState': 'DiscreteIO6InputState',
                'owsDiscreteIO6LowAlarmState': 'DiscreteIO6LowAlarmState',
                'owsDiscreteIO6LowAlarmValue': 'DiscreteIO6LowAlarmValue',
                'owsDiscreteIO6LowConditionalSearchState': 'DiscreteIO6LowConditionalSearchState',
                'owsDiscreteIO6OutputState': 'DiscreteIO6OutputState',
                'owsDiscreteIO6OutputValue': 'DiscreteIO6OutputValue',
                'owsDiscreteIO6PulldownState': 'DiscreteIO6PulldownState',
                'owsDiscreteIO6PulldownValue': 'DiscreteIO6PulldownValue',
                'owsDiscreteIO7ActivityLatch': 'DiscreteIO7ActivityLatch',
                'owsDiscreteIO7ActivityLatchReset': 'DiscreteIO7ActivityLatchReset',
                'owsDiscreteIO7HighAlarmState': 'DiscreteIO7HighAlarmState',
                'owsDiscreteIO7HighAlarmValue': 'DiscreteIO7HighAlarmValue',
                'owsDiscreteIO7HighConditionalSearchState': 'DiscreteIO7HighConditionalSearchState',
                'owsDiscreteIO7InputState': 'DiscreteIO7InputState',
                'owsDiscreteIO7LowAlarmState': 'DiscreteIO7LowAlarmState',
                'owsDiscreteIO7LowAlarmValue': 'DiscreteIO7LowAlarmValue',
                'owsDiscreteIO7LowConditionalSearchState': 'DiscreteIO7LowConditionalSearchState',
                'owsDiscreteIO7OutputState': 'DiscreteIO7OutputState',
                'owsDiscreteIO7OutputValue': 'DiscreteIO7OutputValue',
                'owsDiscreteIO7PulldownState': 'DiscreteIO7PulldownState',
                'owsDiscreteIO7PulldownValue': 'DiscreteIO7PulldownValue',
                'owsDiscreteIO8ActivityLatch': 'DiscreteIO8ActivityLatch',
                'owsDiscreteIO8ActivityLatchReset': 'DiscreteIO8ActivityLatchReset',
                'owsDiscreteIO8HighAlarmState': 'DiscreteIO8HighAlarmState',
                'owsDiscreteIO8HighAlarmValue': 'DiscreteIO8HighAlarmValue',
                'owsDiscreteIO8HighConditionalSearchState': 'DiscreteIO8HighConditionalSearchState',
                'owsDiscreteIO8InputState': 'DiscreteIO8InputState',
                'owsDiscreteIO8LowAlarmState': 'DiscreteIO8LowAlarmState',
                'owsDiscreteIO8LowAlarmValue': 'DiscreteIO8LowAlarmValue',
                'owsDiscreteIO8LowConditionalSearchState': 'DiscreteIO8LowConditionalSearchState',
                'owsDiscreteIO8OutputState': 'DiscreteIO8OutputState',
                'owsDiscreteIO8OutputValue': 'DiscreteIO8OutputValue',
                'owsDiscreteIO8PulldownState': 'DiscreteIO8PulldownState',
                'owsDiscreteIO8PulldownValue': 'DiscreteIO8PulldownValue',
                'owsFamily': 'Family',
                'owsHealth': 'Health',
                'owsLED': 'LED',
                'owsLEDFunction': 'LEDFunction',
                'owsLEDState': 'LEDState',
                'owsPrimaryValue': 'PrimaryValue',
                'owsRawData': 'RawData',
                'owsRelay': 'Relay',
                'owsRelayFunction': 'RelayFunction',
                'owsRelayState': 'RelayState',
                'owsRomID': 'ROMId',
                'owsType': 'Name',
                'owsVersion': 'Version',
        }

        return eds0090_state_dict
