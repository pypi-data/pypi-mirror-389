import unittest

import os
import sys
p=os.path.abspath(os.path.join(os.path.dirname(__file__), '../src'))
sys.path.insert(0, p)
from reg_my_ip_core import RegMyIP

class TestRegMyIP(unittest.TestCase):

    testRegIP = None

    @classmethod
    def setUpClass(cls):
        cls.testRegIP = RegMyIP.from_connection_str(os.getenv('mongo_conn_str'), "reg-my-ip-test")
        # print("setUpClass")
    
    @classmethod
    def tearDownClass(cls):
        cls.testRegIP.get_client().close()
        cls.testRegIP = None
        # print("tearDownClass")

    
    def setUp(self):
        # print("setUp start")
        if self.testRegIP.dbname in self.testRegIP.get_client().list_database_names():
            self.testRegIP.get_client().drop_database(self.testRegIP.dbname)
            # print(f"Complete clear the database[{self.testRegIP.dbname}] for test start up")
        # print("setUp done")
    
    
    def tearDown(self):
        # print("tearDown start")
        if self.testRegIP.dbname in self.testRegIP.get_client().list_database_names():
            self.testRegIP.get_client().drop_database(self.testRegIP.dbname)
            # print(f"Complete clear the database[{self.testRegIP.dbname}] when complete testing")
        # print("tearDown done")

    def get_confs(self)->[]:
        return list(self.testRegIP.get_db().get_collection("conf").find({}))
    
    def get_applications(self)->[]:
        return list(self.testRegIP.get_db().get_collection("applications").find({}))
    
    def get_machines(self)->[]:
        return list(self.testRegIP.get_db().get_collection("machines").find({}))
    
    def get_ip_list(self)->[]:
        return list(self.testRegIP.get_db().get_collection("ip-list").find({}))

    def test_basic_reg_my_ip(self):
        testing_group = "testing-group"
        group_discription = "testing description"
        self.assertFalse(self.testRegIP.group_exists(testing_group),f"Assumming group[{testing_group}] not exists")
        self.assertEqual(len(self.testRegIP.list_groups()), 0, "Assuming there is not group exists yet")
        self.assertEqual(len(self.get_confs()), 0, "Assuming there is not conf exists yet")
        self.assertEqual(len(self.get_applications()), 0, "Assuming there is not application exists yet")
        self.assertEqual(len(self.get_machines()), 0, "Assuming there is not machine exists yet")
        self.assertEqual(len(self.get_ip_list()), 0, "Assuming there is not ip-list exists yet")

        group = self.testRegIP.reg_group(testing_group, group_discription)
        self.assertTrue(self.testRegIP.group_exists(testing_group),f"Assumming group[{testing_group}] exists")
        self.assertEqual(len(self.testRegIP.list_groups()), 1, "Assuming there is not group exists yet")
        self.assertEqual(len(self.get_confs()), 1, "Assuming there is not conf exists yet")
        self.assertEqual(len(self.get_applications()), 0, "Assuming there is not application exists yet")
        self.assertEqual(len(self.get_machines()), 0, "Assuming there is not machine exists yet")
        self.assertEqual(len(self.get_ip_list()), 0, "Assuming there is not ip-list exists yet")

        view = group.view()
        self.assertEqual(view.keys(), {'_id', 'group', 'description', 'secret'})
        self.assertEqual(view['group'], testing_group)
        self.assertEqual(view['description'], group_discription)

        self.assertTrue(self.testRegIP.delete_group(testing_group))
        self.assertFalse(self.testRegIP.group_exists(testing_group),f"Assumming group[{testing_group}] not exists")
        self.assertEqual(len(self.testRegIP.list_groups()), 0, "Assuming there is not group exists yet")
        self.assertEqual(len(self.get_confs()), 0, "Assuming there is not conf exists yet")
        self.assertEqual(len(self.get_applications()), 0, "Assuming there is not application exists yet")
        self.assertEqual(len(self.get_machines()), 0, "Assuming there is not machine exists yet")
        self.assertEqual(len(self.get_ip_list()), 0, "Assuming there is not ip-list exists yet")


    def test_basic_machine(self):
        testing_group = "testing-group"
        group_discription = "testing description"
        machine_name = "m1"
        machine_description = "machine description"
        tags_default = ["tag1", "tag2"]
        self.assertFalse(self.testRegIP.group_exists(testing_group),f"Assumming group[{testing_group}] not exists")
        self.assertEqual(len(self.testRegIP.list_groups()), 0, "Assuming there is not group exists yet")
        self.assertEqual(len(self.get_confs()), 0, "Assuming there is not conf exists yet")
        self.assertEqual(len(self.get_applications()), 0, "Assuming there is not application exists yet")
        self.assertEqual(len(self.get_machines()), 0, "Assuming there is not machine exists yet")
        self.assertEqual(len(self.get_ip_list()), 0, "Assuming there is not ip-list exists yet")

        group = self.testRegIP.reg_group(testing_group, group_discription)
        self.assertTrue(self.testRegIP.group_exists(testing_group),f"Assumming group[{testing_group}] exists")
        self.assertEqual(len(self.testRegIP.list_groups()), 1, "Assuming there is one group")
        self.assertEqual(len(self.get_confs()), 1, "Assuming there is one conf")
        self.assertEqual(len(self.get_applications()), 0, "Assuming there is not application exists yet")
        self.assertEqual(len(self.get_machines()), 0, "Assuming there no machine exists yet")
        self.assertEqual(len(self.get_ip_list()), 0, "Assuming there is not ip-list exists yet")

        machine = group.add_machine(machine_name, machine_description, tags_default)
        self.assertTrue(self.testRegIP.group_exists(testing_group),f"Assumming group[{testing_group}] exists")
        self.assertEqual(len(self.testRegIP.list_groups()), 1, "Assuming there is one group")
        self.assertEqual(len(self.get_confs()), 1, "Assuming there is one conf")
        self.assertEqual(len(self.get_applications()), 0, "Assuming there is not application exists yet")
        self.assertEqual(len(self.get_machines()), 1, "Assuming there is one machine")
        self.assertEqual(len(self.get_ip_list()), 0, "Assuming there is not ip-list exists yet")

        view = machine.view()
        self.assertEqual(view.keys(), {'_id', 'group', 'name', 'description', 'tags', 'ip', 'secret'})
        self.assertEqual(view['group'], testing_group)
        self.assertEqual(view['name'], machine_name)
        self.assertEqual(view['description'], machine_description)
        self.assertEqual(view['tags'], tags_default)
        self.assertEqual(view['ip'], "0.0.0.0")

        
        machine_description = "new description"
        machine.edit_description(machine_description)
        view = machine.view()
        self.assertEqual(view.keys(), {'_id', 'group', 'name', 'description', 'tags', 'ip', 'secret'})
        self.assertEqual(view['group'], testing_group)
        self.assertEqual(view['name'], machine_name)
        self.assertEqual(view['description'], machine_description)
        self.assertEqual(view['tags'], tags_default)
        self.assertEqual(view['ip'], "0.0.0.0")

        new_tags=["tag3", "tag2"]
        remove_tags=["tag1"]
        tags_default = ["tag2", "tag3"]
        machine.edit_machine_tags(new_tags, remove_tags)
        view = machine.view()
        self.assertEqual(view.keys(), {'_id', 'group', 'name', 'description', 'tags', 'ip', 'secret'})
        self.assertEqual(view['group'], testing_group)
        self.assertEqual(view['name'], machine_name)
        self.assertEqual(view['description'], machine_description)
        self.assertEqual(view['tags'], tags_default)
        self.assertEqual(view['ip'], "0.0.0.0")

        new_tags=[]
        remove_tags=["tag4"]
        tags_default = ["tag2", "tag3"]
        with self.assertRaises(Exception):
            machine.edit_machine_tags(new_tags, remove_tags)
        view = machine.view()
        self.assertEqual(view.keys(), {'_id', 'group', 'name', 'description', 'tags', 'ip', 'secret'})
        self.assertEqual(view['group'], testing_group)
        self.assertEqual(view['name'], machine_name)
        self.assertEqual(view['description'], machine_description)
        self.assertEqual(view['tags'], tags_default)
        self.assertEqual(view['ip'], "0.0.0.0")

        group.remove_machine(machine_name)
        self.assertTrue(self.testRegIP.group_exists(testing_group),f"Assumming group[{testing_group}] exists")
        self.assertEqual(len(self.testRegIP.list_groups()), 1, "Assuming there is one group")
        self.assertEqual(len(self.get_confs()), 1, "Assuming there is one conf")
        self.assertEqual(len(self.get_applications()), 0, "Assuming there is not application exists yet")
        self.assertEqual(len(self.get_machines()), 0, "Assuming there no machine exists yet")
        self.assertEqual(len(self.get_ip_list()), 0, "Assuming there is not ip-list exists yet")


    def test_basic_app(self):
        testing_group = "testing-group"
        group_discription = "testing description"
        app_name = "app1"
        app_description = "app description"
        self.assertFalse(self.testRegIP.group_exists(testing_group),f"Assumming group[{testing_group}] not exists")
        self.assertEqual(len(self.testRegIP.list_groups()), 0, "Assuming there is not group exists yet")
        self.assertEqual(len(self.get_confs()), 0, "Assuming there is not conf exists yet")
        self.assertEqual(len(self.get_applications()), 0, "Assuming there is not application exists yet")
        self.assertEqual(len(self.get_machines()), 0, "Assuming there is not machine exists yet")
        self.assertEqual(len(self.get_ip_list()), 0, "Assuming there is not ip-list exists yet")

        group = self.testRegIP.reg_group(testing_group, group_discription)
        self.assertTrue(self.testRegIP.group_exists(testing_group),f"Assumming group[{testing_group}] exists")
        self.assertEqual(len(self.testRegIP.list_groups()), 1, "Assuming there is one group")
        self.assertEqual(len(self.get_confs()), 1, "Assuming there is one conf")
        self.assertEqual(len(self.get_applications()), 0, "Assuming there is not application exists yet")
        self.assertEqual(len(self.get_machines()), 0, "Assuming there no machine exists yet")
        self.assertEqual(len(self.get_ip_list()), 0, "Assuming there is not ip-list exists yet")

        app = group.add_app(app_name, app_description)
        self.assertTrue(self.testRegIP.group_exists(testing_group),f"Assumming group[{testing_group}] exists")
        self.assertEqual(len(self.testRegIP.list_groups()), 1, "Assuming there is one group")
        self.assertEqual(len(self.get_confs()), 1, "Assuming there is one conf")
        self.assertEqual(len(self.get_applications()), 1, "Assuming there is one application")
        self.assertEqual(len(self.get_machines()), 0, "Assuming there no machine exists yet")
        self.assertEqual(len(self.get_ip_list()), 1, "Assuming there is one ip-list")

        self.assertEqual(self.get_applications()[0]['ips'], str(self.get_ip_list()[0]['_id']), "Assuming the ip list in ip-list matching")
        self.assertEqual(app.view().keys(), {'_id', 'group', 'name', 'description', 'secret', 'ips'},"Assuming the app field matches")
        self.assertEqual(app.view()['group'], testing_group)
        self.assertEqual(app.view()['name'], app_name)
        self.assertEqual(app.view()['description'], app_description)
        self.assertEqual(len(app.view()['secret']), 32, "Assume secret is created")

        ips = app.ips()
        self.assertEqual(ips.view().keys(), {'_id', 'ips', 'etag', 'last_update'},"Assuming the ip-list field matches")
        self.assertEqual(len(ips.view()['ips']), 0, "Assume ips is created")
        self.assertIsNotNone(ips.view()['etag'], "Assume etag is created")
        self.assertIsNotNone(ips.view()['last_update'], "Assume last_update is created")
  
        machine_name = "m1"
        machine_description = "machine description"
        tags_default = [f"used-by: {app_name}"]
        machine = group.add_machine(machine_name, machine_description, tags_default)
        self.assertTrue(self.testRegIP.group_exists(testing_group),f"Assumming group[{testing_group}] exists")
        self.assertEqual(len(self.testRegIP.list_groups()), 1, "Assuming there is one group")
        self.assertEqual(len(self.get_confs()), 1, "Assuming there is one conf")
        self.assertEqual(len(self.get_applications()), 1, "Assuming there is one application")
        self.assertEqual(len(self.get_machines()), 1, "Assuming there is one machine")
        self.assertEqual(len(self.get_ip_list()), 1, "Assuming there is one ip-list")

        self.assertEqual(self.get_applications()[0]['ips'], str(self.get_ip_list()[0]['_id']), "Assuming the ip list in ip-list matching")
        self.assertEqual(app.view().keys(), {'_id', 'group', 'name', 'description', 'secret', 'ips'},"Assuming the app field matches")
        self.assertEqual(app.view()['group'], testing_group)
        self.assertEqual(app.view()['name'], app_name)
        self.assertEqual(app.view()['description'], app_description)
        self.assertEqual(len(app.view()['secret']), 32, "Assume secret is created")

        ips = app.ips()
        self.assertEqual(ips.view().keys(), {'_id', 'ips', 'etag', 'last_update'},"Assuming the ip-list field matches")
        self.assertEqual(len(ips.view()['ips']), 1, "Assume ips is created")
        self.assertIsNotNone(ips.view()['etag'], "Assume etag is created")
        self.assertIsNotNone(ips.view()['last_update'], "Assume last_update is created")
        self.assertTrue(str(machine.id) in ips.view()['ips'], "Asumming the machine id is matching")
        self.assertEqual(machine_name, ips.view()['ips'][str(machine.id)]['name'], "Assuming the machine name is matching")
        self.assertEqual("0.0.0.0", ips.view()['ips'][str(machine.id)]['ip'], "Assuming the machine ip is matching")

        self.assertNotEqual(machine.view()['secret'], machine.refresh_secret().view()['secret'], "Assume the secret for machine is updated")
        self.assertNotEqual(app.view()['secret'], app.refresh_secret().view()['secret'], "Assume the secret for app is updated")

        # test edit ip
        new_ip="1.2.3.4"
        machine.edit_machine_ip(new_ip)
        self.assertTrue(self.testRegIP.group_exists(testing_group),f"Assumming group[{testing_group}] exists")
        self.assertEqual(len(self.testRegIP.list_groups()), 1, "Assuming there is one group")
        self.assertEqual(len(self.get_confs()), 1, "Assuming there is one conf")
        self.assertEqual(len(self.get_applications()), 1, "Assuming there is one application")
        self.assertEqual(len(self.get_machines()), 1, "Assuming there is one machine")
        self.assertEqual(len(self.get_ip_list()), 1, "Assuming there is one ip-list")

        self.assertEqual(self.get_applications()[0]['ips'], str(self.get_ip_list()[0]['_id']), "Assuming the ip list in ip-list matching")
        self.assertEqual(app.view().keys(), {'_id', 'group', 'name', 'description', 'secret', 'ips'},"Assuming the app field matches")
        self.assertEqual(app.view()['group'], testing_group)
        self.assertEqual(app.view()['name'], app_name)
        self.assertEqual(app.view()['description'], app_description)
        self.assertEqual(len(app.view()['secret']), 32, "Assume secret is created")

        ips = app.ips()
        self.assertEqual(ips.view().keys(), {'_id', 'ips', 'etag', 'last_update'},"Assuming the ip-list field matches")
        self.assertEqual(len(ips.view()['ips']), 1, "Assume ips is created")
        self.assertIsNotNone(ips.view()['etag'], "Assume etag is created")
        self.assertIsNotNone(ips.view()['last_update'], "Assume last_update is created")
        self.assertTrue(str(machine.id) in ips.view()['ips'], "Asumming the machine id is matching")
        self.assertEqual(machine_name, ips.view()['ips'][str(machine.id)]['name'], "Assuming the machine name is matching")
        self.assertEqual(new_ip, ips.view()['ips'][str(machine.id)]['ip'], "Assuming the machine ip is matching")





if __name__ == '__main__':
    unittest.main()