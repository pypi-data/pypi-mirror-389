
#################################################
# HolAdo (Holistic Automation do)
#
# (C) Copyright 2021-2025 by Eric Klumpp
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# The Software is provided “as is”, without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other dealings in the Software.
#################################################

import logging
from holado_report.report.builders.report_builder import ReportBuilder
from holado_core.common.tools.tools import Tools
from holado_core.common.exceptions.technical_exception import TechnicalException
from holado_system.system.filesystem.file import File

logger = logging.getLogger(__name__)



class ShortScenarioReportBuilder(ReportBuilder):
    def __init__(self, filepath, file_format='txt', exclude_statuses=None, exclude_categories=None, use_compact_format=True):
        self.__file_format = file_format.lower()
        self.__exclude_statuses = exclude_statuses
        self.__exclude_categories = exclude_categories
        self.__use_compact_format = use_compact_format
        
        if self.__file_format == 'txt':
            self.__file = File(filepath, mode='wt')
        else:
            raise TechnicalException(f"Unmanaged format '{self.__file_format}' (possible formats: 'txt')")
        
    def build(self):
        '''
        The file is built after each scenario
        '''
        pass
        
    def after_scenario(self, scenario, scenario_report=None):
        from holado_report.report.report_manager import ReportManager
        category_validation, status_validation, step_failed, step_number, scenario_context, step_context = ReportManager.get_current_scenario_status_information(scenario)
        
        # Manage excluded scenarios
        if self.__exclude_statuses and status_validation in self.__exclude_statuses:
            return
        if category_validation is not None and self.__exclude_categories:
            ind = category_validation.find(' (')
            category = category_validation[:ind] if ind > 0 else category_validation
            if category in self.__exclude_categories:
                return
        
        self.__file_add_scenario(scenario, scenario_report, category_validation, status_validation, step_failed, step_number, scenario_context, step_context)
        
    def after_all(self):
        # Manage file fail
        self.__file.close()
        
    def __file_add_scenario(self, scenario, scenario_report, category_validation, status_validation, step_failed, step_number, scenario_context, step_context):
        from holado_report.report.report_manager import ReportManager
        
        self.__open_file_if_needed()
        
        msg_list = []
        category_str = f" => {category_validation}" if category_validation else ""
        if step_failed:
            msg_list.append(f"scenario in {ReportManager.format_scenario_short_description(scenario)} - {ReportManager.format_step_short_description(step_failed, step_number, has_failed=True)} - {status_validation}{category_str}")
        else:
            msg_list.append(f"scenario in {ReportManager.format_scenario_short_description(scenario)} - {status_validation}{category_str}")
        msg_list.append(f"    Feature/Scenario: {scenario.feature.name}  =>  {scenario.name}")
        msg_list.append(f"    Report: {scenario_report.report_path}")
        msg_list.append(f"    Tags: -t " + " -t ".join(scenario.feature.tags + scenario.tags))
        if step_context:
            msg_list.append(f"    Scenario/Step periods: {ReportManager.format_context_period(scenario_context, use_compact_format=self.__use_compact_format)} -> {ReportManager.format_context_period(step_context, dt_ref=scenario_context.start_datetime, use_compact_format=self.__use_compact_format)}")
        else:
            msg_list.append(f"    Scenario period: {ReportManager.format_context_period(scenario_context, use_compact_format=self.__use_compact_format)}")
        step_error_message = ReportManager.get_step_error_message(step_failed)
        if step_error_message:
            if "\n" in step_error_message:
                msg_list.append(f"    Error message: ")
                msg_list.append(Tools.indent_string(8, step_error_message))
            else:
                msg_list.append(f"    Error message: {step_error_message}")
        msg_list.append(f"")
        msg_list.append(f"")
        
        self.__file.writelines(msg_list)
    
    def __open_file_if_needed(self):
        if not self.__file.is_open:
            self.__file.open()
    
