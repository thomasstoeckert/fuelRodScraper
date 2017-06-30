About FuelRodScraper.py
=========================
FuelRodScraper.py is the scraper for finding updated
Fuel Rod Kiosk locations at Walt Disney World and Disneyland.
One app that uses this is [here,](http://github.com/thomasstoeckert/fuelRodLocator)
an app to display the neaest location of a kiosk on Pebble Smartwatches.

How does it work?
---------------
FuelRodScraper uses PyVirtualDisplay, Selenium, and Firefox to load and render
the map webpages that Disney uses, then it uses xpaths to find and dissect the
webpage for the coordinates and names. After combining it all together, it sends
it to my webserver, which hosts the files for any of my apps.

Why doesn't it work on my machine?
--------------
* This was developed on the Windows Subsystem for Linux (wsl) and as such
it may have issues running on native linux builds. I had severe difficulty getting
it to run on a raspberry pi, mostly due to firefox and selenium behaving poorly.
* It requires [geckodriver](https://github.com/mozilla/geckodriver/releases) 
for your particular operating system to be in the operating directory or in your system path.
* it uses a public/private key system to make sure the files being sent to the server
only come from me. As such, this requires a private RSA key in 'private_key.txt' to operate.
* I've removed the URL to my webserver, and as such, it'll fail during sending. 

If you'd like access to the webserver API, contact me using the contact information on my
github account.