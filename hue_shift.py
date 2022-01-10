# How to use this script in OBS:
#
# Checklist:
# 1. OBS
# 2. Python 3.6 (https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe)
#
#
# Adding the script:
# 1. Open OBS > Tools > Scripts
# 2. Start menu > type "cmd" > click command prompt > type "py --list-paths" > Take note of the line starting with "-3.6-64"
# 3. Copy+paste the directory(something like C:\Users\my_username\AppData\Local\Programs\Python\Python36\python.exe) from step 2 into the "Python Settings" tab
# 4. Download this file onto your computer and put it somewhere safe (If this page looks like a website look for the "Raw" button before saving this file)
# 5. In OBS with the scripts windows still open click the + at the bottom left and select this file that you just downloaded
# 6. Select the "Hue Shift" from the list and select the correct output source you want to apply the effect to
#    NOTE: The source you selected must have a Color Correction filter that has been renamed to "Hue Shift"
# 7. Set your desired effect velocity (360 = 1 rainbow per second)
# 8. Click Start / Stop

import obspython as obs

# Settings
debug_mode = False
autostart = False
hue_velocity = 0.0  # Degrees per second
hue_shift = 0.0 # Angle of the hue shift (-180 to 180, but OBS seems to handle values outside of this range properly)
source_name = ""

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
        debug('Hue Shift autostart is enabled, starting...')
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
            name = obs.obs_source_get_name(source)
            obs.obs_property_list_add_string(source_prop, name, name)

    obs.source_list_release(sources)

    # Bind UI elements
    obs.obs_properties_add_button(props, "start_button", "Start", start_button_clicked)
    obs.obs_properties_add_button(props, "stop_button", "Stop", stop_button_clicked)
    obs.obs_properties_add_bool(props, "autostart", "Autostart")
    obs.obs_properties_add_bool(props, "debug_mode", "Debug mode?")

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
    global debug_mode, autostart, hue_shift_velocity, hue_shift, source_name
    debug("Updating settings.")

    # Update globals with new settings
    debug_mode = obs.obs_data_get_bool(settings, "debug_mode")
    autostart = obs.obs_data_get_bool(settings, "autostart")
    hue_shift_velocity = obs.obs_data_get_double(settings, "hue_shift_velocity")
    source_name = obs.obs_data_get_string(settings, "source")

    # Reset hue
    update_hue(True)

# Update the selected source's hue
def update_hue(reset=False):
    global source_name
    global hue_shift

    # If the update is called with reset intention, set the hue to normal (0)
    if reset:
        debug("Reset hue to 0")
        hue_shift = 0

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
                hue_shift
            )
            debug("Setting hue to " + str(hue_shift))
            obs.obs_source_update(hue_filter, filter_settings)

            # Release the resources
            obs.obs_data_release(filter_settings)
            obs.obs_source_release(hue_filter)

        # Release the resources
        obs.obs_source_release(source)

def timer_callback():
    global hue_shift
    global hue_shift_velocity
    global update_interval

    # Update the hue_shift value. Velocity is degrees / second, update_interval is in milliseconds
    hue_shift += hue_shift_velocity * (update_interval / 1000)
    hue_shift = hue_shift % 360

    update_hue()


# Either start or stop the timer
def reload():
    global timer_running
    global active
    global update_interval

    if active:
        # Attempt to remove the old timer
        if timer_running:
            print("🟥 Stopping old hue shift timer.")
            obs.timer_remove(timer_callback)
            timer_running = False

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
    global source_name

    # Get the current source
    source = obs.calldata_source(cd, "source")

    # If we have a source selected set the active state
    if source is not None:
        name = obs.obs_source_get_name(source)

        # If this source is our selected one then activate hue shift
        # Otherwise stop it
        if name == source_name:
            debug("ℹ️ Setting our source to \"" + str(state) + "\".")
            active = state
            reload()
        else:
            debug("ℹ️ Looking for " + source_name + " found " + name)

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

def source_activated(cd):
    update_source(cd, True)

def source_deactivated(cd):
    update_source(cd, False)