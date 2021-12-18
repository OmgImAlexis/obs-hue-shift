# How to use this script in OBS:
# You need Python 3.6 installed
# 1. Open OBS > Tools > Scripts
# 2. Copypaste the Python 3.6 install directory into Python Settings tab.
# 3. Download this file onto your computer and put it somewhere safe
# 4. Add the script to the list of Loaded Scripts by clicking the + at the bottom left
# 5. Select the script from the list and select the correct output source you want to apply the effect to.
#       If you can't find the correct source, scroll to the bottom of the file to see if your source is filtered out
#       The source you selected must have a Color Correction filter, that has been renamed to "Hue Shift".
#           The script won't work otherwise. I couldn't figure out how to list all the filters in a dropdown because 
#           OBS' documentation on C types in Python are poor.
# 6. Set your desired effect velocity (360 = 1 rainbow per second)
# 7. Click Start / Stop
# The script comes as-is and hasn't been tested for long periods of time for memory leaks etc
#
# The code is released under the MIT license.

import obspython as obs

active = False

hue_velocity = 0.0  # Degrees per second

# Angle of the hue shift (-180 to 180, but OBS seems to handle values outside of this range properly)
hue_shift_value = 0.0

source_name = ""
update_interval = 30  # Milliseconds


def update_hue(reset=False):
    global source_name
    global hue_shift_value

    # If the update is called with reset intention, set the hue to normal (0)
    if reset:
        hue_shift_value = 0

    source = obs.obs_get_source_by_name(source_name)
    if source is not None:
        hue_filter = obs.obs_source_get_filter_by_name(source, "Hue Shift")
        if hue_filter is not None:
            # Get the settings data object for the filter
            filter_settings = obs.obs_source_get_settings(hue_filter)

            # Update the hue_shift property and update the filter with the new settings
            obs.obs_data_set_double(
                filter_settings,
                "hue_shift",
                hue_shift_value
            )
            obs.obs_source_update(hue_filter, filter_settings)

            # Release the resources
            obs.obs_data_release(filter_settings)
            obs.obs_source_release(hue_filter)

        obs.obs_source_release(source)


def timer_callback():
    global hue_shift_value
    global hue_velocity
    global update_interval

    # Update the hue_shift value. Velocity is degrees / second, update_interval is in milliseconds
    hue_shift_value += hue_velocity * update_interval / 1000
    hue_shift_value = hue_shift_value % 360
    update_hue()


def activate():
    global active
    global update_interval

    if active:
        obs.timer_add(timer_callback, update_interval)
    else:
        obs.timer_remove(timer_callback)


def start_button_clicked(props, p):
    global active

    active = not active
    if not active:
        update_hue(True)

    activate()


def activate_signal(cd):
    global source_name

    source = obs.calldata_source(cd, "source")
    if source is not None:
        name = obs.obs_source_get_name(source)
        if name == source_name:
            activate()


def source_activated(cd):
    activate_signal(cd)


def source_deactivated(cd):
    activate_signal(cd)


def script_load(settings):
    sh = obs.obs_get_signal_handler()
    obs.signal_handler_connect(sh, "source_activate", source_activated)
    obs.signal_handler_connect(sh, "source_deactivate", source_deactivated)


def script_description():
    return '''Changes the Hue Shift property of a color correction filter over time
    
The selected source must have a Color Correction filter renamed as "Hue Shift" for the effect to work.
Script with love by Hegemege'''


def script_update(settings):
    global hue_velocity
    global source_name
    global hue_shift_value

    hue_velocity = obs.obs_data_get_double(settings, "hue_shift_velocity")
    source_name = obs.obs_data_get_string(settings, "source")
    hue_shift_value = 0

    update_hue(True)


def script_defaults(settings):
    obs.obs_data_set_default_double(settings, "hue_shift_velocity", 360.0)


def script_properties():
    props = obs.obs_properties_create()
    obs.obs_properties_add_float(
        props, "hue_shift_velocity", "Hue Shift Velocity", -10000, 10000, 0.1)

    source_prop = obs.obs_properties_add_list(
        props,
        "source",
        "Source",
        obs.OBS_COMBO_TYPE_EDITABLE,
        obs.OBS_COMBO_FORMAT_STRING
    )
    sources = obs.obs_enum_sources()
    if sources is not None:
        for source in sources:
            source_id = obs.obs_source_get_id(source)
            
            # Only list sources with 'capture' in the name. 
            # To list all sources, remove the if and de-indent the two lines below it or replace the row with 'if True:' if you are not a rpogrammer)
            if 'capture' in source_id:
                name = obs.obs_source_get_name(source)
                obs.obs_property_list_add_string(source_prop, name, name)
    obs.source_list_release(sources)

    obs.obs_properties_add_button(
        props, "reset_button", "Start / Stop", start_button_clicked)

    return props