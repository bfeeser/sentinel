/**
 * Sentinel: A Production Process Monitor
 * -- Design -- 
 * Ben Feeser
 * CS50 Spring 2015 
 * Presentation: https://www.youtube.com/watch?v=6QSXkZZDsQM
 **/

In this file, I will describe my design of Sentinel. I will divide the document out by folder and by file, as deemed necessary.

/**
 * sentinel/
 */

-- run.py --

This file kicks off Sentinel's Flask server living in sentinel/app/. Atop this file is a shebang that points to the virtual environment folder, essentially telling the shell which Python interpreter (in this case, "flask/bin/python") to use.

Add the '--debug' option when calling run.py to run Sentinel in debug mode.

-- crontab.txt --

This crontab file is used to configure the crontab of the host that sentinel is running on. Right now, the only job in this file is one to run sentinel/app/alerts.py every minute. Using a crontab is key to allow asynchronous runs of our scheduled alerts -- this allows the web server to focus on web server related tasks while cron, can handle all of the jobs that can run in the background.

/**
 * sentinel/logs
 */

A directory of example logs from scripts outside Sentinel. These logs are used for testing Sentinel's REGEX pattern matching. Sentinel's own alerts.py writes to sentinel_alerts in this folder.

/**
 * sentinel/flask
 */

This directory contains the Python virtual environment that Sentinel uses. To avoid dependency hell (eg. never ending dependencies) and version specific dependencies, Python allows for each application to have its own "virtual environment" where it can run its own set of modules specific to that application. For example, if Sentinel required a newer version of Flask, it can have its own version in a self contained package and we need not update the version of Flask running in the appliance that other applications may depend on. In "requirements.txt", we have a "pip freeze", or a list, of all Python modules that are installed in the virtual environment.

/**
 * sentinel/app/
 */

-- __init__.py --

This file is the heart of Sentinel -- "__init__.py" Python files live in the base directory of Python modules and packages. They load all of the configuration and base modules that the package runs. In this case, Sentinel's __init__ connects to the database, starts the Flask-Login Mangager, and Flask-Bcrypt.

Flask-Login is a helpful library for managing user's cookies (also called sessions) and for telling whether or not a user is logged in. The Flask-Login Manager is configured to be set to the "login.html" view when users are not logged in.

Flask-Bcrypt module is used to run the "Blowfish" hashing algorithm on users' passwords to store them in our MySQL database. Flask-Bcrypt also checks users passwords without needing us to hash the provided password or provide the stored hashed password's salt, which is helpful.

-- config.py --

config.py contain's Sentinel's secrets. Here we can find the keys to "sentinel.alerts.sys@gmail.com", "jharvard"'s MySQL access, and related WTForm configuration. config.py also has a helper function to connect to the database -- "connect_db()" -- since the database configurations were in this file, it seemed best to keep them in the same place.

-- views.py --

views.py handles the rendering, routing, and resposes, to all of Sentinel's web requests. The "@app.route("here")" decorators, essentially say if someone wants to arrive "here" -- do this to process the request.

Flask's render_template function takes an HTML file in the templates directory and populates it with the provided WTForms, variables, messages, and more.

The render_logs() view is the most complex view, as it has to handle requests to load, save, update, and delete patterns. The first set of control flow handles loading a given pattern if a request argument (a URL parameter, eg. "pattern_id=10") is provided. 

To load a pattern, we build a pattern object, check if this pattern object exists and load all of the associated forms with that pattern object's data.

The next set of logic handles updates, saves, and deletes. If a pattern does not exist (it does not have a pattern_id provided) and the appropriate forms are filled out, a new pattern object is created when "Save" is hit.  If a pattern_id is provided on the "Save" request, the given pattern_id is updated. Finally, if a pattern_id is provided and "Delete" is hit, the pattern_id is deleted if it is owned by that user.

The next most complex view is the login view. Before every request, we set the "current_user" to "g.user". In the login view, we check if "g.user" is authenticated. If they are, we let them through. Otherwise, they must login.

If the login form is filled out successfully, a user object is attempted to be created. If that user object exists (the email provided links to a password and user_id), we check the given users' provided password against the saved password using Flask-BCrypt. If the "check_password_hash()" function returns True, we let the user through. Flask-Login Manager logs the user in and if the user object exists, it sets the new user object to "g.user", so that we can access this new "global" user in our other requests.

The other interesting views are /api/*. These "/api/" routings essentially accept paramaters and return JSON-ified output via request so that their output can be accepted by views or other functions. Bootstrap tables mainly consume their data.

-- models.py --

In this file, we have the definition of a user object and a pattern object. Sentinel's user object subclasses the UserMixin object so we need not waste time specifying all the attributes provided by the base class. Most importantly, upon initialization, this class gets all associated data with for a given user when provided an email, like so:

user = User('myemail@cs50.com')

This data can be accessed by indexing into the user object:

user.data['id']

Similarly, I found that an object like the User object would be useful for patterns. Thus, I wrote the pattern object, which also retrieves all information related to a given pattern when provided a pattern_id.  Additionally, the pattern model can create a new pattern and return itself via a classmethod, update itself, or delete itself.

-- forms.py --

forms.py contains all of the forms used in Sentinel. These objects utilize Flask-wtforms and WTForms Form objects and validators. We have a login form, a registration form (which subclasses the login form to save some code), and a pattern form.  The validators are useful for checking that required fields have been filled out and marking others as optional. Additionally, we can further validate that provided data should appear similar to an email address with the Email() validator. We can also use password style fields with the PasswordField().

Atop forms, we have a mapping of day of week numbers to abbreviations. This is useful for instantiating our "Schedule Days" in the "Patterns" page, to show the scheduled days as abbreviations and not numbers. Similarly, this day_map is used to show the abbreviations instead of number for the MultiCheckbox used for setting "Schedule Days" in the scheduling modal.

-- processes.py --

processes.py serves two functions -- first it handles all of the get_processes, get_logs, and get_patterns requests and secondly it holds severval helper functions to take the raw output of the get_processes, get_logs, and get_patterns requests and turn them into HTML to be rendered in views.py

jsonify() was written to overwrite Flask's own jsonify method, which does not allow for JSON-ification of lists of JSONs, which is exactly what Sentinel needs for its Bootstrap tables.

get_processes() utilizes the psutils library to query the process list. After querying for specific process information on the host, we create a list of dictionaries that can be consumed by the Bootstrap table in the "Processes" page.

get_logs() checks the provided path for files, iterates though all files line by line, checking for matches with the provided REGEX pattern. If the data is to be consumed by the "Logs" page Bootstrap table, modals are built with the log file's full content and pattern matching information. This resulting data is JSON-ified. If the content is to be consumed by an alert, an HTML table is built containing a list of files queried and the resulting matching lines of text.

get_patterns() queries the database for a user's patterns and returns them in JSON form for the "Patterns" page.

-- alerts.py --

This file runs asynchronously and is kicked off by the crontab. It connects to the database, gathers all the alerts scheduled to run today in this minute, and hits processes.get_logs() to get an HTML table to send containing the alert information. alerts.py's email configuration is found in config.py.

/**
 * sentinel/app/static/
 */

-- /static/js/scripts.js --

scripts.js contains three major functions. On DOM load, the first is bit of code that runs checks if there has been any text inputted into the "Search" field and limits results in the Bootstrap tables based on the REGEX inputted in that field. This "Search" field is used in the "Logs", "Patterns", and "Processes" pages.

The "process_table()" callback function is set on an interval to run every five seconds. It posts an AJAX request to /api/processes to get the current running processes on the selected host. The response data then populates the "Processes" page's Bootstrap table.

log_table() is a function that posts an AJAX request to /api/logs for data when the "Submit" button is clicked. The response data then populates the "Log" page's Bootstrap table. 

/**
 * sentinel/app/templates/
 */

-- base.html --

base.html contains the Jinja templates and HTML that are the backbone of Sentinel. base.html contains the includes for the CSS, JS, the navigation bar, the host-selector, and the Jinja macros to show flash()'ed messages to the user from WTForm errors or via views.py.

The host-selector is a form group consisting the "Host" selector, "User" selector, and the "Search" text field.
