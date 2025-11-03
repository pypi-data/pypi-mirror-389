
from urllib.parse import quote_plus
from pymongo import MongoClient
import pyotp
import time
import ipaddress
import hashlib
import json
from bson.objectid import ObjectId
import datetime as dt
from zoneinfo import ZoneInfo
import functools
from pymongo.errors import PyMongoError


class TX:
    def __init__(self, client):
        self.client = client

    def get_new_session(self):
        session = self.client.start_session()
        tx=session.start_transaction()
        return session, tx


def do_tx():
    def actual_decorator(func):
        @functools.wraps(func) # Good practice to preserve function metadata
        def wrapper(self, *args, **kwargs):
            tx = None
            session = None
            
            named_variable_name = "session"
            provided_session = kwargs[named_variable_name] if named_variable_name in kwargs and kwargs[named_variable_name] is not None else None

            debug=False
            if provided_session is None:
                if debug:
                    print("No section provided, creating session")
            
                session, tx = TX(self.get_client()).get_new_session()
                cur_session = session
            else:
                if debug:
                    print("Section already exists, make use of existing one")
                cur_session = provided_session

            if debug:
                print(f"running function [{func}]")

            # Execute the actual function
            try:
                if provided_session is None:
                    kwargs[named_variable_name]=cur_session
                result = func(self, *args, **kwargs)
            
            except PyMongoError as e:
                if provided_session is not None:
                    if debug:
                        print("PyMongoError, will raise")
                    raise e
                else:
                    if debug:
                        print("PyMongoError, rollback")
                    session.abort_transaction()
                    raise e
            except Exception as e:
                if provided_session is None:
                    if debug:
                        print("Exception, will raise")
                    session.abort_transaction()
                raise e
            else:
                if provided_session is None:
                    if debug:
                        print("commit change")
                    session.commit_transaction()
            finally:
                if debug:
                    print("do finally")
                if provided_session is None:
                    if tx is not None:
                        if debug:
                            print("off load tx")
                        tx = None
                    if session is not None:
                        if debug:
                            print("off load session")
                        session=None

            return result
        return wrapper
    return actual_decorator