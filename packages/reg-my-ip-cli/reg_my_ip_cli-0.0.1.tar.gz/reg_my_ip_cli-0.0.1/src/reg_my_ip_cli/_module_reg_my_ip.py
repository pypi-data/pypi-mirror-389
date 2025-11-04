from reg_my_ip_core import RegMyIP
import os
import argparse
import json

def _print_json(data):
    """Helper to pretty-print dictionary data."""
    if data is None:
        print("null")
        return
    # A simple way to handle non-serializable BSON types like ObjectId
    print(json.dumps(data, indent=2, default=str))

def exec():
    parser = argparse.ArgumentParser(description="Manage IP configurations with reg-my-ip.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Sub-command help")

    parser_group = subparsers.add_parser("groups", help="Manage groups")
    # Group commands
    parser_group = subparsers.add_parser("group", help="Manage group")
    parser_group.add_argument("name", help="Group name")
    group_subparsers = parser_group.add_subparsers(dest="action", required=True)
    
    g_create = group_subparsers.add_parser("create", help="Create a new group")
    # g_create.add_argument("--name", "-n", help="Group name")
    g_create.add_argument("--description", "-d", help="Group description", required=True)

    g_delete = group_subparsers.add_parser("delete", help="Delete a group")
    # g_delete.add_argument("--name", "-n", help="Group name")

    # g_list = group_subparsers.add_parser("list", help="List all groups")

    g_show = group_subparsers.add_parser("show", help="Show group details")
    # g_show.add_argument("--name", "-n", help="Group name")

    g_edit_desc = group_subparsers.add_parser("edit-desc", help="Update a group's description")
    g_edit_desc.add_argument("description", help="The new description")

    parser_machines = subparsers.add_parser("machines", help="Manage machines")
    parser_machines.add_argument("--group", "-g", help="Group name")
    # Machine commands
    parser_machine = subparsers.add_parser("machine", help="Manage machine")
    parser_machine.add_argument("--group", "-g", help="Group name")
    parser_machine.add_argument("name", help="Machine name")
    machine_subparsers = parser_machine.add_subparsers(dest="action", required=True)

    m_create = machine_subparsers.add_parser("create", help="Create a new machine in a group")
    m_create.add_argument("--description", "-d", help="Machine description", required=True)
    m_create.add_argument("--tags", nargs='*', help="Tags for the machine", default=[])

    m_delete = machine_subparsers.add_parser("delete", help="Delete a machine from a group")

    m_show = machine_subparsers.add_parser("show", help="Show machine details")

    m_edit_desc = machine_subparsers.add_parser("edit-desc", help="Update a machine's description")
    m_edit_desc.add_argument("description", help="The new description")


    m_update_ip = machine_subparsers.add_parser("update-ip", help="Update a machine's IP address")
    m_update_ip.add_argument("--ip", help="The new IP address")

    m_add_tags = machine_subparsers.add_parser("add-tags", help="Add one or more tags to a machine")
    m_add_tags.add_argument("--tags", nargs='+', help="Tags to add", required=True)

    m_remove_tags = machine_subparsers.add_parser("remove-tags", help="Remove one or more tags from a machine")
    m_remove_tags.add_argument("--tags", nargs='+', help="Tags to remove", required=True)

    m_refresh_secret = machine_subparsers.add_parser("refresh-secret", help="Refresh a machine's secret")

    # Applications commands
    parser_app = subparsers.add_parser("apps", help="Manage applications")
    parser_app.add_argument("--group", "-g", help="Group name")

    # Application commands
    parser_app = subparsers.add_parser("app", help="Manage application")
    parser_app.add_argument("--group", "-g", help="Group name")
    parser_app.add_argument("name", help="Application name")
    app_subparsers = parser_app.add_subparsers(dest="action", required=True)

    a_create = app_subparsers.add_parser("create", help="Create a new application in a group")
    a_create.add_argument("--description", "-d", help="Application description", required=True)

    a_delete = app_subparsers.add_parser("delete", help="Delete an application from a group")

    a_show = app_subparsers.add_parser("show", help="Show application details")

    a_show_ips = app_subparsers.add_parser("show-ips", help="Show IP list for an application")

    a_edit_desc = app_subparsers.add_parser("edit-desc", help="Update an application's description")
    a_edit_desc.add_argument("description", help="The new description")

    a_create = app_subparsers.add_parser("refresh-ips", help="Create a new application in a group")

    a_link = app_subparsers.add_parser("link-to-machine", help="Create a link to machine")
    a_link.add_argument("--machine", "-m", help="Machine name to link to", required=True)

    args = parser.parse_args()

    reg = RegMyIP.from_connection_str(os.getenv("mongo_conn_str"), "reg-my-ip")

    try:
        if args.command == "groups":
            _print_json(reg.list_groups())
        elif args.command == "group":
            if args.action == "create":
                group = reg.reg_group(args.name, args.description)
                _print_json(group.view())
            elif args.action == "delete":
                reg.delete_group(args.name)
                print(f"Group '{args.name}' deleted.")
            elif args.action == "show":
                _print_json(reg.group(args.name).view())
            elif args.action == "edit-desc":
                group = reg.group(args.name).edit_description(args.description)
                _print_json(group.view())
        
        elif args.command == "machines":
                group = reg.group(args.group)
                machines = [m.view()['name'] for m in group.machines()]
                _print_json(machines)
        elif args.command == "machine":
            group = reg.group(args.group)
            if args.action == "create":
                machine = group.add_machine(args.name, args.description, args.tags)
                _print_json(machine.view())
            elif args.action == "delete":
                group.remove_machine(args.name)
                print(f"Machine '{args.name}' from group '{args.group}' deleted.")
            elif args.action == "show":
                _print_json(group.machine(args.name).view())
            elif args.action == "edit-desc":
                machine = group.machine(args.name).edit_machine_description(args.description)
                _print_json(machine.view())
            elif args.action == "update-ip":
                machine = group.machine(args.name).edit_machine_ip(args.ip)
                _print_json(machine.view())
            elif args.action == "add-tags":
                machine = group.machine(args.name).edit_machine_tags(to_be_added=args.tags, to_be_removed=[])
                _print_json(machine.view())
            elif args.action == "remove-tags":
                machine = group.machine(args.name).edit_machine_tags(to_be_added=[], to_be_removed=args.tags)
                _print_json(machine.view())
            elif args.action == "refresh-secret":
                machine = group.machine(args.name).refresh_secret()
                _print_json(machine.view())
        elif args.command == "apps":
            group = reg.group(args.group)
            _print_json(group.apps())
        elif args.command == "app":
            group = reg.group(args.group)
            if args.action == "create":
                app = group.add_app(args.name, args.description)
                _print_json(app.view())
            elif args.action == "delete":
                group.remove_app(args.name)
                print(f"Application '{args.name}' from group '{args.group}' deleted.")
            elif args.action == "show":
                _print_json(group.app(args.name).view())
            elif args.action == "show-ips":
                _print_json(group.app(args.name).ips().view())
            elif args.action == "edit-desc":
                app = group.app(args.name).edit_description(args.description)
                _print_json(app.view())
            elif args.action == "refresh-ips":
                _print_json(group.app(args.name).update_app_ips().view())
            elif args.action == "link-to-machine":
                _print_json(group.machine(args.machine).edit_machine_tags(to_be_added=[f"used-by: {args.name}"], to_be_removed=[]).view())

    except Exception as e:
        print(f"Error: {e}")
        exit(1)