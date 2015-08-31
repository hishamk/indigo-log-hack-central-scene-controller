# Indigo 6 Log File Hack to Utilize Unsupported Central Scene Z-Wave Controllers

First off, this is a real quick and dirty hack. I came up with this today as I'm in the possession of a pretty neat 8-button central scene Z-Wave controller. Unfortunately, it's not supported by Indigo 6.

The way this works is that it monitors the Z-Wave debug writes to the log for central scene controllers, and issues Indigo 6 REST API requests against those.


**The BAD**

It uses polling! I'll probably switch to some OS file change monitoring. pyinotify is not yet available for OS X.

It's a dirty HACK (albeit a tame one tapping into the log files).

I've only tested this 20 mins prior to pushing this repo. So YMMV.

**The GOOD**

There are some pretty neat looking central scene controllers released at CES 2015. You can use them... today!


**USAGE**

Make sure Indigo server is running and authentication is enabled.

Indigo needs to be setup to save Z-Wave debug info to the log file.

Do this by selecting 'Show debug logging of interface communication' in Configure Z-Wave.

Open the event log window and click 'Show Event Logs Folder'.

Note the path of the indigo_log.txt shortcut.

In csc.py change the path if needed (you most likely will not need to).

Change the user and password as needed. You may want to change the host and port if they're different on your setup. 

The core of the setup is in the setup_controllers() function. See the example setup. It's pretty straightforward:

Note that all numbers (written as literal two character strings as provided by the logs) are hexadecimal. That means anything above 9 would not be simply 10. So if your device or button number is 10, that would be '0A'. I'll probably change this to use decimal, but for now, you can refer to http://ascii.cl/conversion.htm if you get confused.

```sh
controller = EightButtonController('03') #Setup a new controller with device is 3. You must use '03' as in literal strings. I didn't bother to change this just yet.
```

Then bind the actions needed:
```sh
controller.addSingleClickActionMapping('07', 'All Kitchen Lights On') #Again, a literal '07', this time for the button number. This is followed by the Action Group title as defined in Indigo.
controller.addDoubleClickActionMapping('07', 'All Kitchen Lights Off') #Suggest you use the double click to 'reverse'/toggle single click actions.

controller.addHoldButtonDimmerMapping('05', 'Counter Lights')  #'Counter Lights' is the device name. The hold button action does not execute Action Groups, rather it's for dimming lights (up).
```

Finally, make sure you update the controllers to use by including their ids in run_loop:
```sh
get_last_controller_events(10, ['03', '05',]).
```

**TO-DO**
Saner dimming (down as well for a start).


**REQUIREMENTS**
Python 2.7.x
requests module

