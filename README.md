/**
 * Sentinel: A Production Process Monitor
 * -- Documentation --
 * Ben Feeser
 * CS50 Spring 2015
 * Presentation: https://www.youtube.com/watch?v=6QSXkZZDsQM
 **/

In this file, I will document how to setup Sentinel on the Harvard appliance. All commands you need to run in the terminal are prefixed by "$".

First begin by unpacking Sentinel in the appliance into the /home/jharvard/vhosts directory:

$ cd ~/vhosts
$ unzip sentinel.zip

You should have a new folder as so: /home/jharvard/vhosts/sentinel

Let's update the permissions of all the files we just unzipped, assuming we are in the ~/vhosts/ directory:

$ chmod 711 sentinel/
$ chmod 711 sentinel/app
$ chmod 711 sentinel/app/templates/
$ chmod 711 sentinel/app/static/
$ chmod 711 sentinel/app/static/img
$ chmod 711 sentinel/app/static/js
$ chmod 711 sentinel/app/static/css
$ chmod 711 sentinel/app/static/fonts
$ chmod 711 sentinel/logs/
$ chmod 700 sentinel/*.py
$ chmod 700 sentinel/app/*.py
$ chmod 644 sentinel/app/static/img/*
$ chmod 644 sentinel/app/static/js/*
$ chmod 644 sentinel/app/static/css/*
$ chmod 644 sentinel/app/static/fonts/*
$ chmod 644 sentinel/templates/*
$ chmod a+r sentinel/logs/*

$ cd ~/vhosts/sentinel/

Next, in the sentinel directory, using gedit open the sentinel.sql file.

$ gedit sentinel.sql

Open up Chrome and head to: "localhost/phpmyadmin". In the phpmyadmin page, login using the "jharvard" user and the password "crimson".

Once in PHPmyAdmin, click on the SQL scroll icon. Copy the SQL in gedit and paste it into the text area field in PHPmyAdmin and hit "Go". We have created the sentinel database.

Now we need to set up the job that will run and send our alerts. We will do this using "cron". In the sentinel directory, run this command:

$ crontab crontab.txt

This sets up the "crontab" which is a list of jobs for our boy, cron, to run and in this case, to run them on the minute, every minute. The job he is running is sentinel/app/alerts.py.  This python script finds alerts that are scheduled to run in the given minute, builds their HTML and sends them off. After a minute has passed, run this command:

$ tail -f logs/sentinel_alerts

You should be tailing alerts.py's log file, which confirms that alerts.py is successfully running. Press Ctrl+C to exit tailing the file.

In ~/vhosts/sentinel/ directory run:

$ ./run.py

This is the command that start's sentinel's Flask webserver. Now, open up Chrome and head to "localhost:5000". You should see Sentinel's home page.

Click the button "Register". Fill in your email, password, and confirmation. Now, to further confirm your credentials, login again.

You should now arrive at Sentinel's index page, which is also the "Processes" page. The drop downs for "Host" and "User" are to be used to  select the host and user that the Sentinel app is running on. In this case, Sentinel is only configured for use on the appliance.

Next, we have the "Search" field. You can use this field to filter results in the "Processes", "Logs", and "Patterns" pages. After five seconds, processes should begin popping up in your screen. This is showing you showing what is running on your appliance. Search for our Flask server by typing "flask" into the search field.

Next, click on the "Logs" tab in the navigation bar. Be sure to expand your appliance/browser so that you can view all of the navigation tabs. Here you will see a new field to select a "Path". This "Path" is a preconfigured path ("/home/jharvard/vhosts/sentinel/logs/") that allows users to search the logs in that directory. Next, are the "Name" and "Pattern" fields, which allow you respectively to name and to create a pattern, which is Sentinel's name for a REGEX query.

Type "error" into the Pattern field. Hit Submit. You should see results populate in the table below.

Results that had matches to the REGEX pattern "error" will have green buttons that say "Match". Click on a "Match" button. A modal will pop up showing all the lines in the file that matched your pattern. If you click on the file name in the "Log" column of the table, a modal will pop up showing the entire log file.

Let's save this pattern. Fill out "Name" with "Log Errors". Hit "Save".

Now, let's go to the Patterns page. Click on "Patterns" in the navigation bar. You should see your new pattern, "Log Errors", listed there. You'll see it has no "Schedule Days" or "Schedule Time".

Let's schedule an email alert for this pattern. Click on "Log Errors" in the "Name" column. This will link you back to the pattern in the "Logs" page, where you can update this pattern.

Next, hit the "Schedule" button to have a scheduling tool in a modal pop up. Put your email in the "Recipients" field. Schedule the alert for today using the checkboxes under "Days". Finally, set the "Time" to be a few minutes from the current time. Hit "Close" or click outside of the modal to exit the modal. Hit "Save".

Now click on "Patterns" in the navigation bar. You should see that your pattern successfully updated and now has a "Recipient", "Scheduled Days", and a "Scheduled Time". About now, your alert should be arriving to your inbox. Take a look.

If it has not come in yet, check your appliance's current time (mine is 23 hours behind). If you need to check, run:

$ date

We've just decided we're tired of this alert. Click on the "Log Errors" in the "Name" column of the "Patterns" page. We're linked back to the same pattern in the "Logs" page to update it or delete it. Let's delete it. Hit "Delete". Hit "Delete" again. Too bad, it seems you can't delete it more than once.

Next, create more patterns, update them, delete them, and schedule them. Watch your inbox or others' inboxes fill up. Watch some processes in the "Processes" tab. When you've finished, hit "Logout".

That covers the current functionality of Sentinel, a production process monitor.
