import reg_my_ip_core as project
import os
from j_vault_http_client_xethhung12 import client
def main():
    client.load_to_env()
    print("helloworld")
    
    # reg_my_ip =project.RegMyIP.from_connection_str(os.getenv("mongo_conn_str"), "reg-my-ip") print(reg_my_ip.list_groups())
    # print(reg_my_ip.group_exists("xeth-is-owner"))
    # print(reg_my_ip.delete_group("xeth-is-owner"))
    # print(reg_my_ip.reg_group("xeth-is-owner", "testing description").view())
    # print(reg_my_ip.group("xeth-is-owner").view())
    # print(reg_my_ip.group("xeth-is-owner").machine_exists("www.specialtiesexpress.com"))
    # print(reg_my_ip.group("xeth-is-owner").remove_machine("www.specialtiesexpress.com"))
    # print(reg_my_ip.group("xeth-is-owner").add_machine(
    #     "www.specialtiesexpress.com",
    #     "web page",
    #     ["web", "ui"]
    #     ).view()
    # )
    # print(reg_my_ip.group("xeth-is-owner").machine(
    #     "www.specialtiesexpress.com",
    #     ).view())
    # print(reg_my_ip.group("xeth-is-owner")
    #     .machine( "www.specialtiesexpress.com")
    #     .edit_machine_description("test update description1")
    #     .view()
    # )
    # print(reg_my_ip.group("xeth-is-owner")
    #     .machine( "www.specialtiesexpress.com")
    #     .edit_machine_tags(["t1", "t2", "used-by: backup-app"], ["ui"])
    #     .view()
    # )
    # # print(reg_my_ip.group("xeth-is-owner")
    # #     .add_new_ip_list().view()
    # # )
    # print(reg_my_ip.group("xeth-is-owner")
    #     .remove_app("backup-app")
    # )
    # print(reg_my_ip.group("xeth-is-owner")
    #     .add_app("backup-app", "backup app").view()
    # )
    # print(reg_my_ip.group("xeth-is-owner")
    #     .list_app()
    # )
    # print(reg_my_ip.group("xeth-is-owner")
    #     .app_exists("backup-app")
    # )
    # print("+++++++++++++")
    # print(reg_my_ip.group("xeth-is-owner")
    #     .app("backup-app").ips().view()
    # )
    # print(
    #     reg_my_ip.group("xeth-is-owner")
    #     .machine("www.specialtiesexpress.com")
    #     .edit_machine_ip("127.0.0.1")
    # )
    # print(reg_my_ip.group("xeth-is-owner")
    #     .app("backup-app").ips().view()
    # )

    # print(reg_my_ip.group("xeth-is-owner")
    #     .machine("m1").edit_machine_tags(["used-by: app1"], [])
    # )
    # print(reg_my_ip.group("xeth-is-owner")
    #     .machine("m1").edit_machine_tags([], ["used-by: app1"])
    # )
