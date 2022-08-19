from email.policy import strict
from flask import Flask,request,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_restful import Resource,Api,reqparse,abort
from flask_bcrypt import Bcrypt
import datetime
import os
# from flask_migrate import Migrate

#Init app
app=Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
api= Api(app)

#database
app.config["SECRET_KEY"] = '9bbd8f44c4ec734042fd241973766449'
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///App.db'
#init db
db=SQLAlchemy(app)
# migrate = Migrate(app,db)
#init ma
ma=Marshmallow(app)
#init bcrypt
bcrypt = Bcrypt(app)

def getDateTimeInMillis():
    return datetime.datetime.now().timestamp() * 1000


class Courthouse(db.Model):
    __tablename__ = 'Courthouse'
    id = db.Column(db.Integer,primary_key=True)
    courtType = db.Column(db.String, nullable=False)
    courtLocation = db.Column(db.String, nullable=False)
    users = db.relationship('User', backref='Courthouse')
    # fixedCaseDates = db.relationship('FixedCaseDate', backref='Courthouse')

    def __repr__(self):
        return self.id + self.courtLocation

class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    fullName = db.Column(db.String, nullable=False)
    cityOfOrigin = db.Column(db.String, nullable=False)
    courtHouse = db.Column(db.Integer, db.ForeignKey('Courthouse.id'), nullable=False)
    role = db.Column(db.String, nullable=False)
    cases = db.relationship('Case', backref='User')
    fixedCaseDates = db.relationship('FixedCaseDate', backref='User')

    def __repr__(self):
        return self.id

class Request(db.Model):
    __tablename__ = 'Request'
    id = db.Column(db.Integer, primary_key=True)
    fromUser = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    toUser = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    requestType = db.Column(db.String, nullable=False)
    requestData = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    createdOn = db.Column(db.String, default=getDateTimeInMillis(), nullable=False)

    def __repr__(self):
        return self.id

class Case(db.Model):
    __tablename__ = 'Case'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    assignedAdvocate = db.Column(db.String, nullable=False)
    affidavit = db.Column(db.String, nullable=False)
    chargeSheet = db.Column(db.String, nullable=False)
    caseCreatedTime = db.Column(db.String, default=getDateTimeInMillis(), nullable=False)
    lastModified = db.Column(db.String, default=getDateTimeInMillis(), nullable=False)
    caseStatus = db.Column(db.String, nullable=False)
    severityIndex = db.Column(db.String, nullable=False)
    assignedBy = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    fixedCaseDate = db.relationship("FixedCaseDate", backref="Case")

    def __repr__(self):
        return self.id

class FixedCaseDate(db.Model):
    __tablename__ = 'FixedCaseDate'
    id = db.Column(db.Integer, primary_key=True)
    case = db.Column(db.Integer, db.ForeignKey("Case.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    createdBy = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    type = db.Column(db.String, nullable=False)

    def __repr__(self):
        return self.id



class JudgeCasePreference(db.Model):
    __tablename__ = 'JudgeCasePreference'
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    section = db.Column(db.String, nullable=False)
    preferenceOrder = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return self.user.name + " " + self.preferenceOrder

class UserSchema(ma.Schema):
    class Meta:
        fields=('id','username','fullname','city of origin','role','cases')

#init schema
user_schema = UserSchema()
users_schema = UserSchema(many=True)


#case schema

class CaseSchema(ma.Schema):
    class Meta:
        fields=('id','name','assignedAdvocate','affidavit','chargeSheet','caseCreatedTime','lastModified','caseStatus','severityIndex','assignedBy')

#init schema
case_schema = CaseSchema()
cases_schema = CaseSchema(many=True)

class FixedcaseSchema(ma.Schema):
    class Meta:
        fields=('id','case','date','createdby','type')

#init schema
fixedcase_schema = FixedcaseSchema()
fixedcases_schema = FixedcaseSchema(many=True)

class CourthouseSchema(ma.Schema):
    class Meta:
        fields=('id','courttype','courtLocation')

#init schema
courthouse_schema = CourthouseSchema()
courthouses_schema = CourthouseSchema(many=True)

class RequestSchema(ma.Schema):
    class Meta:
        fields=('id','fromuser','touser','requesttype','requestdata','status','createdon')

#init schema
Request_schema = RequestSchema()
Requests_schema = RequestSchema(many=True)

class JudgecaseprefSchema(ma.Schema):
    class Meta:
        fields=('id','user','section','preferenceoder')

#init schema
Judgecasepref_schema = JudgecaseprefSchema()
Judgecaseprefs_schema = JudgecaseprefSchema(many=True)


class Court(Resource):
    def get(self):
        court=Courthouse.query.all()
        return courthouses_schema.jsonify(court)
    def post(self):
        courttype=request.json['courttype'] 
        courtLocation=request.json['courtlocation']
        # user=request.json['user']
        # fixedcasesdates=request.json['fixedcasesdate']
        court =Courthouse(courtType=courttype,courtLocation =courtLocation)
        db.session.add(court)
        db.session.commit()
        return courthouse_schema.jsonify(court)
    
class user(Resource):
    def get(self):
        user=User.query.all()
        return users_schema.jsonify(user)
    def post(self):
        username=request.json['username']
        password =request.json['password']
        fullName=request.json['fullName']
        cityOfOrigin=request.json['cityOfOrigin']
        courtHouse =request.json['courtHouse']
        role=request.json['role']
        cases=request.json['cases']
        fixedCaseDates=request.json['fixedCaseDates']
        user =User(username=username,password =password, fullName= fullName,cityOfOrigin=cityOfOrigin,courtHouse=courtHouse,role=role,cases=cases,fixedCaseDates=fixedCaseDates)
        db.session.add(user)
        db.session.commit()
        return courthouse_schema.jsonify(user)
    
    def delete(self):
       user=User.query.all()
       db.seesion.delete(user)
       db.session.commit()

class users(Resource):
    def get(self,userid):
        user = User.query.filter_by(id=userid).all()
        return users_schema.jsonify(user)
    
    def delete(self,userid):
       user = User.query.filter_by(id=userid).all()
       db.seesion.delete(user)
       db.session.commit()
    
    def put(self,userid):
        user = User.query.filter_by(id=userid).all()
        user.username=request.json['username']
        user.password =request.json['password']
        user.fullName=request.json['fullName']
        user.cityOfOrigin=request.json['cityOfOrigin']
        user.courtHouse =request.json['courtHouse']
        user.role=request.json['role']
        user.cases=request.json['cases']
        user.fixedCaseDates=request.json['fixedCaseDates']
        db.session.commit()

class cases(Resource):
    def get(self,caseno):
        case = Case.query.filter_by(id=caseno).all()
        return cases_schema.jsonify(case)
    
    def delete(self,caseno):
       case = Case.query.filter_by(id=caseno).all()
       db.seesion.delete(case)
       db.session.commit()
    
    def put(self,caseno):
        case = Case.query.filter_by(id=caseno).all()
        case.name=request.json['name']
        case.assignedAdvocate =request.json['assignedAdvocate']
        case.affidivit=request.json['affidivi']
        case.chargesheet=request.json['chargesheet']
        case.casestatus =request.json['casestatus']
        case.sevirity=request.json['sevirity']
        case.assignedby=request.json['assignedby']
        case.fixedCaseDates=request.json['fixedCaseDates']
        db.session.commit()

class case(Resource):
    def get(self):
        case = Case.query.all()
        return cases_schema.jsonify(case)
    
    def delete(self):
       case = Case.query.all()
       db.seesion.delete(case)
       db.session.commit()
    
    def post(self):
        name=request.json['name']
        assignedAdvocate =request.json['assignedAdvocate']
        affidivit=request.json['affidavit']
        chargesheet=request.json['chargeSheet']
        casestatus =request.json['caseStatus']
        sevirity=request.json['severityIndex']
        assignedby=request.json['assignedBy']
        case =Case(name=name,assignedAdvocate =assignedAdvocate, affidavit= affidivit,chargeSheet=chargesheet,caseStatus=casestatus,severityIndex=sevirity,assignedBy=assignedby)
        db.session.add(case)
        db.session.commit()
        
class requests(Resource):
    def get(self):
        requests = Request.query.all()
        return Requests_schema.jsonify(requests)
    
    def post(self):
        fromUser=request.json['fromUser']
        toUser =request.json['toUser']
        requestType=request.json['requestType']
        requestData=request.json['requestData']
        status =request.json['status']
        request =Request(fromUser=fromUser,toUser =toUser, requestType= requestType,requestData=requestData,status=status)
        db.session.add(request)
        db.session.commit()

class requestss(Resource):
    def get(self,reqid):
        requests = Request.query.filter_by(id=reqid).all()
        return Request_schema.jsonify(requests)

    def delete(self,reqid):
       requests = Request.query.filter_by(id=reqid).all()
       db.seesion.delete(requests)
       db.session.commit()
    
    
    def put(self,reqid):
        requests = Request.query.filter_by(id=reqid).all()
        requests.fromUser=request.json['fromUser']
        requests.toUser =request.json['toUser']
        requests.requestType=request.json['requestType']
        requests.requestData=request.json['requestData']
        requests.status =request.json['status']
        db.session.commit()

class fixeddates(Resource):
    def get(self):
        fixedcasedate = FixedCaseDate.query.all()
        return fixedcases_schema.jsonify(fixedcasedate)
    
    def post(self):
        case=request.json['case']
        date =request.json['date']
        createdBy=request.json['createdBy']
        type=request.json['type']
        fixeddate =FixedCaseDate(case=case,date =date, createdBy= createdBy,type=type)
        db.session.add(fixeddate)
        db.session.commit()\

class fixeddate(Resource):
    def get(self,fixid):
        fixedcasedate = FixedCaseDate.filter_by(id=fixid).all()
        return fixedcase_schema.jsonify(fixedcasedate)
    
    def put(self,fixid):
        fixedcasedate = FixedCaseDate.filter_by(id=fixid).all()
        fixedcasedate.case=request.json['case']
        fixedcasedate.date =request.json['date']
        fixedcasedate.createdBy=request.json['createdBy']
        fixedcasedate.type=request.json['type']
        db.session.commit()
    
    def delete(self,fixid):
        fixedcasedate = FixedCaseDate.filter_by(id=fixid).all()
        db.seesion.delete(fixedcasedate)
        db.session.commit()
        

api.add_resource(Court,'/courthouse')
api.add_resource(user,'/user')
api.add_resource(case,'/case')
api.add_resource(cases,'/case/<int:caseno>')
api.add_resource(requests,'/request')
api.add_resource(requestss,'/request/<int:reqid>')
api.add_resource(fixeddates,'/fixedcasedates')  
api.add_resource(fixeddate,'/fixedcasedates/<int:fixid>')  

#run Server
if __name__=='__main__':
    app.run(debug=True)



