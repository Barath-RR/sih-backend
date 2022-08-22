import os
import secrets
import traceback

from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_marshmallow import Marshmallow
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

from helpers import exceptionAsAJson, successAsJson, getDateTimeInMillis

# Init app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
api = Api(app)
# database
app.config["SECRET_KEY"] = '9bbd8f44c4ec734042fd241973766449'
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///App.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config['UPLOAD_FOLDER'] = "files/"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# init db
db = SQLAlchemy(app)
# init ma
ma = Marshmallow(app)
# init bcrypt
bcrypt = Bcrypt(app)





class Courthouse(db.Model):
    __tablename__ = 'Courthouse'
    id = db.Column(db.Integer, primary_key=True)
    courtType = db.Column(db.String, nullable=False)
    courtLocation = db.Column(db.String, nullable=False)
    users = db.relationship('User', backref='Courthouse')
    fixedCaseDates = db.relationship('FixedCaseDate', backref='Courthouse')

    def __repr__(self):
        return self.id + self.courtLocation


class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    fullName = db.Column(db.String, nullable=False)
    cityOfOrigin = db.Column(db.String, nullable=False)
    courtHouse = db.Column(db.Integer, db.ForeignKey(
        'Courthouse.id'), nullable=False)
    role = db.Column(db.String, nullable=False)
    cases = db.relationship('Case', backref='User')
    fixedCaseDates = db.relationship('FixedCaseDate', backref='User')

    def __repr__(self):
        return str(self.id)


class Request(db.Model):
    __tablename__ = 'Request'
    id = db.Column(db.Integer, primary_key=True)
    fromUser = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    toUser = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    requestType = db.Column(db.String, nullable=False)
    requestData = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    createdOn = db.Column(
        db.String, default=getDateTimeInMillis(), nullable=False)

    def __repr__(self):
        return str(self.id)


class Case(db.Model):
    __tablename__ = 'Case'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    assignedAdvocate = db.Column(db.String, nullable=False)
    affidavit = db.Column(db.String, nullable=False)
    chargeSheet = db.Column(db.String, nullable=False)
    caseCreatedTime = db.Column(
        db.String, default=getDateTimeInMillis(), nullable=False)
    lastModified = db.Column(
        db.String, default=getDateTimeInMillis(), nullable=False)
    caseStatus = db.Column(db.String, nullable=False, default="Not yet assigned")
    severityIndex = db.Column(db.String, nullable=False, default="0.1")
    assignedBy = db.Column(
        db.Integer, db.ForeignKey('User.id'), nullable=False)
    fixedCaseDate = db.relationship("FixedCaseDate", backref="Case")

    def __repr__(self):
        return self.id


class FixedCaseDate(db.Model):
    __tablename__ = 'FixedCaseDate'
    id = db.Column(db.Integer, primary_key=True)
    case = db.Column(db.Integer, db.ForeignKey("Case.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    createdBy = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    courthouse = db.Column(db.Integer, db.ForeignKey("Courthouse.id"), nullable=False)
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
        return self.user + " " + self.preferenceOrder


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'username', 'fullname', 'city of origin', 'role')


# init schema
user_schema = UserSchema()
users_schema = UserSchema(many=True)


# case schema
class CaseSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'assignedAdvocate', 'affidavit', 'chargeSheet',
                  'caseCreatedTime', 'lastModified', 'caseStatus', 'severityIndex', 'assignedBy')


# init schema
case_schema = CaseSchema()
cases_schema = CaseSchema(many=True)


class FixedcaseSchema(ma.Schema):
    class Meta:
        fields = ('id', 'case', 'date', 'createdby', 'type')


# init schema
fixedcase_schema = FixedcaseSchema()
fixedcases_schema = FixedcaseSchema(many=True)


class CourthouseSchema(ma.Schema):
    class Meta:
        fields = ('id', 'courttype', 'courtLocation')


# init schema
courthouse_schema = CourthouseSchema()
courthouses_schema = CourthouseSchema(many=True)


class RequestSchema(ma.Schema):
    class Meta:
        fields = ('id', 'fromuser', 'touser', 'requesttype',
                  'requestdata', 'status', 'createdon')


# init schema
Request_schema = RequestSchema()
Requests_schema = RequestSchema(many=True)


class JudgecaseprefSchema(ma.Schema):
    class Meta:
        fields = ('id', 'user', 'section', 'preferenceoder')


# init schema
Judgecasepref_schema = JudgecaseprefSchema()
Judgecaseprefs_schema = JudgecaseprefSchema(many=True)


class CourtController(Resource):
    def get(self):
        court = Courthouse.query.all()
        return courthouses_schema.jsonify(court)

    def post(self):
        court_type = request.form.get('courtType')
        court_location = request.form.get('courtLocation')
        court = Courthouse(courtType=court_type, courtLocation=court_location)
        db.session.add(court)
        db.session.commit()
        return courthouse_schema.jsonify(court)


class UserController(Resource):
    def get(self):
        try:
            user = User.query.all()
            return users_schema.jsonify(user)
        except Exception as e:
            print(e)
            return exceptionAsAJson("user get", e)

    def post(self):
        username = request.form.get('username')
        password = request.form.get('password')
        fullName = request.form.get('fullName')
        cityOfOrigin = request.form.get('cityOfOrigin')
        try:
            courtHouse = Courthouse.query.filter(
                Courthouse.id == request.form.get('courtHouse')).one()
            # print(courtHouse)courtHouseser post courthouse get", e)
        except Exception as e:
            print(e)
            return exceptionAsAJson("user post", str(e))
        role = request.form.get('role')
        user = User(username=username, password=password, fullName=fullName,
                    cityOfOrigin=cityOfOrigin, courtHouse=courtHouse.id, role=role)
        db.session.add(user)
        db.session.commit()
        return courthouse_schema.jsonify(user)

    def delete(self):
        try:
            users = User.query.all()
            print(users)
            for user in users:
                print(user)
                db.session.delete(user)
            db.session.commit()
        except Exception as e:
            return exceptionAsAJson("user delete", e)


class AllUserController(Resource):
    def get(self, userid):
        user = User.query.filter_by(id=userid).all()
        if user == None:
            return exceptionAsAJson("users get", "No user found")
        return users_schema.jsonify(user)

    def delete(self, userid):
        user = User.query.filter_by(id=userid).one()
        db.seesion.delete(user)
        db.session.commit()
        return successAsJson()

    def put(self, userid):
        user = User.query.filter_by(id=userid).all()
        user.username = request.json['username']
        user.password = request.json['password']
        user.fullName = request.json['fullName']
        user.cityOfOrigin = request.json['cityOfOrigin']
        user.courtHouse = request.json['courtHouse']
        user.role = request.json['role']
        user.cases = request.json['cases']
        user.fixedCaseDates = request.json['fixedCaseDates']
        db.session.commit()


class AllCaseController(Resource):
    def get(self, caseno):
        case = Case.query.filter_by(id=caseno).all()
        return cases_schema.jsonify(case)

    def delete(self, caseno):
        case = Case.query.filter_by(id=caseno).all()
        db.seesion.delete(case)
        db.session.commit()

    def put(self, caseno):
        case = Case.query.filter_by(id=caseno).all()
        case.name = request.form.get('name')
        case.assignedAdvocate = request.form.get('assignedAdvocate')
        case.affidivit = request.form.get('affidivi')
        case.chargesheet = request.form.get('chargesheet')
        case.casestatus = request.form.get('casestatus')
        case.sevirity = request.form.get('sevirity')
        case.assignedby = request.form.get('assignedby')
        case.fixedCaseDates = request.form.get('fixedCaseDates')
        db.session.commit()


class CaseController(Resource):
    def get(self):
        case = Case.query.all()
        return cases_schema.jsonify(case)

    def post(self):
        name = request.form.get('case_name')
        assignedAdvocate = request.form.get("assigned_advocate")
        affidavit = request.files['affidavit']
        chargesheet = request.files["charge_sheet"]
        assignedby = request.form.get("assigned_by")
        affidavit_rename = "{}_{}_affidavit.pdf".format(name, secrets.token_hex(10))
        affidavit.save(os.path.join(app.config["UPLOAD_FOLDER"] + "/affidavit/", secure_filename(affidavit_rename)))
        chargesheet_rename = "{}_{}_chargesheet.pdf".format(name, secrets.token_hex(10))
        chargesheet.save(
            os.path.join(app.config["UPLOAD_FOLDER"] + "/chargesheet/", secure_filename(chargesheet_rename)))

        case = Case(name=name, assignedAdvocate=assignedAdvocate, affidavit=affidavit_rename,
                    chargeSheet=chargesheet_rename, assignedBy=assignedby)
        print(name, assignedAdvocate, affidavit, chargesheet, assignedby)
        data = dict(request.form)
        print(data)
        db.session.add(case)
        db.session.commit()
        return successAsJson()


# class RequestController(Resource):
#     def get(self):
#         requests = Request.query.all()
#         return Requests_schema.jsonify(requests)
#
#     def post(self):
#         fromUser = request.json['fromUser']
#         toUser = request.json['toUser']
#         requestType = request.json['requestType']
#         requestData = request.json['requestData']
#         status = request.json['status']
#         request = Request(fromUser=fromUser, toUser=toUser,
#                           requestType=requestType, requestData=requestData, status=status)
#         print(request)
#         db.session.add(request)
#         db.session.commit()
#
#
# class AllRequestController(Resource):
#     def get(self, reqid):
#         requests = Request.query.filter_by(id=reqid).all()
#         return Request_schema.jsonify(requests)
#
#     def delete(self, reqid):
#         requests = Request.query.filter_by(id=reqid).all()
#         db.seesion.delete(requests)
#         db.session.commit()
#
#     def put(self, reqid):
#         requests = Request.query.filter_by(id=reqid).all()
#         requests.fromUser = request.json['fromUser']
#         requests.toUser = request.json['toUser']
#         requests.requestType = request.json['requestType']
#         requests.requestData = request.json['requestData']
#         requests.status = request.json['status']
#         db.session.commit()


class AllFixedDateController(Resource):
    def get(self):
        fixedcasedate = FixedCaseDate.query.all()
        return fixedcases_schema.jsonify(fixedcasedate)

    def post(self):
        case = request.json['case']
        date = request.json['date']
        createdBy = request.json['createdBy']
        type = request.json['type']
        fixeddate = FixedCaseDate(
            case=case, date=date, createdBy=createdBy, type=type)
        db.session.add(fixeddate)
        db.session.commit()


class FixedDateController(Resource):
    def get(self, fixid):
        fixedcasedate = FixedCaseDate.filter_by(id=fixid).all()
        return fixedcase_schema.jsonify(fixedcasedate)

    def put(self, fixid):
        fixedcasedate = FixedCaseDate.filter_by(id=fixid).all()
        fixedcasedate.case = request.form.get('case')
        fixedcasedate.date = request.form.get('date')
        fixedcasedate.createdBy = request.form.get('createdBy')
        fixedcasedate.type = request.form.get('type')
        db.session.commit()

    def delete(self, fixid):
        fixedcasedate = FixedCaseDate.filter_by(id=fixid).all()
        db.seesion.delete(fixedcasedate)
        db.session.commit()


class ScheduleController(Resource):
    def get(self):
        cases = Case.query.order_by(Case.caseCreatedTime).limit(10)
        return cases_schema.jsonify(cases)


class LoginController(Resource):
    def post(self):
        try:
            username = request.form.get("username")
            password = request.form.get("password")
            print(username, password)
            user = User.query.filter(User.username == username and User.password == password).one()
            if user != None:
                return user_schema.jsonify(user)
            return jsonify({
                "status": "Authentication failed"
            })
        except Exception as e:
            traceback.print_exc()
            return exceptionAsAJson("login post", str(e))


api.add_resource(CourtController, '/courthouse')
api.add_resource(UserController, '/user')
api.add_resource(AllUserController, '/user/<int:userno>')
api.add_resource(CaseController, '/case')
api.add_resource(AllCaseController, '/case/<int:caseno>')
# api.add_resource(RequestController, '/request')
# api.add_resource(AllRequestController, '/request/<int:reqid>')
api.add_resource(AllFixedDateController, '/fixedcasedate')
api.add_resource(FixedDateController, '/fixedcasedate/<int:fixid>')
api.add_resource(LoginController, "/login")
api.add_resource(ScheduleController, "/schedule")

# run Server
if __name__ == '__main__':
    app.run(debug=True)
