
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

from holado_core.common.tools.tools import Tools
import logging
from holado_report.report.builders.report_builder import ReportBuilder
from holado_xml.xml.stream_xml_file import StreamXMLFile
from holado_system.system.filesystem.file import File
from holado_core.common.exceptions.technical_exception import TechnicalException

logger = logging.getLogger(__name__)



class DetailedScenarioReportBuilder(ReportBuilder):
    """ Detailed scenario report
    It is dedicated to have a convenient compromise between completeness and shortness.
    
    Notes: XML version of this report is mandatory by test-server as it uses CampaignManager that needs it in its campaign import process.
           For this import process, all periods must be in uncompact format, thus this format is forced in XML format management.
    """
    def __init__(self, filepath, file_format='xml', exclude_statuses=None, exclude_categories=None):
        self.__file_format = file_format.lower()
        self.__exclude_statuses = exclude_statuses
        self.__exclude_categories = exclude_categories
        
        if self.__file_format == 'xml':
            self.__file = StreamXMLFile(filepath, mode='wt')
        elif self.__file_format == 'txt':
            self.__file = File(filepath, mode='wt')
        else:
            raise TechnicalException(f"Unmanaged format '{self.__file_format}' (possible formats: 'txt', 'xml')")
        
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
        # Manage file
        self.__file.close()
        
    def __file_add_scenario(self, scenario, scenario_report, category_validation, status_validation, step_failed, step_number, scenario_context, step_context):
        if self.__file_format == 'xml':
            self.__file_add_scenario_xml(scenario, scenario_report, category_validation, status_validation, step_failed, step_number, scenario_context, step_context)
        else:
            self.__file_add_scenario_txt(scenario, scenario_report, category_validation, status_validation, step_failed, step_number, scenario_context, step_context)
        
    def __file_add_scenario_xml(self, scenario, scenario_report, category_validation, status_validation, step_failed, step_number, scenario_context, step_context):
        from holado_report.report.report_manager import ReportManager
        
        self.__open_file_if_needed()
        
        data = {
            'scenario': {
                'file': ReportManager.format_scenario_short_description(scenario),
                'feature': scenario.feature.name,
                'scenario': scenario.name,
                'scenario_period': ReportManager.format_context_period(scenario_context, use_compact_format=False),
                'report': scenario_report.report_path,
                'tags': "-t " + " -t ".join(scenario.feature.tags + scenario.tags),
                }
            }
        if category_validation:
            data['scenario']['validation_category'] = category_validation
        data['scenario']['validation_status'] = status_validation
        if step_failed is not None:
            failure_data = {
                'step_number': step_number,
                'step_line': step_failed.line
                }
            if step_context is not None:
                failure_data['step_period'] = ReportManager.format_context_period(step_context, use_compact_format=False)

            step_descr = ReportManager.get_step_description(step_failed)
            if "\n" in step_descr:
                failure_data['step'] = "\n" + Tools.indent_string(12, step_descr) + Tools.indent_string(8, "\n")
            else:
                failure_data['step'] = step_descr
                
            step_error_message = ReportManager.get_step_error_message(step_failed)
            if step_error_message:
                if "\n" in step_error_message:
                    failure_data['error_message'] = "\n" + Tools.indent_string(12, step_error_message) + Tools.indent_string(8, "\n")
                else:
                    failure_data['error_message'] = step_error_message
            
            step_error = ReportManager.get_step_error(step_failed)
            if step_error and step_error != step_error_message:
                if "\n" in step_error:
                    failure_data['error'] = "\n" + Tools.indent_string(12, step_error) + Tools.indent_string(8, "\n")
                else:
                    failure_data['error'] = step_error
            data['scenario']['failure'] = failure_data
        elif status_validation != 'Passed':
            data['scenario']['failure'] = "No step failed, it has probably failed on a missing step implementation"
            
        self.__file.write_element_dict(data, pretty=True, indent=Tools.indent_string(4, ''))
        # Add 2 empty lines for more readability
        self.__file.internal_file.writelines(['', ''])
        
    def __file_add_scenario_txt(self, scenario, scenario_report, category_validation, status_validation, step_failed, step_number, scenario_context, step_context):
        from holado_report.report.report_manager import ReportManager
        
        self.__open_file_if_needed()
        
        msg_list = [f"{scenario.filename} - l.{scenario.line}"]
        msg_list.append(f"    Feature: {scenario.feature.name}")
        msg_list.append(f"    Scenario: {scenario.name}")
        msg_list.append(f"    Report: {scenario_report.report_path}")
        msg_list.append(f"    Scenario period: {ReportManager.format_context_period(scenario_context)}")
        msg_list.append(f"    Tags: -t " + " -t ".join(scenario.feature.tags + scenario.tags))
        if category_validation:
            msg_list.append(f"    Validation category: {category_validation}")
        msg_list.append(f"    Validation status: {status_validation}")
        if step_failed is not None:
            msg_list.append(f"    Failure:")
            msg_list.append(f"        Step number-line: {step_number} - l.{step_failed.line}")
            msg_list.append(f"        Step period: {ReportManager.format_context_period(step_context)}")
            step_descr = ReportManager.get_step_description(step_failed)
            if "\n" in step_descr:
                msg_list.append(f"        Step:")
                msg_list.append(Tools.indent_string(12, step_descr))
            else:
                msg_list.append(f"        Step: {step_descr}")
                
            step_error = ReportManager.get_step_error(step_failed)
            if step_error:
                if "\n" in step_error:
                    msg_list.append(f"        Error:")
                    msg_list.append(Tools.indent_string(12, step_error))
                else:
                    msg_list.append(f"        Error: {step_error}")
        else:
            msg_list.append(f"    Failure: No step failed, it has probably failed on a missing step implementation")
        msg_list.append(f"")
        msg_list.append(f"")
            
        self.__file.writelines(msg_list)
    
    def __open_file_if_needed(self):
        if not self.__file.is_open:
            self.__file.open()
    
    
