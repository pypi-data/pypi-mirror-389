
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
from holado_system.system.filesystem.file import File
from holado_python.common.tools.datetime import DateTime, FORMAT_DATETIME_ISO
from holado_core.common.exceptions.technical_exception import TechnicalException

logger = logging.getLogger(__name__)



class SummaryScenarioByCategoryReportBuilder(ReportBuilder):
    def __init__(self, filepath, file_format='txt', exclude_statuses=None, exclude_categories=None, with_scenario_end_date=True, with_scenario_period=False, with_step_period=False, use_compact_format=True):
        self.__file_format = file_format.lower()
        self.__exclude_statuses = exclude_statuses
        self.__exclude_categories = exclude_categories
        self.__with_scenario_end_date = with_scenario_end_date
        self.__with_scenario_period = with_scenario_period
        self.__with_step_period = with_step_period
        self.__use_compact_format = use_compact_format
        
        if self.__file_format == 'txt':
            self.__file = File(filepath, auto_flush=False, mode='wt')
        else:
            raise TechnicalException(f"Unmanaged format '{self.__file_format}' (possible formats: 'txt')")
        
        self.__scenarios_by_category = {}
        self.__categories_order = [
                'Regression',
                'Always Failed',
                'Random',
                'Regression but Not Relevant',
                'Always Not Relevant',
                'Random but Not Relevant',
                'Fixed',
                'Always Success',
                'Unknown'
            ]
        
    def build(self):
        '''
        The file is built after each scenario
        '''
        pass
        
    def after_scenario(self, scenario, scenario_report=None):
        from holado_report.report.report_manager import ReportManager
        category_validation, status_validation, step_failed, step_number, scenario_context, step_context = ReportManager.get_current_scenario_status_information(scenario)
        if category_validation is not None:
            ind = category_validation.find(' (')
            category = category_validation[:ind] if ind > 0 else category_validation
        else:
            category = None
        
        # Manage excluded scenario
        if self.__exclude_statuses and status_validation in self.__exclude_statuses:
            return
        if self.__exclude_categories and category in self.__exclude_categories:
            return
        
        if category is not None:
            # Add scenario information into category
            category_str = f" => {category_validation}" if category_validation else ""
            scenario_prefix_str = f"{ReportManager.format_context_period(scenario_context)} " if self.__with_scenario_period \
                                  else f"{DateTime.datetime_2_str(scenario_context.end_datetime, FORMAT_DATETIME_ISO)} - " if self.__with_scenario_end_date \
                                  else ""
            if step_failed:
                step_format_kwargs = {'step_context': step_context if self.__with_step_period else None,
                                      'dt_ref': scenario_context.start_datetime if self.__use_compact_format else None}
                scenario_txt = f"{scenario_prefix_str}{ReportManager.format_scenario_short_description(scenario)} - {ReportManager.format_step_short_description(step_failed, step_number, has_failed=True, **step_format_kwargs)} - {status_validation}{category_str}"
            else:
                scenario_txt = f"{scenario_prefix_str}{ReportManager.format_scenario_short_description(scenario)} - {status_validation}{category_str}"
            
            if category not in self.__scenarios_by_category:
                self.__scenarios_by_category[category] = []
            self.__scenarios_by_category[category].append(scenario_txt)
            
            # Update categories order with unexpected category
            if category not in self.__categories_order:
                self.__categories_order.append(category)
            
            self.__update_file()
        
    def __update_file(self):
        with self.__file as fout:
            for category in self.__categories_order:
                if category in self.__scenarios_by_category:
                    fout.writelines([
                        f"## {category}",
                        ""
                        ])
                    fout.writelines(self.__scenarios_by_category[category])
                    fout.writelines([
                        ""
                        ""
                        ])
    
