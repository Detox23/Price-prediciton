from .dbConnection import *
import hashlib, binascii, os, smtplib
from bson.objectid import ObjectId
from threading import Lock
import string
import random
lock = Lock()

def connect_to_tokens():
    connection = MongoClient("mongodb://jakub:90809988Qwe@thecluster-shard-00-00-zrxzv.mongodb.net:27017,thecluster-shard-00-01-zrxzv.mongodb.net:27017,thecluster-shard-00-02-zrxzv.mongodb.net:27017/test?ssl=true&replicaSet=theCluster-shard-0&authSource=admin&retryWrites=true")
    db = pymongo.database.Database(connection, 'Project')
    collection = pymongo.collection.Collection(db, 'Tokens')
    return collection


def connect_to_users():
    connection = MongoClient("mongodb://jakub:90809988Qwe@thecluster-shard-00-00-zrxzv.mongodb.net:27017,thecluster-shard-00-01-zrxzv.mongodb.net:27017,thecluster-shard-00-02-zrxzv.mongodb.net:27017/test?ssl=true&replicaSet=theCluster-shard-0&authSource=admin&retryWrites=true")
    db = pymongo.database.Database(connection, 'Project')
    collection = pymongo.collection.Collection(db, 'Users')
    return collection


def connect_to_houses():
    connection = MongoClient("mongodb://jakub:90809988Qwe@thecluster-shard-00-00-zrxzv.mongodb.net:27017,thecluster-shard-00-01-zrxzv.mongodb.net:27017,thecluster-shard-00-02-zrxzv.mongodb.net:27017/test?ssl=true&replicaSet=theCluster-shard-0&authSource=admin&retryWrites=true")
    db = pymongo.database.Database(connection, 'Project')
    collection = pymongo.collection.Collection(db, 'Houses')
    return collection


def insert_1000_tokens():
    try:
        the_list = []
        existing_list = get_existing_tokens()
        for i in range(1000):
            # number = round(random.randint(1, 600000) * datetime.datetime.now().microsecond+0.121/55 / 0.02)
            number = 15
            if number not in the_list and number not in existing_list:
                the_list.append(number)
            else:
                #then retry to add tokens
                break
        connect_to_tokens().insert_many(the_list)
    except TypeError:
        return False


def get_existing_tokens():
    the_list = []
    token_list = list(connect_to_tokens().find({}, {'_id': 0, 'isUsed': 0}))
    for el in token_list:
        if el not in the_list:
            the_list.append(el['token'])
    return the_list


def get_token():
    token = connect_to_tokens().find_one({'isUsed': False})
    number = token['token']
    return number


def give_token(email, number):
    result_ = False
    user = connect_to_users().find_one({'email':email})
    if number is not None and user is None:
        lock.acquire()
        the_token = connect_to_tokens().find_one({'token': int(number)})
        if the_token['isUsed'] is True:
            return False
        msg = "This is your token. It is important! Remember to save it. Use it to create the account: " + str(number)
        changed = connect_to_tokens().update_one(the_token, {"$set": {'isUsed': True}})
        lock.release()
        if changed.modified_count > 0:
            result_ = True
            send_mail(email, msg)
    return result_


def register(email, password, token):
    the_result = True
    the_token = connect_to_tokens().find_one({'token': int(token)})
    if the_token is not None:
        result = connect_to_users().insert_one({'email': email, 'token': the_token, 'password': hash_password(password),
                                                'is_admin': False})
        if result is None:
            the_result = False
        else:
            msg = 'Your account has been created.'
            send_mail(email, msg)
    return the_result


def get_user_by_mail(email):
    result = connect_to_users().find_one({'email': email})
    return result


def get_user_by_id(_id):
    found = connect_to_users().find_one({'token._id': ObjectId(_id)})
    return found


def log_in(email, password):
    try:
        stored = connect_to_users().find_one({'email': email})['password']
        return check_password(password, stored)
    except TypeError:
        return False


def change_password(email, token, new_password):
    result_ = False
    connection = connect_to_users()
    result = connection.find_one({'token.token': int(token), 'email': email})
    if result is not None:
        changed = connection.update_one({'token.token': int(token), 'email': email}, {'$set': {'password': hash_password(new_password)}})
        if changed.modified_count == 1:
            msg = 'Your password has been changed to ' + new_password
            send_mail(email, msg)
            result_ = True

    return result_


def send_mail(to, message):
    server = smtplib.SMTP('smtp.gmail.com', 25)
    server.starttls()
    server.login('predproject2004@gmail.com', '90809988Qwe')
    msg = "Dear " + to + ". " + message
    server.sendmail('predproject2004@gmail.com', to, msg)


def generate_random_password():
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(20))


def reset_password(token, email):
    result_ = False
    connection = connect_to_users()
    result = connection.find_one({'token.token': int(token), 'email': email})
    password = generate_random_password()
    if result is not None:
        changed = connection.update_one({'token.token': int(token), 'email': email},
                                        {'$set': {'password': hash_password(password)}})
        if changed.modified_count == 1:
            msg = 'Your password has been reset and now it is: ' + password
            send_mail(email, msg)
            result_ = True
    return result_


def hash_password(password):
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt+pwdhash).decode('ascii')


def check_password(password, stored):
    salt = stored[:64]
    stored_pass = stored[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                                  salt.encode('ascii'), 100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_pass


def delete_account(token, password, email):
    result = connect_to_users().delete_one({'token': token, 'password': hash_password(password), 'email': email})
    if result.deleted_count == 1:
        connect_to_tokens().update_one(connect_to_tokens().find_one({'token': token}), {"$set": {'isUsed': False}})
        msg = 'Your account has been deleted'
        send_mail(email, msg)

