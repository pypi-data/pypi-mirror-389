from pymongo import MongoClient
from reg_my_ip_core.totp_tools import gen_secret
from reg_my_ip_core.tx_tools import do_tx
from bson.objectid import ObjectId
import datetime as dt
from zoneinfo import ZoneInfo
import hashlib
import json
from reg_my_ip_core.digest_tools import md5_hash
import ipaddress

class MongoClinetBased:
    def get_client(self):
        pass

class RegMyIP(MongoClinetBased):
    @staticmethod
    def from_connection_str(connection_str, name)->'RegMyIP':
        client = MongoClient(connection_str) 
        return RegMyIP(client, name)

    def __init__(self, client, dbname):
        self.client = client
        self.dbname = dbname
    
    def get_client(self):
        return self.client

    def get_db(self):
        return self.client.get_database(self.dbname)
    
    @do_tx()
    def list_groups(self, session=None)->[str]:
        return [g['group'] for g in self.get_db().get_collection("conf").find({}, session=session)]

    @do_tx()
    def group_exists(self, group, session=None)->bool:
        return self.get_db().get_collection("conf").find_one({"group":group}, session=session) is not None

    @do_tx()
    def reg_group(self, group: str, description: str, session=None)->'Group':
        if self.group_exists(group, session=session):
            raise Exception(f"Group[{group}] already exists")
        
        rs = self.get_db().get_collection("conf").insert_one({
            "group": group,
            "description": description,
            "secret": gen_secret(),
        }, session=session)
        return Group(self, rs.inserted_id, session=session)

    @do_tx()
    def group(self, group: str, session=None)->'Group':
        if self.group_exists(group, session=session) == False:
            raise Exception(f"Group[{group}] not exists")
        return Group.by_name(self, group, session=session)
    
    @do_tx()
    def delete_group(self, group: str, session=None)->bool:
        if self.group_exists(group, session=session):
            self.get_db().get_collection("conf").delete_many({"group":group}, session=session)
            self.get_db().get_collection("machines").delete_many({"group":group}, session=session)
            for id in [ObjectId(var1['ips']) for var1 in self.get_db().get_collection("applications").find({"group":group}, session=session)]:
                self.get_db().get_collection("ip-list").delete_one({"_id":id}, session=session)
            self.get_db().get_collection("applications").delete_many({"group":group}, session=session) 

        return True


class Group(MongoClinetBased):
    @staticmethod
    def by_name(reg_my_ip: 'RegMyIP', name: str, session=None)->'Group':
        conf = reg_my_ip.get_db().get_collection("conf").find_one({"group":name}, session=session)
        return Group(reg_my_ip, conf['_id'], session=session)


    def __init__(self, reg_my_ip: RegMyIP, id: ObjectId, session=None):
        self.reg_my_ip=reg_my_ip
        self.id=id
        view = self.view(session=session)
        self.name = view['group']
    
    def get_client(self):
        return self.reg_my_ip.get_client()
    
    @do_tx()
    def view(self, session=None):
        rs= self.reg_my_ip.get_db().get_collection("conf").find_one({"_id": self.id}, session=session)
        return rs

    @do_tx()
    def machine_exists(self, machine, session=None)->bool:
        return self.reg_my_ip.get_db().get_collection("machines").find_one({"group":self.name, "name": machine}, session=session) is not None

    @do_tx()
    def machine(self, machine, session=None)->'Machine':
        if self.machine_exists(machine, session=session) == False:
            raise Exception(f"Machine[{machine}] not exists")
        view = self.reg_my_ip.get_db().get_collection("machines").find_one({"group":self.name, "name": machine}, session=session)
        return Machine(self, view['_id'], session=session)

    @do_tx()
    def machines(self, session=None)->bool:
        return [Machine(self, m['_id'], session=session) for m in self.reg_my_ip.get_db().get_collection("machines").find({"group":self.name}, session=session)]

    @do_tx()
    def remove_machine(self, name: str, session=None):
        self.reg_my_ip.get_db().get_collection("machines").delete_one({"group":self.name, "name": name}, session=session)
        return True

    @do_tx()
    def apps(self, session=None)->[str]:
        return [ Application.by_name(self, var1['name']).view()['name'] for var1 in self.reg_my_ip.get_db().get_collection("applications").find({"group":self.name}, session=session)]

    @do_tx()
    def add_machine(self, name: str, description: str, tags: [str], session=None):
        if self.machine_exists(name, session=session) == True:
            raise Exception(f"Machine[{name}] already exists")

        id=self.reg_my_ip.get_db().get_collection("machines").insert_one(
            {
                "group":self.name,
                "name": name,
                "description": description,
                "tags": tags,
                "ip": "0.0.0.0",
                "secret": gen_secret()
            }, session=session
        ).inserted_id

        self.update_ips_by_machine(self.machine(name, session=session), session=session)
        return Machine(self, id, session=session)
    
    @do_tx()
    def app(self, name, session=None)->'Application':
        if not self.app_exists(name,session=session):
            raise Exception(f"Application[{name}] not exists")
        return Application(self, self.reg_my_ip.get_db().get_collection("applications").find_one({"group":self.name, "name": name}, session=session)['_id'], session=session)
            
        
    @do_tx()
    def app_exists(self, app, session=None)->bool:
        return self.reg_my_ip.get_db().get_collection("applications").find_one({"group":self.name, "name": app}, session=session) is not None

    @do_tx()
    def add_new_ip_list(self, session=None):
        data={}   
        return IPList(self, self.reg_my_ip.get_db().get_collection("ip-list").insert_one({
            "ips": data,
            "etag": md5_hash(json.dumps(data)),
            "last_update": dt.datetime.now(ZoneInfo("Asia/Hong_Kong")).isoformat()
        }, session=session).inserted_id, session=session)

    @do_tx()
    def add_app(self, name: str, description: str, session=None)->'Application':
        if self.app_exists(name, session=session) == True:
            raise Exception(f"Application[{name}] already exists")
        id=self.reg_my_ip.get_db().get_collection("applications").insert_one(
            {
                "group":self.name,
                "name": name,
                "description": description,
                "secret": gen_secret(),
                "ips": str(self.add_new_ip_list(session=session).id)
            }, session=session
        ).inserted_id
        app= Application(self,id, session=session)
        app.update_app_ips(session=session)

        return app
    
    @do_tx()
    def edit_description(self, description: str, session=None):
        self.reg_my_ip.get_db().get_collection("conf").find_one_and_update(
            {"_id": self.id},
            {"$set": {"description": description}},
            session=session
        )
        return self


    @do_tx()
    def remove_app(self, name: str, session=None):
        if self.app_exists(name, session=session):
            ip_list_id = self.app(name, session=session).view()['_id']
            self.reg_my_ip.get_db().get_collection("ip-list").delete_one({"_id":ObjectId(ip_list_id)}, session=session)
        self.reg_my_ip.get_db().get_collection("applications").delete_one({"group":self.name, "name": name}, session=session)
        return True
    
    @do_tx()
    def ip_list_exists(self, id: ObjectId, session=None):
        self.reg_my_ip.get_db().get_collection("ip-list").find_one({"_id": id}, session=session) is not None

    @do_tx()
    def ip_list(self, id: ObjectId, session=None):
        if self.ip_list_exists(id, session=session) == False:
            raise Exception(f"IPList[{id} not exists")
        return IPList(self, id, session=session)

    @do_tx()     
    def update_ips_by_machine(self, machine, session=None):
        machine_view = machine.view(session=session)
        list_of_app=[var1[len('used-by: '):] for var1 in machine_view['tags'] if var1.startswith('used-by: ')]
        for app_name in list_of_app:
            if self.app_exists(app_name, session=session) == False:
                continue
            self.app(app_name, session=session)\
                .update_app_ips(session=session)
        
class IPList(MongoClinetBased):
    def __init__(self, group: Group, id: ObjectId, session=None):
        self.group=group
        self.reg_my_ip=group.reg_my_ip
        self.id=ObjectId(id)
        v = self.view(session=session)
        self.etag = v['etag']
        self.last_update = v['last_update']


    def get_client(self):
        return self.reg_my_ip.get_client()

    @do_tx()
    def view(self, session=None):
        v = self.reg_my_ip.get_db().get_collection("ip-list").find_one({"_id": self.id}, session=session)
        return v
    

        
class Application:
    @do_tx()
    def by_name(group: 'Group', name: str, session=None)->'Application':
        return Application(group, group.reg_my_ip.get_db().get_collection("applications").find_one({"group": group.name, "name": name}, session=session)['_id'], session=session)

    def __init__(self, group: Group, id: ObjectId, session=None):
        self.group=group
        self.reg_my_ip=group.reg_my_ip
        self.id=id
        v = self.view(session=session)
        self.name = v['name']

    def get_client(self):
        return self.reg_my_ip.get_client()
    
    @do_tx()
    def view(self, session=None):
        rs= self.reg_my_ip.get_db().get_collection("applications").find_one({"_id": self.id}, session=session)
        return rs

    @do_tx()
    def edit_description(self, description: str, session=None):
        self.reg_my_ip.get_db().get_collection("applications").find_one_and_update(
            {"_id": self.id},
            {"$set": {"description": description}},
            session=session
        )
        return self
    
    @do_tx()
    def refresh_secret(self, session=None):
        self.reg_my_ip.get_db().get_collection("applications").find_one_and_update(
            {"group": self.group.name, "name": self.name},
            { "$set": {"secret": gen_secret()}},
            session=session
        )
        return self

    @do_tx()
    def update_app_ips(self, session=None)->'Application':
        view = self.view(session=session)
        app_name = view['name']
        ip_list = self.ips(session=session).view(session=session)

        machines = self.group.machines(session=session)
        
        ips={}
        etag=ip_list['etag']
        last_update=ip_list['last_update']

        # add missing machine
        for machine in machines:
            machine_view = machine.view(session=session)
            if sum([ 1 for tag in machine_view['tags'] if tag == f'used-by: {app_name}']) == 0:
                continue
            # print(machine)
            ips[str(machine_view['_id'])] = {"name": machine_view['name'], "ip": machine_view['ip']}

        md5=md5_hash(json.dumps(ips))
        if md5 != etag:
            last_update = dt.datetime.now(ZoneInfo("Asia/Hong_Kong")).isoformat()
            self.reg_my_ip.get_db().get_collection("ip-list").update_one(
                {"_id": ip_list['_id']},
                {"$set": {"ips":ips, "etag": md5, "last_update": last_update}},
                session=session
            )
        return self

    @do_tx()
    def ips(self, session=None)->'IPList':
        view = self.view(session=session)
        return self.group.ip_list(ObjectId(view['ips']), session=session)
    


class Machine(MongoClinetBased):

    @do_tx()
    def by_name(group: 'Group', name: str, session=None)->'Machine':
        return Machine(group, group.reg_my_ip.get_db().get_collection("machines").find_one({"group": group.name, "name": name}, session=session)['_id'], session=session)


    def __init__(self, group: Group, id: ObjectId, session=None):
        self.group=group
        self.reg_my_ip=group.reg_my_ip
        self.id=id
        view = self.view(session=session)
        self.name = view['name']

    def get_client(self):
        return self.reg_my_ip.get_client()

    
    @do_tx()
    def view(self, session=None):
        rs= self.reg_my_ip.get_db().get_collection("machines").find_one({"_id": self.id}, session=session)
        return rs
        
    @do_tx()
    def edit_description(self, description: str, session=None):
        self.reg_my_ip.get_db().get_collection("machines").find_one_and_update(
            {"group": self.group.name, "name": self.name},
            { "$set": {"description": description}},
            session=session
        )
        return self

    @do_tx()
    def refresh_secret(self, session=None):
        self.reg_my_ip.get_db().get_collection("machines").find_one_and_update(
            {"group": self.group.name, "name": self.name},
            { "$set": {"secret": gen_secret()}},
            session=session
        )
        return self


    @do_tx()
    def edit_machine_tags(self, to_be_added: [str], to_be_removed: [str], session=None):
        machine = self.reg_my_ip.get_db().get_collection("machines").find_one(
            {"group": self.group.name, "name": self.name}, session=session
        )

        affected_apps = []

        tags = machine['tags']
        for var1 in to_be_removed:
            if var1.startswith('used-by: '):
                affected_apps.append(var1[len('used-by: '):])
            tags.remove(var1)
        for var1 in to_be_added:
            if var1 not in tags:
                if var1.startswith('used-by: '):
                    affected_apps.append(var1[len('used-by: '):])
                tags.append(var1)
        
        self.reg_my_ip.get_db().get_collection("machines").find_one_and_update(
            {"group": self.group.name, "name": self.name},
            { "$set": {"tags": tags}},
            session=session
        )
        for app_name in affected_apps:
            if self.group.app_exists(app_name, session=session):
                self.group.app(app_name, session=session).update_app_ips(session=session)

        return self
        
    @do_tx()
    def edit_machine_ip(self, ip: str, session = None):
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            raise Exception(f"IP[{ip}] not valid")

        self.reg_my_ip.get_db().get_collection("machines").find_one_and_update(
            {"group": self.group.name, "name": self.name},
            { "$set": {"ip": ip}},
            session=session
        )

        self.group.update_ips_by_machine(self, session=session)
        return self