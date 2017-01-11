import json
import re
import pymongo
from datetime import datetime
from bson import json_util
from bson.objectid import ObjectId

class PsessionDAO():

	# Initialises the database documents
	def __init__(self, database):
		self.db = database
		self.parliamentariandb = database.parliamentarians
		self.registerdb = database.registers
		self.psessiondb = database.psessions

	# This module calculates the age given the date of birth 
	# Just an interesting feature to adon
	def CalcAge(self, birthday):
		if birthday is None:
			return ""

		birthdate = datetime.now() - birthday
		return int(birthdate.days/365.2425)

	def ValidDate(self, date):
		try:
			return datetime.strptime(date, "%m/%d/%Y")
		except:
			return None

	# Querries the database for the parliamentarian registers
	def GetRegisters(self):
		co_recs = self.registerdb.find().sort("name",1)
		if co_recs is None:
			print("No registers in database?")
			return None

		registers = [{
				"_id"  : c['_id'],
				"name" : c['name'],
				"constituency" : c['constituency']
			} for c in co_recs]

		return registers

	def AutocompleteParliamentarian(self, name_start):
		first, last = None, None
		pieces = re.split("\W+", name_start)
		if len(pieces) > 1:
			first, last = pieces[0], " ".join(pieces[1:])
		elif len(pieces) == 1:
			first = pieces[0]
		else:
			return ""

		first_regex = re.compile("^" + first, re.IGNORECASE)
		last_regex = re.compile(("\w+" if last is None else "^"+last), re.IGNORECASE)

		matches = self.parliamentariandb.aggregate([
			{
				"$match":{
					"firstname":first_regex,
					"lastname":last_regex
				}
			},
			{
				"$project":{
					"name":{
						"$concat":[
							"$firstname",
							" ",
							"$lastname"
						]
					}
				}
			}
		])

		parliamentarians = [parliamentarian['name'] for parliamentarian in matches['result']]
		return json.dumps(parliamentarians)

	# Registers new session in the parliamentarian records schedule
	def AddPsessionAttendance(self, psessionid, name, house, method, ptype):		
		first, last = None, None
		pieces = re.split("\W+", name)
		if len(pieces) > 1:
			first, last = pieces[0], " ".join(pieces[1:])
		else:
			print("Name doesn't match pattern")
			return None

		stu_rec = self.parliamentariandb.find_one({'firstname':first, 'lastname':last})
		if stu_rec is None:
			print("parliamentarian does not exist")
			return

		att_rec = {"parliamentarian" : stu_rec['_id']}
		if house != "":
			att_rec.update({
				"house" : {
					"method" : method,
					"house" : htype
				}
			})
		elif ptype == "punched":
			att_rec.update({
				"house" : {
					"method" : "punched",
					"house" : None
				}
			})

		self.psessiondb.update({
					'_id':ObjectId(psessionid)
				},
				{
					"$push":{
						"attendance":att_rec
					}
				}
			)
    
    # Reemoves session in the parliamentarian records schedule
	def RemovePsessionAttendance(self, psession_id, parliamentarian_id):
		psessionrec = self.psessiondb.find_one({"_id":ObjectId(psession_id)})
		attendance = [att for att in psessionrec['attendance']]
		for i,att in enumerate(attendance):
			if att['parliamentarian'] == ObjectId(parliamentarian_id):
				del attendance[i]
				break

		psessionrec['attendance'] = attendance

		self.psessiondb.update({
				"_id":ObjectId(psession_id)
			},
			{
				"$set":{
					"attendance":attendance
				}
			})
    
    # Registers new session in the parliament schedule
	def AddPsession(self, register, date, ctype):
		co_rec = self.registerdb.find_one({'name':register})
		if co_rec is None:
			print("Register name not in system")
			return
		
		psessiondate = self.ValidDate(date)
		if psessiondate is None:
			return None

		new_psession = {
			"date" : psessiondate,
			"register" : co_rec['_id'],
			"type" : ctype,
			"attendance" : []
		}
		
		cla_rec = self.psessiondb.find_one({'date':new_psession['date']})
		if cla_rec is not None:
			print("psession already exists")
			return
				
		self.psessiondb.insert(new_psession)
	
	# Removes session in the parliament schedule
	def RemovePsession(self, psession_id):
		self.psessiondb.remove({"_id":ObjectId(psession_id)})
    
    # Querries the database for the session Details based on attendees records
	def GetPsession(self, psessionid):
		psessionrec = self.psessiondb.find_one({"_id":ObjectId(psessionid)})

		stud_ids = [rec["parliamentarian"] for rec in psessionrec["attendance"]]
		dbparliamentarians = self.parliamentariandb.find({"_id":{"$in":stud_ids}})
		parliamentarians = {parliamentarian['_id']:parliamentarian for parliamentarian in dbparliamentarians}

		register = self.registerdb.find_one({"_id": psessionrec["register"]})

		psessiondata = {
			"id" : psessionrec['_id'],
			"date": psessionrec['date'].strftime("%A, %B %d %Y"),
			"register": register["name"],
			"type": psessionrec["type"],
			"attendance": []
			# "notes": psessionrec["notes"]
		}

		for attrecord in psessionrec["attendance"]:
			parliamentarian = parliamentarians[attrecord["parliamentarian"]]
			name = parliamentarian["firstname"] + " " + parliamentarian["lastname"]

			psessionrow = {
				"id" : parliamentarian['_id'],
				"name" : name,
				"age" : self.CalcAge(parliamentarian["dob"]),
				"gender" : parliamentarian['gender'],
				"housed" : "",
				"housemethod" : ""
			}

			if "house" in attrecord:
				if attrecord["house"]["housed"] is not None:
					psessionrow["housed"] = "$" + str(attrecord["house"]["amount"]) + " " + attrecord["house"]["housed"]
				else:
					psessionrow["housed"] = ""
				psessionrow["housemethod"] = attrecord["house"]["method"]
			psessiondata["attendance"].append(psessionrow)

		return psessiondata
    
    # Querries the database for All the Parliament Sessions
	def GetPsessions(self):
		dbpsessions = self.psessiondb.find().sort("date",-1)
		dbregisters = self.registerdb.find()

		registers = {register['_id']:register['name'] for register in dbregisters}

		psessiontable = [{
				"id": psessiond['_id'],
				"register": registers[psessiond['register']],
				"type" : psessiond["type"],
				"date": psessiond['date'].strftime("%A, %B %d %Y"),
				"attendance": len(psessiond["attendance"])
			} for psessiond in dbpsessions]

		return psessiontable
    
    # Ability to edit the parliamentarian records
	def EditParliamentarian(self, name, dob, gender, constituency, emergencycontact, emergencyphone, parliamentarian_id):
		first, last = None, None
		pieces = re.split("\W+", name)
		if len(pieces) > 1:
			first, last = pieces[0], " ".join(pieces[1:])
		else:
			print("Name doesn't match pattern")
			return None

		parliamentarian = {
			"firstname" : first,
			"lastname" : last,
			"dob" : self.ValidDate(dob),
			"constituency" : constituency,
			"gender" : gender,
			"emergencycontact" : emergencycontact,
			"emergencyphone" : emergencyphone
		}

		self.parliamentariandb.update({'_id':ObjectId(parliamentarian_id)}, parliamentarian)
    
    # Add a new parliamentarian to the database
	def AddParliamentarian(self, name, dob, gender, constituency, emergencycontact, emergencyphone):
		first, last = None, None
		pieces = re.split("\W+", name)
		if len(pieces) > 1:
			first, last = pieces[0], " ".join(pieces[1:])
		else:
			print("Name doesn't match pattern")
			return None

		parliamentarian = {
			"firstname" : first,
			"lastname" : last,
			"dob" : self.ValidDate(dob),
			"constituency" : constituency,
			"gender" : gender,
			"emergencycontact" : emergencycontact,
			"emergencyphone" : emergencyphone
		}

		stu_rec = self.parliamentariandb.find_one({'firstname':first, 'lastname':last})
		if stu_rec is not None:
			print("parliamentarian already exists")
			return

		self.parliamentariandb.insert(parliamentarian)
	
	# Querries the database for All the Parliamentarians	
	def GetParliamentarians(self):
		dbparliamentarians = self.parliamentariandb.find({}).sort("lastname",1)

		parliamentariantable = [{
				"id" : stu_rec['_id'],
				"name": stu_rec['firstname'] + " " + stu_rec['lastname'],
				"age" : self.CalcAge(stu_rec["dob"]),
				"gender" : stu_rec["gender"],
				"constituency" : stu_rec["constituency"],
			} for stu_rec in dbparliamentarians]

		return parliamentariantable

    # Querries the database for the Parliamentarian Details
	def GetParliamentarian(self, parliamentarian_id, edit=False):
		stu_rec = self.parliamentariandb.find_one({'_id':ObjectId(parliamentarian_id)})

		dob_fmt = ("%m/%d/%Y" if edit else "%A, %B %d %Y")
		birthdate = lambda x:(x.strftime(dob_fmt) if x else "") 

		parliamentarian = {
			"id": stu_rec['_id'],
			"name": stu_rec['firstname'] + " " + stu_rec['lastname'],
			"dob" : birthdate(stu_rec["dob"]),
			"gender" : stu_rec["gender"],
			"constituency" : stu_rec["constituency"],
			"emergencycontact" : stu_rec["emergencycontact"],
			"emergencyphone" : stu_rec["emergencyphone"]
		}

		return parliamentarian

def j0(obj):return json.dumps(obj, sort_keys=True, indent=4, default=json_util.default)
def jprint(obj):print(j0(obj))
