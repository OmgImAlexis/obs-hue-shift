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

# Settings
debug_mode = False
autostart = False
hue_velocity = 0.0  # Degrees per second
hue_shift = 0.0 # Angle of the hue shift (-180 to 180, but OBS seems to handle values outside of this range properly)
source_id = ""

# Local vars
active = False
timer_running = False
update_interval = 30  # Milliseconds

# In debug mode log messages
def debug(message):
    global debug_mode
    if debug_mode: print("ℹ️ " + message)

# Set defaults
def script_defaults(settings):
    debug("Setting defaults")
    obs.obs_data_set_default_double(settings, "hue_shift_velocity", 360.0)
    obs.obs_data_set_default_bool(settings, "autostart", False)
    obs.obs_data_set_default_bool(settings, "debug_mode", False)

# Set script's description
def script_description():
    return "Changes the Hue Shift property of a color correction filter over time." + \
           "The selected source must have a Color Correction filter renamed as \"Hue Shift\" for the effect to work." + \
           "Script with love by Hegemege, changes by OmgImAlexis"

# On script load
def script_load(settings):
    global autostart, active
    debug("Loaded Hue Shift")
    signal_handler = obs.obs_get_signal_handler()
    obs.signal_handler_connect(signal_handler, "source_activate", source_activated)
    obs.signal_handler_connect(signal_handler, "source_deactivate", source_deactivated)

    # Load settings
    script_update(settings)

    if autostart:
        active = True
        reload()

# Script was selected in the script window
def script_properties():
    debug('Hue Shift selected in script window')
    props = obs.obs_properties_create()

    # Add an input box for the hue shift velocity
    obs.obs_properties_add_float(props, "hue_shift_velocity", "Hue Shift Velocity", -10000, 10000, 0.1)

    # Add a list of all the sources
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
            id = obs.obs_source_get_id(source)
            name = obs.obs_source_get_name(source)
            obs.obs_property_list_add_string(source_prop, id, name)

    obs.source_list_release(sources)

    # Bind UI elements
    obs.obs_properties_add_button(props, "start_button", "Start", start_button_clicked)
    obs.obs_properties_add_button(props, "stop_button", "Stop", stop_button_clicked)
    obs.obs_properties_add_bool(props, "autostart_checkbox", "Autostart", autostart_checkbox_clicked)

    return props

# The settings will be saved here
def script_save(settings):
    debug("Saved settings.")
    script_update(settings)

# The script is being unloaded
def script_unload():
    global timer_running;
    
    # Remove timer
    if timer_running:
        print("🟥 Stopped hue shift timer.")
        obs.timer_remove(timer_callback)
        timer_running = False

    debug("Unloaded script.")

# Called when a setting changes
def script_update(settings):
    global debug_mode, autostart, hue_velocity, hue_shift, source_id
    debug("Updating settings.")

    # Update globals with new settings
    debug_mode = obs.obs_data_get_bool(settings, "debug_mode")
    autostart = obs.obs_data_get_bool(settings, "autostart")
    hue_velocity = obs.obs_data_get_double(settings, "hue_velocity")
    source_id = obs.obs_data_get_string(settings, "source_id")

    # Reset hue
    update_hue(True)

# Update the selected source's hue
def update_hue(reset=False):
    global source_id
    global hue_shift

    # If the update is called with reset intention, set the hue to normal (0)
    if reset:
        hue_shift = 0

    source = obs.obs_get_source_by_name(source_id)
    if source is not None:
        hue_filter = obs.obs_source_get_filter_by_name(source, "Hue Shift")
        if hue_filter is not None:
            # Get the settings data object for the filter
            filter_settings = obs.obs_source_get_settings(hue_filter)

            # Update the hue_shift property and update the filter with the new settings
            obs.obs_data_set_double(
                filter_settings,
                "hue_shift",
                hue_shift
            )
            obs.obs_source_update(hue_filter, filter_settings)

            # Release the resources
            obs.obs_data_release(filter_settings)
            obs.obs_source_release(hue_filter)

        obs.obs_source_release(source)

def timer_callback():
    global hue_shift
    global hue_velocity
    global update_interval

    # Update the hue_shift value. Velocity is degrees / second, update_interval is in milliseconds
    hue_shift += hue_velocity * update_interval / 1000
    hue_shift = hue_shift % 360

    update_hue()


# Either start or stop the timer
def reload():
    global timer_running
    global active
    global update_interval

    # Attempt to remove the old timer
    if timer_running:
        obs.timer_remove(timer_callback)
        timer_running = False

    if active:
        print("🟢 Started hue shift timer.")
        obs.timer_add(timer_callback, update_interval)
        timer_running = True
    else:
        if timer_running:
            print("🟥 Stopped hue shift timer.")
            obs.timer_remove(timer_callback)
            timer_running = False
        else:
            print("🔷 Hue was not running, skipping stop.")

def update_source(cd, state):
    global active
    global source_id

    # Get the current source
    source = obs.calldata_source(cd, "source")

    # If we have a source selected set the active state
    if source is not None:
        id = obs.obs_source_get_id(source)

        # If this source is our selected one then activate hue shift
        # Otherwise stop it
        if id == source_id:
            print("ℹ️ Setting our source to \"" + str(state) + "\".")
            active = state
            reload()
        else:
            print("ℹ️ Looking for " + source_id + " found " + id)

def start_button_clicked(props, p):
    print("ℹ️ Start button clicked")
    global active
    active = True
    reload()

def stop_button_clicked(props, p):
    print("ℹ️ Stop button clicked")
    global active
    active = False
    reload()

def autostart_checkbox_clicked(props, p):
    global autostart
    print("ℹ️ Autostart checkbox clicked")
    # Flip autostart
    autostart = not autostart

def source_activated(cd):
    update_source(cd, True)

def source_deactivated(cd):
    update_source(cd, False)
