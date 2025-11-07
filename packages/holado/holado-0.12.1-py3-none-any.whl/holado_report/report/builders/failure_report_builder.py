
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
import json
from holado_system.system.filesystem.file import File
from holado_xml.xml.xml_file import XMLFile

logger = logging.getLogger(__name__)



class FailureReportBuilder(ReportBuilder):
    """Failure report builder
    Supported formats: 'txt', 'json', 'xml'
    """
    def __init__(self, filepath, file_format='xml', sort_by_nb_scenario=True, exclude_statuses=None, exclude_categories=None):
        self.__file_format = file_format.lower()
        self.__sort_by_nb_scenario = sort_by_nb_scenario
        self.__exclude_statuses = exclude_statuses
        self.__exclude_categories = exclude_categories
        
        if self.__file_format in ['txt', 'json']:
            self.__file = File(filepath, mode='wt')
        elif self.__file_format == 'xml':
            self.__file = XMLFile(filepath, mode='wt')
        else:
            raise TechnicalException(f"Unmanaged format '{self.__file_format}' (possible formats: 'txt', 'json', 'xml')")
        
        self.__failures = {}
        
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
    
    def __file_add_scenario(self, scenario, scenario_report, category_validation, status_validation, step_failed, step_number, scenario_context, step_context):
        if status_validation != "Passed" and step_failed is not None:
            self.__add_failure(scenario, scenario_report, category_validation, status_validation, step_failed, step_number, scenario_context, step_context)
            self.__update_file()
            
    def __add_failure(self, scenario, scenario_report, category_validation, status_validation, step_failed, step_number, scenario_context, step_context):
        from holado_report.report.report_manager import ReportManager
        
        step_error_message = ReportManager.get_step_error_message(step_failed).strip()
        if step_error_message not in self.__failures:
            self.__failures[step_error_message] = []
        
        category_str = f" => {category_validation}" if category_validation else ""
        if self.__file_format == 'txt':
            msg_list = []
            msg_list.append(f"scenario in {ReportManager.format_scenario_short_description(scenario)} - {ReportManager.format_step_short_description(step_failed, step_number, has_failed=True)} - {status_validation}{category_str}")
            msg_list.append(f"    Feature/Scenario: {scenario.feature.name}  =>  {scenario.name}")
            msg_list.append(f"    Report: {scenario_report.report_path}")
            msg_list.append(f"    Tags: -t " + " -t ".join(scenario.feature.tags + scenario.tags))
            msg_list.append(f"    Scenario/Step periods: {ReportManager.format_context_period(scenario_context)} -> {ReportManager.format_context_period(step_context)}")
            msg_scenario = "\n".join(msg_list)
            
            self.__failures[step_error_message].append(msg_scenario)
        elif self.__file_format in ['json', 'xml']:
            scenario_info = {
                'title': f"{ReportManager.format_scenario_short_description(scenario)} - {ReportManager.format_step_short_description(step_failed, step_number, has_failed=True)} - {status_validation}{category_str}",
                'scenario': f"{scenario.feature.name}  =>  {scenario.name}",
                'report': scenario_report.report_path,
                'tags': "-t " + " -t ".join(scenario.feature.tags + scenario.tags),
                'periods': f"{ReportManager.format_context_period(scenario_context)} -> {ReportManager.format_context_period(step_context)}"
                }
            self.__failures[step_error_message].append(scenario_info)
        else:
            raise TechnicalException(f"Unmanaged format '{self.__file_format}' (possible formats: 'txt', 'json')")
    
    def __update_file(self):
        failures = dict(sorted(self.__failures.items(), key=lambda item:-len(item[1]))) if self.__sort_by_nb_scenario else self.__failures
        
        with self.__file as fout:
            if self.__file_format == 'txt':
                for failure, scenarios_messages in failures.items():
                    fout.write(failure + "\n")
                    fout.write("\n")
                    for msg in scenarios_messages:
                        fout.write(Tools.indent_string(4, msg) + "\n")
                        fout.write("\n")
            elif self.__file_format == 'json':
                json_str = json.dumps(failures, ensure_ascii=False, indent=4)
                fout.write(json_str)
            elif self.__file_format == 'xml':
                self.__file_write_failures_xml(fout, failures)
            else:
                raise TechnicalException(f"Unmanaged format '{self.__file_format}' (possible formats: 'txt', 'json')")

    def __file_write_failures_xml(self, fout, failures):
        output_dict = {
            'failures': {
                'failure': [self.__convert_failure_to_output_dict(error_message, scenarios) for error_message, scenarios in failures.items()]
                }
            }
        
        fout.write_dict(output_dict, pretty=True, indent=Tools.indent_string(4, ''))
    
    def __convert_failure_to_output_dict(self, error_message, scenarios):
        res = {}
        
        if "\n" in error_message:
            res['error_message'] = "\n" + Tools.indent_string(12, error_message) + Tools.indent_string(8, "\n")
        else:
            res['error_message'] = error_message
        
        res['scenarios'] = {'scenario': scenarios}
        
        return res
    



