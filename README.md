## Generic Parliament Attendance Log App
========================================


Parliament Attendance Log App is pieced together using the following components:

* The [Flask micro-framework](http://flask.pocoo.org) to host the web interface, with [Jinja2](http://jinja.pocoo.org/docs/) to template web pages based on Python objects.
* [Flask’s Oauth plug-in](https://pythonhosted.org/Flask-OAuth/)  to enable using Google OAuth for simple user authentication.
* [PyMongo](http://api.mongodb.org/python/current/) to link the web framework to the MongoDB database.
* [Pure CSS](http://purecss.io/) to simplify making the pages look ‘pretty.’
* [JQuery UI](http://jqueryui.com/) simplified adding handy interface features such as a javascript calendar to select parliament session dates as well as parliamentarian name auto-completion during attendance logging.
* [Heroku](http://heroku.com/) for a free hosting solution easily managed by git and ssh.
* [OpenShift](http://www.openshift.com/) by RedHat

  
### Schema
--------------------------------------------------
The MongoDB database schema uses four collections:

1. **authentication:** contains Google Oauth credentials as well as the secret key for the application.
2. **registers:** contains all registers as well as their e-mails to validate against Google Oauth login.
3. **parliamentarians:** holds all details about parliamentarians such as emergency contacts, e-mail, birthdays, etc.
4. **psessions:** Contains all records of parliament sessions. Each record contains a date and associates to the record for its indicated register. Within the record is a list of attendances with house type info if applicable and an association to a parliamentarian record for the attended parliamentarian.


The schema for the parliamentarian and parliament sessions collections are shown below.

```json
Parlamentarians
{
    "_id" : ObjectId("53a0ee5b798a010258167aa7"),
    "firstname" : "Eunice",
    "lastname" : "Anderson",
    "gender" : "female",
    "email" : "altheabanks@zensor.com"
    "dob" : ISODate("1997-09-25T00:00:00Z"),
    "emergencyphone" : "+1 (949) 511-3347",
    "emergencycontact" : "Althea Banks",
}

Parliament Sessions
{
    "_id" : ObjectId("53a0f734798a0110dc74abc1"),
    "date" : ISODate("2014-01-01T00:00:00Z"),
    "register" : ObjectId("53a0ef10798a010f40e8cabc"),
    "type" : "law"
    "attendance" : [
        {
            "parliamentarian" : ObjectId("53a0ee5b798a010258167ab6")
        },
        {
            "payment" : {
                "amount" : 15,
                "method" : "credit",
                "house" : "upper"
            },
            "parliamentarian" : ObjectId("53a0ee5b798a010258167ab5")
        },
        {
            "payment" : {
                "amount" : 0,
                "method" : "punched",
                "house" : null
            },
            "parliamentarian" : ObjectId("53a0ee5b798a010258167aaf")
        },
    ]
}
```

Parliament Attendance is modeled after hosting parliament sessions on a track-attendance basis rather than on marking expected attendances as absent, held-up etc.  Marking attendance is made easy by autocompleting the submission form as you type parliamentarian names (assuming matching names exist in the parliamentarians database collection).


### Run it Locally
-------------------

1. Clone this repository

   `$ git clone https://github.com/samsonpaul/parliament.git`

2. Install project dependencies via pip. It's recommended that you do this in a virtualenv

   `$ pip install -r requirements.txt`

3. Initialize your development database.

   `$ python app.py db init`

4. Construct the database and migrate the database models.

   `$ python app.py db upgrade`

5. Run a development server.

   `$ python manage.py runserver`


## Issues/TODO
Parliament Attendance Log App has some tiny server issues that needs to be fixed based on linking up pymongo config


