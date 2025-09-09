# -*- coding: utf-8 -*-
    
states = [
    {'name': 'write_db_help'},
    {'name': 'read_db_help'},
    {'name': 'read_db_groups'},
    {'name': 'read_db_operations'},
    {'name': 'read_db_tools_by_group_id'},
    {'name': 'read_db_tools_by_plans_id'},
    {'name': 'read_db_rights_by_user_id'},
    {'name': 'write_db_rights_by_user_id'},
    {'name': 'read_db_plans'},
    {'name': 'write_db_plans'},
    {'name': 'write_db_plans'},
    {'name': 'write_db_users'},
    {'name': 'read_db_users'},
    {'name': 'read_db_err'},
    {'name': 'read_db_history'},
    {'name': 'write_db_mass_drop_tools_by_free'},
    {'name': 'read_db_mass_drop_tools_by_free'},
    {'name': 'read_db_mass_drop_tools_by_plan'},
    {'name': 'write_db_mass_drop_tools_by_plan'},
    {'name': 'read_db_mass_load_tools_by_free'},
    {'name': 'read_db_mass_load_tools_by_plan'},
    {'name': 'write_db_mass_load_tools_by_free'},
    {'name': 'write_db_mass_load_tools_by_plan'},
    {'name': 'read_cnf_signature'},
    {'name': 'read_cnf'},
    {'name': 'http_parse_answer'},
    {'name': 'http_post_request_send_data'},
    {'name': 'http_wait_get_answer'},
    {'name': 'http_wait_post_answer'},
    # {'name': 'http_get_request_take_command'},
    {'name': 'cmd_run_timeout_post_back'},
    {'name': 'cmd_run_timeout_get_back'},
]

transitions = [
    {'trigger': 'write_ok', 'source': 'write_db_help', 'dest': 'http_post_request_send_data'},
    {'trigger': 'write_err', 'source': 'write_db_help', 'dest': 'http_post_request_send_data'},
    {'trigger': 'data', 'source': 'read_db_help', 'dest': 'http_post_request_send_data'},
    {'trigger': 'data', 'source': 'read_db_groups', 'dest': 'http_post_request_send_data'},
    {'trigger': 'data', 'source': 'read_db_tools_by_group_id', 'dest': 'http_post_request_send_data'},
    {'trigger': 'data', 'source': 'read_cnf', 'dest': 'http_post_request_send_data'},
    {'trigger': 'data', 'source': 'read_db_operations', 'dest': 'http_post_request_send_data'},
    {'trigger': 'data', 'source': 'read_db_mass_load_tools_by_plan', 'dest': 'http_post_request_send_data'},
    {'trigger': 'data', 'source': 'read_db_mass_drop_tools_by_plan', 'dest': 'http_post_request_send_data'},
    {'trigger': 'data', 'source': 'read_db_tools_by_plans_id', 'dest': 'http_post_request_send_data'},
    {'trigger': 'data', 'source': 'read_db_mass_load_tools_by_free', 'dest': 'http_post_request_send_data'},
    {'trigger': 'data', 'source': 'read_db_rights_by_user_id', 'dest': 'http_post_request_send_data'},
    {'trigger': 'data', 'source': 'read_db_mass_drop_tools_by_free', 'dest': 'http_post_request_send_data'},
    {'trigger': 'write_err', 'source': 'write_db_rights_by_user_id', 'dest': 'http_post_request_send_data'},
    {'trigger': 'write_ok', 'source': 'write_db_rights_by_user_id', 'dest': 'http_post_request_send_data'},
    {'trigger': 'write_ok', 'source': 'write_db_mass_drop_tools_by_free', 'dest': 'http_post_request_send_data'},
    {'trigger': 'write_err', 'source': 'write_db_mass_drop_tools_by_free', 'dest': 'http_post_request_send_data'},
    {'trigger': 'write_err', 'source': 'write_db_users', 'dest': 'http_post_request_send_data'},
    {'trigger': 'write_ok', 'source': 'write_db_users', 'dest': 'http_post_request_send_data'},
    {'trigger': 'data', 'source': 'read_db_plans', 'dest': 'http_post_request_send_data'},
    {'trigger': 'write_err', 'source': 'write_db_mass_load_tools_by_free', 'dest': 'http_post_request_send_data'},
    {'trigger': 'write_ok', 'source': 'write_db_mass_load_tools_by_free', 'dest': 'http_post_request_send_data'},
    {'trigger': 'write_ok', 'source': 'write_db_plans', 'dest': 'http_post_request_send_data'},
    {'trigger': 'write_err', 'source': 'write_db_plans', 'dest': 'http_post_request_send_data'},
    {'trigger': 'data', 'source': 'read_db_users', 'dest': 'http_post_request_send_data'},
    {'trigger': 'data', 'source': 'read_db_err', 'dest': 'http_post_request_send_data'},
    {'trigger': 'get_cnf', 'source': 'http_parse_answer', 'dest': 'read_cnf'},
    {'trigger': 'get_mass_load_tools_by_free', 'source': 'http_parse_answer', 'dest': 'read_db_mass_load_tools_by_free'},
    {'trigger': 'get_rights_by_user_id', 'source': 'http_parse_answer', 'dest': 'read_db_rights_by_user_id'},
    {'trigger': 'get_help', 'source': 'http_parse_answer', 'dest': 'read_db_help'},
    {'trigger': 'set_mass_drop_tools_by_free', 'source': 'http_parse_answer', 'dest': 'write_cnf_unlock_drop'},
    {'trigger': 'get_mass_load_tools_by_plan', 'source': 'http_parse_answer', 'dest': 'read_db_mass_load_tools_by_plan'},
    {'trigger': 'set_mass_load_tools_by_plan', 'source': 'http_parse_answer', 'dest': 'write_cnf_unlock_load'},
    {'trigger': 'get_plans', 'source': 'http_parse_answer', 'dest': 'read_db_plans'},
    {'trigger': 'get_operations', 'source': 'http_parse_answer', 'dest': 'read_db_operations'},
    {'trigger': 'empty', 'source': 'http_parse_answer', 'dest': 'cmd_empty'},
    {'trigger': 'set_mass_drop_tools_by_plan', 'source': 'http_parse_answer', 'dest': 'write_cnf_unlock_drop'},
    {'trigger': 'get_command', 'source': 'http_parse_answer', 'dest': 'http_post_request_send_data'},
    {'trigger': 'get_users', 'source': 'http_parse_answer', 'dest': 'write_db_users'},
    {'trigger': 'get_err', 'source': 'http_parse_answer', 'dest': 'read_db_err'},
    {'trigger': 'get_mass_drop_tools_by_free', 'source': 'http_parse_answer', 'dest': 'read_db_mass_drop_tools_by_free'},
    {'trigger': 'get_groups', 'source': 'http_parse_answer', 'dest': 'read_db_groups'},
    {'trigger': 'get_mass_drop_tools_by_plan', 'source': 'http_parse_answer', 'dest': 'read_db_mass_drop_tools_by_plan'},
    {'trigger': 'get_history', 'source': 'http_parse_answer', 'dest': 'read_db_history'},
    {'trigger': 'set_mass_load_tools_by_free', 'source': 'http_parse_answer', 'dest': 'write_cnf_unlock_load'},
    {'trigger': 'get_rights_by_user_id', 'source': 'http_parse_answer', 'dest': 'write_db_rights_by_user_id'},
    {'trigger': 'set_help', 'source': 'http_parse_answer', 'dest': 'write_db_help'},
    {'trigger': 'get_users', 'source': 'http_parse_answer', 'dest': 'read_db_users'},
    {'trigger': 'get_tools_by_group_id', 'source': 'http_parse_answer', 'dest': 'read_db_tools_by_group_id'},
    {'trigger': 'get_tools_by_plans_id', 'source': 'http_parse_answer', 'dest': 'read_db_tools_by_plans_id'},
    {'trigger': 'write_ok', 'source': 'write_db_mass_drop_tools_by_plan', 'dest': 'http_post_request_send_data'},
    {'trigger': 'write_err', 'source': 'write_db_mass_drop_tools_by_plan', 'dest': 'http_post_request_send_data'},
    {'trigger': 'data', 'source': 'read_db_history', 'dest': 'http_post_request_send_data'},
    {'trigger': 'send_request_post', 'source': 'http_post_request_send_data', 'dest': 'cmd_run_timeout_post_back'},
    {'trigger': 'set_plans', 'source': 'http_post_request_send_data', 'dest': 'write_db_plans'},
    {'trigger': 'received_command', 'source': 'http_wait_get_answer', 'dest': 'http_parse_answer'},
    {'trigger': 'timeout_err', 'source': 'http_wait_get_answer', 'dest': 'write_db_err_request'},
    {'trigger': 'wait_run', 'source': 'cmd_run_timeout_post_back', 'dest': 'http_wait_post_answer'},
    {'trigger': 'write_ok', 'source': 'write_db_mass_load_tools_by_plan', 'dest': 'http_post_request_send_data'},
    {'trigger': 'write_err', 'source': 'write_db_mass_load_tools_by_plan', 'dest': 'http_post_request_send_data'},
    {'trigger': 'received_ok', 'source': 'http_wait_post_answer', 'dest': 'http_parse_answer'},
    {'trigger': 'timeout_err', 'source': 'http_wait_post_answer', 'dest': 'write_db_err_request'},
    {'trigger': 'wait_run', 'source': 'cmd_run_timeout_get_back', 'dest': 'http_wait_get_answer'},
    # {'trigger': 'send_request_get', 'source': 'http_get_request_take_command', 'dest': 'cmd_run_timeout_get_back'},
    # {'trigger': 'get_token', 'source': 'read_cnf_signature', 'dest': 'http_get_request_take_command'},
]



"""
write_db_help
read_db_help
read_db_groups
read_db_operations
read_db_tools_by_group_id
read_db_tools_by_plans_id
read_db_rights_by_user_id
write_db_rights_by_user_id
read_db_plans
write_db_plans
write_db_plans
write_db_users
read_db_users
read_db_err
read_db_history
write_db_mass_drop_tools_by_free
read_db_mass_drop_tools_by_free
read_db_mass_drop_tools_by_plan
write_db_mass_drop_tools_by_plan
read_db_mass_load_tools_by_free
read_db_mass_load_tools_by_plan
write_db_mass_load_tools_by_free
write_db_mass_load_tools_by_plan
read_cnf_signature
read_cnf
"""