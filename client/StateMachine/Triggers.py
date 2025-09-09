from StateMachine.state_map import states,transitions
from StateMachine.screens import screen

class Triggers(object):
    def e_state(self):
        return self.state

    def e_trigger(self, name: str):
        return self.trigger(name)

    def e_empty(self):
        return self.empty()

    def e_set_mass_load_data(self):
        return self.set_mass_load_data()

    def e_view_err_rights(self):
        return self.view_err_rights()

    def e_set_mass_drop_data(self):
        return self.set_mass_drop_data()

    def e_get_users(self):
        return self.get_users()

    def e_view_mass_load_ok(self):
        return self.view_mass_load_ok()

    def e_data(self):
        return self.data()

    def e_view_get_tool(self):
        return self.view_get_tool()

    def e_view_warehouse_group(self):
        return self.view_warehouse_group()

    def e_cnf_ok(self):
        return self.cnf_ok()

    def e_get_history(self):
        return self.get_history()

    def e_btn_select_group(self):
        return self.btn_select_group()

    def e_btn_serial(self):
        return self.btn_serial()

    def e_view_wait(self):
        return self.view_wait()

    def e_view_tool_groups(self):
        return self.view_tool_groups()

    def e_view_history_err(self):
        return self.view_history_err()

    def e_btn_summary(self):
        return self.btn_summary()

    def e_input_name_code(self):
        return self.input_name_code()

    def e_get_rights_by_user_id(self):
        return self.get_rights_by_user_id()

    def e_view_summary(self):
        return self.view_summary()

    def e_timer_event(self):
        return self.timer_event()

    def e_received_command(self):
        return self.received_command()

    def e_get_groups(self):
        return self.get_groups()

    def e_btn_user_id(self):
        return self.btn_user_id()

    def e_btn_history_err(self):
        return self.btn_history_err()

    def e_view_user_operations(self):
        return self.view_user_operations()

    def e_System_reboot(self):
        return self.System_reboot()

    def e_btn_down(self):
        return self.btn_down()

    def e_get_operations(self):
        return self.get_operations()

    def e_btn_up(self):
        return self.btn_up()

    def e_set_mass_drop_tools_by_plan(self):
        return self.set_mass_drop_tools_by_plan()

    def e_get_mass_load_tools_by_free(self):
        return self.get_mass_load_tools_by_free()

    def e_view_err_login(self):
        return self.view_err_login()

    def e_btn_net(self):
        return self.btn_net()

    def e_err_barcode(self):
        return self.err_barcode()

    def e_timeout_err(self):
        return self.timeout_err()

    def e_btn_drop_ok(self):
        return self.btn_drop_ok()

    def e_btn_select_group_names(self):
        return self.btn_select_group_names()

    def e_view_plans(self):
        return self.view_plans()

    def e_err_devices(self):
        return self.err_devices()

    def e_multiline_text(self):
        return self.multiline_text()

    def e_set_mass_load_tools_by_free(self):
        return self.set_mass_load_tools_by_free()

    def e_lock(self):
        return self.lock()

    def e_err_authorization(self):
        return self.err_authorization()

    def e_view_tool_names(self):
        return self.view_tool_names()

    def e_command_is_send(self):
        return self.command_is_send()

    def e_keyboard_status(self):
        return self.keyboard_status()

    def e_set_help(self):
        return self.set_help()

    def e_view_cnf_IP(self):
        return self.view_cnf_IP()

    def e_btn_reboot(self):
        return self.btn_reboot()

    def e_timeout_back(self):
        return self.timeout_back()

    def e_btn_back(self):
        return self.btn_back()

    def e_user_name(self):
        return self.user_name()

    def e_view_mass_drop_ok(self):
        return self.view_mass_drop_ok()

    def e_unlock(self):
        return self.unlock()

    def e_btn_select_users(self):
        return self.btn_select_users()

    def e_view_user_name(self):
        return self.view_user_name()

    def e_btn_plan_id_history(self):
        return self.btn_plan_id_history()

    def e_view_plan_operations(self):
        return self.view_plan_operations()

    def e_set_mass_drop_tools_by_free(self):
        return self.set_mass_drop_tools_by_free()

    def e_plan_id(self):
        return self.plan_id()

    def e_err_critical(self):
        return self.err_critical()

    def e_wait_run(self):
        return self.wait_run()

    def e_err_rights(self):
        return self.err_rights()

    def e_set_mass_load_tools_by_plan(self):
        return self.set_mass_load_tools_by_plan()

    def e_btn_warehouse_select_tools(self):
        return self.btn_warehouse_select_tools()

    def e_get_err(self):
        return self.get_err()

    def e_get_mass_load_tools_by_plan(self):
        return self.get_mass_load_tools_by_plan()

    def e_btn_authorization(self):
        return self.btn_authorization()

    def e_ok(self):
        return self.ok()

    def e_drop_ok(self):
        return self.drop_ok()

    def e_view_mass_load_tools(self):
        return self.view_mass_load_tools()

    def e_type_storekeeper(self):
        return self.type_storekeeper()

    def e_btn_help(self):
        return self.btn_help()

    def e_system_start(self):
        return self.system_start()

    def e_btn_load_ok(self):
        return self.btn_load_ok()

    def e_mass_drop_tools(self):
        return self.mass_drop_tools()

    def e_test(self):
        return self.test()

    def e_send_request_post(self):
        return self.send_request_post()

    def e_load_ok(self):
        return self.load_ok()

    def e_command_ok(self):
        return self.command_ok()

    def e_get_cnf(self):
        return self.get_cnf()

    def e_btn_mass_load(self):
        return self.btn_mass_load()

    def e_view_cnf_serial(self):
        return self.view_cnf_serial()

    def e_btn_warehouse_group(self):
        return self.btn_warehouse_group()

    def e_get_tools_by_plans_id(self):
        return self.get_tools_by_plans_id()

    def e_btn_ok(self):
        return self.btn_ok()

    def e_btn_select_plans(self):
        return self.btn_select_plans()

    def e_view_err(self):
        return self.view_err()

    def e_send_request_get(self):
        return self.send_request_get()

    def e_btn_mass_drop(self):
        return self.btn_mass_drop()

    def e_btn_keyboard(self):
        return self.btn_keyboard()

    def e_view_tools(self):
        return self.view_tools()

    def e_received_ok(self):
        return self.received_ok()

    def e_get_tools_by_group_id(self):
        return self.get_tools_by_group_id()

    def e_view_warehouse_select_tools(self):
        return self.view_warehouse_select_tools()

    def e_get_plans(self):
        return self.get_plans()

    def e_system_stop(self):
        return self.system_stop()

    def e_status(self):
        return self.status()

    def e_err_get_tools_by_plan_id(self):
        return self.err_get_tools_by_plan_id()

    def e_view_users(self):
        return self.view_users()

    def e_btn_off(self):
        return self.btn_off()

    def e_write_ok(self):
        return self.write_ok()

    def e_barcode(self):
        return self.barcode()

    def e_get_mass_drop_tools_by_plan(self):
        return self.get_mass_drop_tools_by_plan()

    def e_write_err(self):
        return self.write_err()

    def e_ready_to_use(self):
        return self.ready_to_use()

    def e_get_mass_drop_tools_by_free(self):
        return self.get_mass_drop_tools_by_free()

    def e_get_help(self):
        return self.get_help()

    def e_btn_tool_name(self):
        return self.btn_tool_name()

    def e_view_ok(self):
        return self.view_ok()

    def e_view_type_admin(self):
        return self.view_type_admin()
