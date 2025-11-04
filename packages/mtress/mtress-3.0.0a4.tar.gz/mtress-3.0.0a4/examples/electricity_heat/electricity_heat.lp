\* Source Pyomo model name=Model *\

min 
objective:
+0.035 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_0)
+0.035 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_1)

s.t.

c_e_BusBlock_balance((_house_1____Air_HE____heat_source_)_0)_:
-1 flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_40_)_0)
-1 flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_30_)_0)
-1 flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_20_)_0)
-1 flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_15_)_0)
+1 flow((_house_1____Air_HE____source_reservoir_)_(_house_1____Air_HE____heat_source_)_0)
= 0

c_e_BusBlock_balance((_house_1____Air_HE____heat_source_)_1)_:
-1 flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_40_)_1)
-1 flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_30_)_1)
-1 flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_20_)_1)
-1 flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_15_)_1)
+1 flow((_house_1____Air_HE____source_reservoir_)_(_house_1____Air_HE____heat_source_)_1)
= 0

c_e_BusBlock_balance((_house_1____Air_HE____utilisation_)_0)_:
-1 flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_40_)_0)
-1 flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_30_)_0)
-1 flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_20_)_0)
-1 flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_15_)_0)
+1 flow((_house_1____Air_HE____source_utilisation_)_(_house_1____Air_HE____utilisation_)_0)
= 0

c_e_BusBlock_balance((_house_1____Air_HE____utilisation_)_1)_:
-1 flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_40_)_1)
-1 flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_30_)_1)
-1 flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_20_)_1)
-1 flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_15_)_1)
+1 flow((_house_1____Air_HE____source_utilisation_)_(_house_1____Air_HE____utilisation_)_1)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_0)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____HeatPump____electricity_)_0)
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____electricity_demand____input_)_0)
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____ResistiveHeater____heater_)_0)
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_0)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_1)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____HeatPump____electricity_)_1)
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____electricity_demand____input_)_1)
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____ResistiveHeater____heater_)_1)
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_1)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____feed_in_)_0)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_0)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____feed_in_)_1)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_1)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_0)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_0)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_1)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_1)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_0)_:
-1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_0)
+1 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_0)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_1)_:
-1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_1)
+1 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_1)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_10_)_0)_:
-1 flow((_house_1____HeatCarrier____T_10_)_(_house_1____ResistiveHeater____heat_10_15_)_0)
-1 flow((_house_1____HeatCarrier____T_10_)_(_house_1____Air_HE____source_15_)_0)
+1 flow((_house_1____HeatPump____HE_in_15_)_(_house_1____HeatCarrier____T_10_)_0)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_10_)_1)_:
-1 flow((_house_1____HeatCarrier____T_10_)_(_house_1____ResistiveHeater____heat_10_15_)_1)
-1 flow((_house_1____HeatCarrier____T_10_)_(_house_1____Air_HE____source_15_)_1)
+1 flow((_house_1____HeatPump____HE_in_15_)_(_house_1____HeatCarrier____T_10_)_1)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_15_)_0)_:
-1 flow((_house_1____HeatCarrier____T_15_)_(_house_1____ResistiveHeater____heat_15_20_)_0)
-1 flow((_house_1____HeatCarrier____T_15_)_(_house_1____HeatPump____HE_in_15_)_0)
-1 flow((_house_1____HeatCarrier____T_15_)_(_house_1____Air_HE____source_20_)_0)
+1 flow((_house_1____ResistiveHeater____heat_10_15_)_(_house_1____HeatCarrier____T_15_)_0)
+1 flow((_house_1____HeatPump____HE_in_20_)_(_house_1____HeatCarrier____T_15_)_0)
+1 flow((_house_1____Air_HE____source_15_)_(_house_1____HeatCarrier____T_15_)_0)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_15_)_1)_:
-1 flow((_house_1____HeatCarrier____T_15_)_(_house_1____ResistiveHeater____heat_15_20_)_1)
-1 flow((_house_1____HeatCarrier____T_15_)_(_house_1____HeatPump____HE_in_15_)_1)
-1 flow((_house_1____HeatCarrier____T_15_)_(_house_1____Air_HE____source_20_)_1)
+1 flow((_house_1____ResistiveHeater____heat_10_15_)_(_house_1____HeatCarrier____T_15_)_1)
+1 flow((_house_1____HeatPump____HE_in_20_)_(_house_1____HeatCarrier____T_15_)_1)
+1 flow((_house_1____Air_HE____source_15_)_(_house_1____HeatCarrier____T_15_)_1)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_20_)_0)_:
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____ResistiveHeater____heat_20_30_)_0)
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____HeatPump____HE_in_20_)_0)
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Air_HE____source_30_)_0)
+1 flow((_house_1____ResistiveHeater____heat_15_20_)_(_house_1____HeatCarrier____T_20_)_0)
+1 flow((_house_1____Air_HE____source_20_)_(_house_1____HeatCarrier____T_20_)_0)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_20_)_1)_:
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____ResistiveHeater____heat_20_30_)_1)
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____HeatPump____HE_in_20_)_1)
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Air_HE____source_30_)_1)
+1 flow((_house_1____ResistiveHeater____heat_15_20_)_(_house_1____HeatCarrier____T_20_)_1)
+1 flow((_house_1____Air_HE____source_20_)_(_house_1____HeatCarrier____T_20_)_1)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_30_)_0)_:
-1 flow((_house_1____HeatCarrier____T_30_)_(_house_1____ResistiveHeater____heat_30_40_)_0)
-1 flow((_house_1____HeatCarrier____T_30_)_(_house_1____HeatPump____HE_out_40_)_0)
-1 flow((_house_1____HeatCarrier____T_30_)_(_house_1____Air_HE____source_40_)_0)
+1 flow((_house_1____ResistiveHeater____heat_20_30_)_(_house_1____HeatCarrier____T_30_)_0)
+1 flow((_house_1____space_heating____heat_exchanger_)_(_house_1____HeatCarrier____T_30_)_0)
+1 flow((_house_1____Air_HE____source_30_)_(_house_1____HeatCarrier____T_30_)_0)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_30_)_1)_:
-1 flow((_house_1____HeatCarrier____T_30_)_(_house_1____ResistiveHeater____heat_30_40_)_1)
-1 flow((_house_1____HeatCarrier____T_30_)_(_house_1____HeatPump____HE_out_40_)_1)
-1 flow((_house_1____HeatCarrier____T_30_)_(_house_1____Air_HE____source_40_)_1)
+1 flow((_house_1____ResistiveHeater____heat_20_30_)_(_house_1____HeatCarrier____T_30_)_1)
+1 flow((_house_1____space_heating____heat_exchanger_)_(_house_1____HeatCarrier____T_30_)_1)
+1 flow((_house_1____Air_HE____source_30_)_(_house_1____HeatCarrier____T_30_)_1)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_40_)_0)_:
-1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____ResistiveHeater____heat_40_55_)_0)
-1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____space_heating____heat_exchanger_)_0)
+1 flow((_house_1____ResistiveHeater____heat_30_40_)_(_house_1____HeatCarrier____T_40_)_0)
+1 flow((_house_1____HeatPump____HE_out_40_)_(_house_1____HeatCarrier____T_40_)_0)
+1 flow((_house_1____Air_HE____source_40_)_(_house_1____HeatCarrier____T_40_)_0)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_40_)_1)_:
-1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____ResistiveHeater____heat_40_55_)_1)
-1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____space_heating____heat_exchanger_)_1)
+1 flow((_house_1____ResistiveHeater____heat_30_40_)_(_house_1____HeatCarrier____T_40_)_1)
+1 flow((_house_1____HeatPump____HE_out_40_)_(_house_1____HeatCarrier____T_40_)_1)
+1 flow((_house_1____Air_HE____source_40_)_(_house_1____HeatCarrier____T_40_)_1)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_55_)_0)_:
+1 flow((_house_1____ResistiveHeater____heat_40_55_)_(_house_1____HeatCarrier____T_55_)_0)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_55_)_1)_:
+1 flow((_house_1____ResistiveHeater____heat_40_55_)_(_house_1____HeatCarrier____T_55_)_1)
= 0

c_e_BusBlock_balance((_house_1____HeatPump____Qin_15_)_0)_:
-1 flow((_house_1____HeatPump____Qin_15_)_(_house_1____HeatPump____cop_15_40_)_0)
+1 flow((_house_1____HeatPump____HE_in_15_)_(_house_1____HeatPump____Qin_15_)_0)
= 0

c_e_BusBlock_balance((_house_1____HeatPump____Qin_15_)_1)_:
-1 flow((_house_1____HeatPump____Qin_15_)_(_house_1____HeatPump____cop_15_40_)_1)
+1 flow((_house_1____HeatPump____HE_in_15_)_(_house_1____HeatPump____Qin_15_)_1)
= 0

c_e_BusBlock_balance((_house_1____HeatPump____Qin_20_)_0)_:
-1 flow((_house_1____HeatPump____Qin_20_)_(_house_1____HeatPump____cop_20_40_)_0)
+1 flow((_house_1____HeatPump____HE_in_20_)_(_house_1____HeatPump____Qin_20_)_0)
= 0

c_e_BusBlock_balance((_house_1____HeatPump____Qin_20_)_1)_:
-1 flow((_house_1____HeatPump____Qin_20_)_(_house_1____HeatPump____cop_20_40_)_1)
+1 flow((_house_1____HeatPump____HE_in_20_)_(_house_1____HeatPump____Qin_20_)_1)
= 0

c_e_BusBlock_balance((_house_1____HeatPump____Qout_40_)_0)_:
-1 flow((_house_1____HeatPump____Qout_40_)_(_house_1____HeatPump____HE_out_40_)_0)
+1 flow((_house_1____HeatPump____cop_15_40_)_(_house_1____HeatPump____Qout_40_)_0)
+1 flow((_house_1____HeatPump____cop_20_40_)_(_house_1____HeatPump____Qout_40_)_0)
= 0

c_e_BusBlock_balance((_house_1____HeatPump____Qout_40_)_1)_:
-1 flow((_house_1____HeatPump____Qout_40_)_(_house_1____HeatPump____HE_out_40_)_1)
+1 flow((_house_1____HeatPump____cop_15_40_)_(_house_1____HeatPump____Qout_40_)_1)
+1 flow((_house_1____HeatPump____cop_20_40_)_(_house_1____HeatPump____Qout_40_)_1)
= 0

c_e_BusBlock_balance((_house_1____HeatPump____electricity_)_0)_:
+1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____HeatPump____electricity_)_0)
-1 flow((_house_1____HeatPump____electricity_)_(_house_1____HeatPump____cop_15_40_)_0)
-1 flow((_house_1____HeatPump____electricity_)_(_house_1____HeatPump____cop_20_40_)_0)
= 0

c_e_BusBlock_balance((_house_1____HeatPump____electricity_)_1)_:
+1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____HeatPump____electricity_)_1)
-1 flow((_house_1____HeatPump____electricity_)_(_house_1____HeatPump____cop_15_40_)_1)
-1 flow((_house_1____HeatPump____electricity_)_(_house_1____HeatPump____cop_20_40_)_1)
= 0

c_e_BusBlock_balance((_house_1____HeatPump____heat_budget_)_0)_:
-1 flow((_house_1____HeatPump____heat_budget_)_(_house_1____HeatPump____cop_15_40_)_0)
-1 flow((_house_1____HeatPump____heat_budget_)_(_house_1____HeatPump____cop_20_40_)_0)
+1 flow((_house_1____HeatPump____heat_budget_source_)_(_house_1____HeatPump____heat_budget_)_0)
= 0

c_e_BusBlock_balance((_house_1____HeatPump____heat_budget_)_1)_:
-1 flow((_house_1____HeatPump____heat_budget_)_(_house_1____HeatPump____cop_15_40_)_1)
-1 flow((_house_1____HeatPump____heat_budget_)_(_house_1____HeatPump____cop_20_40_)_1)
+1 flow((_house_1____HeatPump____heat_budget_source_)_(_house_1____HeatPump____heat_budget_)_1)
= 0

c_e_BusBlock_balance((_house_1____ResistiveHeater____heat_)_0)_:
-1 flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_10_15_)_0)
-1 flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_15_20_)_0)
-1 flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_20_30_)_0)
-1 flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_30_40_)_0)
-1 flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_40_55_)_0)
+1 flow((_house_1____ResistiveHeater____heater_)_(_house_1____ResistiveHeater____heat_)_0)
= 0

c_e_BusBlock_balance((_house_1____ResistiveHeater____heat_)_1)_:
-1 flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_10_15_)_1)
-1 flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_15_20_)_1)
-1 flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_20_30_)_1)
-1 flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_30_40_)_1)
-1 flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_40_55_)_1)
+1 flow((_house_1____ResistiveHeater____heater_)_(_house_1____ResistiveHeater____heat_)_1)
= 0

c_e_BusBlock_balance((_house_1____electricity_demand____input_)_0)_:
+1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____electricity_demand____input_)_0)
= 9

c_e_BusBlock_balance((_house_1____electricity_demand____input_)_1)_:
+1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____electricity_demand____input_)_1)
= 13

c_e_BusBlock_balance((_house_1____space_heating____output_)_0)_:
+1 flow((_house_1____space_heating____heat_exchanger_)_(_house_1____space_heating____output_)_0)
= 50

c_e_BusBlock_balance((_house_1____space_heating____output_)_1)_:
+1 flow((_house_1____space_heating____heat_exchanger_)_(_house_1____space_heating____output_)_1)
= 60

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heat_15_20_)_(_house_1____HeatCarrier____T_15_)_(_house_1____HeatCarrier____T_20_)_0)_:
+1 flow((_house_1____HeatCarrier____T_15_)_(_house_1____ResistiveHeater____heat_15_20_)_0)
-1 flow((_house_1____ResistiveHeater____heat_15_20_)_(_house_1____HeatCarrier____T_20_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heat_15_20_)_(_house_1____ResistiveHeater____heat_)_(_house_1____HeatCarrier____T_20_)_0)_:
+1 flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_15_20_)_0)
-5.805 flow((_house_1____ResistiveHeater____heat_15_20_)_(_house_1____HeatCarrier____T_20_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_40_)_(_house_1____Air_HE____utilisation_)_(_house_1____HeatCarrier____T_40_)_0)_:
+1 flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_40_)_0)
-0.001161 flow((_house_1____Air_HE____source_40_)_(_house_1____HeatCarrier____T_40_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_40_)_(_house_1____Air_HE____heat_source_)_(_house_1____HeatCarrier____T_40_)_0)_:
+1 flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_40_)_0)
-11.61 flow((_house_1____Air_HE____source_40_)_(_house_1____HeatCarrier____T_40_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_40_)_(_house_1____HeatCarrier____T_30_)_(_house_1____HeatCarrier____T_40_)_0)_:
+1 flow((_house_1____HeatCarrier____T_30_)_(_house_1____Air_HE____source_40_)_0)
-1 flow((_house_1____Air_HE____source_40_)_(_house_1____HeatCarrier____T_40_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_30_)_(_house_1____Air_HE____utilisation_)_(_house_1____HeatCarrier____T_30_)_0)_:
+1 flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_30_)_0)
-0.001161 flow((_house_1____Air_HE____source_30_)_(_house_1____HeatCarrier____T_30_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_30_)_(_house_1____Air_HE____heat_source_)_(_house_1____HeatCarrier____T_30_)_0)_:
+1 flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_30_)_0)
-11.61 flow((_house_1____Air_HE____source_30_)_(_house_1____HeatCarrier____T_30_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_30_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_30_)_0)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Air_HE____source_30_)_0)
-1 flow((_house_1____Air_HE____source_30_)_(_house_1____HeatCarrier____T_30_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heater_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____ResistiveHeater____heat_)_0)_:
+1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____ResistiveHeater____heater_)_0)
-1 flow((_house_1____ResistiveHeater____heater_)_(_house_1____ResistiveHeater____heat_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_15_)_(_house_1____Air_HE____utilisation_)_(_house_1____HeatCarrier____T_15_)_0)_:
+1 flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_15_)_0)
-0.0005805 flow((_house_1____Air_HE____source_15_)_(_house_1____HeatCarrier____T_15_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_15_)_(_house_1____Air_HE____heat_source_)_(_house_1____HeatCarrier____T_15_)_0)_:
+1 flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_15_)_0)
-5.805 flow((_house_1____Air_HE____source_15_)_(_house_1____HeatCarrier____T_15_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_15_)_(_house_1____HeatCarrier____T_10_)_(_house_1____HeatCarrier____T_15_)_0)_:
+1 flow((_house_1____HeatCarrier____T_10_)_(_house_1____Air_HE____source_15_)_0)
-1 flow((_house_1____Air_HE____source_15_)_(_house_1____HeatCarrier____T_15_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____HE_in_20_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatPump____Qin_20_)_0)_:
+5.805 flow((_house_1____HeatCarrier____T_20_)_(_house_1____HeatPump____HE_in_20_)_0)
-1 flow((_house_1____HeatPump____HE_in_20_)_(_house_1____HeatPump____Qin_20_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____HE_in_20_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_15_)_0)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____HeatPump____HE_in_20_)_0)
-1 flow((_house_1____HeatPump____HE_in_20_)_(_house_1____HeatCarrier____T_15_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_20_)_(_house_1____Air_HE____utilisation_)_(_house_1____HeatCarrier____T_20_)_0)_:
+1 flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_20_)_0)
-0.0005805 flow((_house_1____Air_HE____source_20_)_(_house_1____HeatCarrier____T_20_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_20_)_(_house_1____HeatCarrier____T_15_)_(_house_1____HeatCarrier____T_20_)_0)_:
+1 flow((_house_1____HeatCarrier____T_15_)_(_house_1____Air_HE____source_20_)_0)
-1 flow((_house_1____Air_HE____source_20_)_(_house_1____HeatCarrier____T_20_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_20_)_(_house_1____Air_HE____heat_source_)_(_house_1____HeatCarrier____T_20_)_0)_:
+1 flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_20_)_0)
-5.805 flow((_house_1____Air_HE____source_20_)_(_house_1____HeatCarrier____T_20_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heat_30_40_)_(_house_1____HeatCarrier____T_30_)_(_house_1____HeatCarrier____T_40_)_0)_:
+1 flow((_house_1____HeatCarrier____T_30_)_(_house_1____ResistiveHeater____heat_30_40_)_0)
-1 flow((_house_1____ResistiveHeater____heat_30_40_)_(_house_1____HeatCarrier____T_40_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heat_30_40_)_(_house_1____ResistiveHeater____heat_)_(_house_1____HeatCarrier____T_40_)_0)_:
+1 flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_30_40_)_0)
-11.61 flow((_house_1____ResistiveHeater____heat_30_40_)_(_house_1____HeatCarrier____T_40_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____HE_in_15_)_(_house_1____HeatCarrier____T_15_)_(_house_1____HeatPump____Qin_15_)_0)_:
+5.805 flow((_house_1____HeatCarrier____T_15_)_(_house_1____HeatPump____HE_in_15_)_0)
-1 flow((_house_1____HeatPump____HE_in_15_)_(_house_1____HeatPump____Qin_15_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____HE_in_15_)_(_house_1____HeatCarrier____T_15_)_(_house_1____HeatCarrier____T_10_)_0)_:
+1 flow((_house_1____HeatCarrier____T_15_)_(_house_1____HeatPump____HE_in_15_)_0)
-1 flow((_house_1____HeatPump____HE_in_15_)_(_house_1____HeatCarrier____T_10_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heat_40_55_)_(_house_1____HeatCarrier____T_40_)_(_house_1____HeatCarrier____T_55_)_0)_:
+1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____ResistiveHeater____heat_40_55_)_0)
-1 flow((_house_1____ResistiveHeater____heat_40_55_)_(_house_1____HeatCarrier____T_55_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heat_40_55_)_(_house_1____ResistiveHeater____heat_)_(_house_1____HeatCarrier____T_55_)_0)_:
+1 flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_40_55_)_0)
-17.415 flow((_house_1____ResistiveHeater____heat_40_55_)_(_house_1____HeatCarrier____T_55_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heat_20_30_)_(_house_1____ResistiveHeater____heat_)_(_house_1____HeatCarrier____T_30_)_0)_:
+1 flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_20_30_)_0)
-11.61 flow((_house_1____ResistiveHeater____heat_20_30_)_(_house_1____HeatCarrier____T_30_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heat_20_30_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_30_)_0)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____ResistiveHeater____heat_20_30_)_0)
-1 flow((_house_1____ResistiveHeater____heat_20_30_)_(_house_1____HeatCarrier____T_30_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____space_heating____heat_exchanger_)_(_house_1____HeatCarrier____T_40_)_(_house_1____space_heating____output_)_0)_:
+11.61 flow((_house_1____HeatCarrier____T_40_)_(_house_1____space_heating____heat_exchanger_)_0)
-1 flow((_house_1____space_heating____heat_exchanger_)_(_house_1____space_heating____output_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____space_heating____heat_exchanger_)_(_house_1____HeatCarrier____T_40_)_(_house_1____HeatCarrier____T_30_)_0)_:
+1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____space_heating____heat_exchanger_)_0)
-1 flow((_house_1____space_heating____heat_exchanger_)_(_house_1____HeatCarrier____T_30_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____HE_out_40_)_(_house_1____HeatPump____Qout_40_)_(_house_1____HeatCarrier____T_40_)_0)_:
+1 flow((_house_1____HeatPump____Qout_40_)_(_house_1____HeatPump____HE_out_40_)_0)
-11.61 flow((_house_1____HeatPump____HE_out_40_)_(_house_1____HeatCarrier____T_40_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____HE_out_40_)_(_house_1____HeatCarrier____T_30_)_(_house_1____HeatCarrier____T_40_)_0)_:
+1 flow((_house_1____HeatCarrier____T_30_)_(_house_1____HeatPump____HE_out_40_)_0)
-1 flow((_house_1____HeatPump____HE_out_40_)_(_house_1____HeatCarrier____T_40_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____cop_15_40_)_(_house_1____HeatPump____Qin_15_)_(_house_1____HeatPump____Qout_40_)_0)_:
+1 flow((_house_1____HeatPump____Qin_15_)_(_house_1____HeatPump____cop_15_40_)_0)
-0.8614983479833693 flow((_house_1____HeatPump____cop_15_40_)_(_house_1____HeatPump____Qout_40_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____cop_15_40_)_(_house_1____HeatPump____electricity_)_(_house_1____HeatPump____Qout_40_)_0)_:
+1 flow((_house_1____HeatPump____electricity_)_(_house_1____HeatPump____cop_15_40_)_0)
-0.13850165201663067 flow((_house_1____HeatPump____cop_15_40_)_(_house_1____HeatPump____Qout_40_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____cop_15_40_)_(_house_1____HeatPump____heat_budget_)_(_house_1____HeatPump____Qout_40_)_0)_:
+1 flow((_house_1____HeatPump____heat_budget_)_(_house_1____HeatPump____cop_15_40_)_0)
-1 flow((_house_1____HeatPump____cop_15_40_)_(_house_1____HeatPump____Qout_40_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heat_10_15_)_(_house_1____ResistiveHeater____heat_)_(_house_1____HeatCarrier____T_15_)_0)_:
+1 flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_10_15_)_0)
-5.805 flow((_house_1____ResistiveHeater____heat_10_15_)_(_house_1____HeatCarrier____T_15_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heat_10_15_)_(_house_1____HeatCarrier____T_10_)_(_house_1____HeatCarrier____T_15_)_0)_:
+1 flow((_house_1____HeatCarrier____T_10_)_(_house_1____ResistiveHeater____heat_10_15_)_0)
-1 flow((_house_1____ResistiveHeater____heat_10_15_)_(_house_1____HeatCarrier____T_15_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____cop_20_40_)_(_house_1____HeatPump____Qin_20_)_(_house_1____HeatPump____Qout_40_)_0)_:
+1 flow((_house_1____HeatPump____Qin_20_)_(_house_1____HeatPump____cop_20_40_)_0)
-0.8923043081493822 flow((_house_1____HeatPump____cop_20_40_)_(_house_1____HeatPump____Qout_40_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____cop_20_40_)_(_house_1____HeatPump____electricity_)_(_house_1____HeatPump____Qout_40_)_0)_:
+1 flow((_house_1____HeatPump____electricity_)_(_house_1____HeatPump____cop_20_40_)_0)
-0.10769569185061777 flow((_house_1____HeatPump____cop_20_40_)_(_house_1____HeatPump____Qout_40_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____cop_20_40_)_(_house_1____HeatPump____heat_budget_)_(_house_1____HeatPump____Qout_40_)_0)_:
+1 flow((_house_1____HeatPump____heat_budget_)_(_house_1____HeatPump____cop_20_40_)_0)
-1 flow((_house_1____HeatPump____cop_20_40_)_(_house_1____HeatPump____Qout_40_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heat_15_20_)_(_house_1____HeatCarrier____T_15_)_(_house_1____HeatCarrier____T_20_)_1)_:
+1 flow((_house_1____HeatCarrier____T_15_)_(_house_1____ResistiveHeater____heat_15_20_)_1)
-1 flow((_house_1____ResistiveHeater____heat_15_20_)_(_house_1____HeatCarrier____T_20_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heat_15_20_)_(_house_1____ResistiveHeater____heat_)_(_house_1____HeatCarrier____T_20_)_1)_:
+1 flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_15_20_)_1)
-5.805 flow((_house_1____ResistiveHeater____heat_15_20_)_(_house_1____HeatCarrier____T_20_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_40_)_(_house_1____Air_HE____utilisation_)_(_house_1____HeatCarrier____T_40_)_1)_:
+1 flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_40_)_1)
-0.001161 flow((_house_1____Air_HE____source_40_)_(_house_1____HeatCarrier____T_40_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_40_)_(_house_1____Air_HE____heat_source_)_(_house_1____HeatCarrier____T_40_)_1)_:
+1 flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_40_)_1)
-11.61 flow((_house_1____Air_HE____source_40_)_(_house_1____HeatCarrier____T_40_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_40_)_(_house_1____HeatCarrier____T_30_)_(_house_1____HeatCarrier____T_40_)_1)_:
+1 flow((_house_1____HeatCarrier____T_30_)_(_house_1____Air_HE____source_40_)_1)
-1 flow((_house_1____Air_HE____source_40_)_(_house_1____HeatCarrier____T_40_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_30_)_(_house_1____Air_HE____utilisation_)_(_house_1____HeatCarrier____T_30_)_1)_:
+1 flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_30_)_1)
-0.001161 flow((_house_1____Air_HE____source_30_)_(_house_1____HeatCarrier____T_30_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_30_)_(_house_1____Air_HE____heat_source_)_(_house_1____HeatCarrier____T_30_)_1)_:
+1 flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_30_)_1)
-11.61 flow((_house_1____Air_HE____source_30_)_(_house_1____HeatCarrier____T_30_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_30_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_30_)_1)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Air_HE____source_30_)_1)
-1 flow((_house_1____Air_HE____source_30_)_(_house_1____HeatCarrier____T_30_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heater_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____ResistiveHeater____heat_)_1)_:
+1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____ResistiveHeater____heater_)_1)
-1 flow((_house_1____ResistiveHeater____heater_)_(_house_1____ResistiveHeater____heat_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_15_)_(_house_1____Air_HE____utilisation_)_(_house_1____HeatCarrier____T_15_)_1)_:
+1 flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_15_)_1)
-0.0005805 flow((_house_1____Air_HE____source_15_)_(_house_1____HeatCarrier____T_15_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_15_)_(_house_1____Air_HE____heat_source_)_(_house_1____HeatCarrier____T_15_)_1)_:
+1 flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_15_)_1)
-5.805 flow((_house_1____Air_HE____source_15_)_(_house_1____HeatCarrier____T_15_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_15_)_(_house_1____HeatCarrier____T_10_)_(_house_1____HeatCarrier____T_15_)_1)_:
+1 flow((_house_1____HeatCarrier____T_10_)_(_house_1____Air_HE____source_15_)_1)
-1 flow((_house_1____Air_HE____source_15_)_(_house_1____HeatCarrier____T_15_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____HE_in_20_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatPump____Qin_20_)_1)_:
+5.805 flow((_house_1____HeatCarrier____T_20_)_(_house_1____HeatPump____HE_in_20_)_1)
-1 flow((_house_1____HeatPump____HE_in_20_)_(_house_1____HeatPump____Qin_20_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____HE_in_20_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_15_)_1)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____HeatPump____HE_in_20_)_1)
-1 flow((_house_1____HeatPump____HE_in_20_)_(_house_1____HeatCarrier____T_15_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_20_)_(_house_1____Air_HE____utilisation_)_(_house_1____HeatCarrier____T_20_)_1)_:
+1 flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_20_)_1)
-0.0005805 flow((_house_1____Air_HE____source_20_)_(_house_1____HeatCarrier____T_20_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_20_)_(_house_1____HeatCarrier____T_15_)_(_house_1____HeatCarrier____T_20_)_1)_:
+1 flow((_house_1____HeatCarrier____T_15_)_(_house_1____Air_HE____source_20_)_1)
-1 flow((_house_1____Air_HE____source_20_)_(_house_1____HeatCarrier____T_20_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____Air_HE____source_20_)_(_house_1____Air_HE____heat_source_)_(_house_1____HeatCarrier____T_20_)_1)_:
+1 flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_20_)_1)
-5.805 flow((_house_1____Air_HE____source_20_)_(_house_1____HeatCarrier____T_20_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heat_30_40_)_(_house_1____HeatCarrier____T_30_)_(_house_1____HeatCarrier____T_40_)_1)_:
+1 flow((_house_1____HeatCarrier____T_30_)_(_house_1____ResistiveHeater____heat_30_40_)_1)
-1 flow((_house_1____ResistiveHeater____heat_30_40_)_(_house_1____HeatCarrier____T_40_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heat_30_40_)_(_house_1____ResistiveHeater____heat_)_(_house_1____HeatCarrier____T_40_)_1)_:
+1 flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_30_40_)_1)
-11.61 flow((_house_1____ResistiveHeater____heat_30_40_)_(_house_1____HeatCarrier____T_40_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____HE_in_15_)_(_house_1____HeatCarrier____T_15_)_(_house_1____HeatPump____Qin_15_)_1)_:
+5.805 flow((_house_1____HeatCarrier____T_15_)_(_house_1____HeatPump____HE_in_15_)_1)
-1 flow((_house_1____HeatPump____HE_in_15_)_(_house_1____HeatPump____Qin_15_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____HE_in_15_)_(_house_1____HeatCarrier____T_15_)_(_house_1____HeatCarrier____T_10_)_1)_:
+1 flow((_house_1____HeatCarrier____T_15_)_(_house_1____HeatPump____HE_in_15_)_1)
-1 flow((_house_1____HeatPump____HE_in_15_)_(_house_1____HeatCarrier____T_10_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heat_40_55_)_(_house_1____HeatCarrier____T_40_)_(_house_1____HeatCarrier____T_55_)_1)_:
+1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____ResistiveHeater____heat_40_55_)_1)
-1 flow((_house_1____ResistiveHeater____heat_40_55_)_(_house_1____HeatCarrier____T_55_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heat_40_55_)_(_house_1____ResistiveHeater____heat_)_(_house_1____HeatCarrier____T_55_)_1)_:
+1 flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_40_55_)_1)
-17.415 flow((_house_1____ResistiveHeater____heat_40_55_)_(_house_1____HeatCarrier____T_55_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heat_20_30_)_(_house_1____ResistiveHeater____heat_)_(_house_1____HeatCarrier____T_30_)_1)_:
+1 flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_20_30_)_1)
-11.61 flow((_house_1____ResistiveHeater____heat_20_30_)_(_house_1____HeatCarrier____T_30_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heat_20_30_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_30_)_1)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____ResistiveHeater____heat_20_30_)_1)
-1 flow((_house_1____ResistiveHeater____heat_20_30_)_(_house_1____HeatCarrier____T_30_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____space_heating____heat_exchanger_)_(_house_1____HeatCarrier____T_40_)_(_house_1____space_heating____output_)_1)_:
+11.61 flow((_house_1____HeatCarrier____T_40_)_(_house_1____space_heating____heat_exchanger_)_1)
-1 flow((_house_1____space_heating____heat_exchanger_)_(_house_1____space_heating____output_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____space_heating____heat_exchanger_)_(_house_1____HeatCarrier____T_40_)_(_house_1____HeatCarrier____T_30_)_1)_:
+1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____space_heating____heat_exchanger_)_1)
-1 flow((_house_1____space_heating____heat_exchanger_)_(_house_1____HeatCarrier____T_30_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____HE_out_40_)_(_house_1____HeatPump____Qout_40_)_(_house_1____HeatCarrier____T_40_)_1)_:
+1 flow((_house_1____HeatPump____Qout_40_)_(_house_1____HeatPump____HE_out_40_)_1)
-11.61 flow((_house_1____HeatPump____HE_out_40_)_(_house_1____HeatCarrier____T_40_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____HE_out_40_)_(_house_1____HeatCarrier____T_30_)_(_house_1____HeatCarrier____T_40_)_1)_:
+1 flow((_house_1____HeatCarrier____T_30_)_(_house_1____HeatPump____HE_out_40_)_1)
-1 flow((_house_1____HeatPump____HE_out_40_)_(_house_1____HeatCarrier____T_40_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____cop_15_40_)_(_house_1____HeatPump____Qin_15_)_(_house_1____HeatPump____Qout_40_)_1)_:
+1 flow((_house_1____HeatPump____Qin_15_)_(_house_1____HeatPump____cop_15_40_)_1)
-0.8614983479833693 flow((_house_1____HeatPump____cop_15_40_)_(_house_1____HeatPump____Qout_40_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____cop_15_40_)_(_house_1____HeatPump____electricity_)_(_house_1____HeatPump____Qout_40_)_1)_:
+1 flow((_house_1____HeatPump____electricity_)_(_house_1____HeatPump____cop_15_40_)_1)
-0.13850165201663067 flow((_house_1____HeatPump____cop_15_40_)_(_house_1____HeatPump____Qout_40_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____cop_15_40_)_(_house_1____HeatPump____heat_budget_)_(_house_1____HeatPump____Qout_40_)_1)_:
+1 flow((_house_1____HeatPump____heat_budget_)_(_house_1____HeatPump____cop_15_40_)_1)
-1 flow((_house_1____HeatPump____cop_15_40_)_(_house_1____HeatPump____Qout_40_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heat_10_15_)_(_house_1____ResistiveHeater____heat_)_(_house_1____HeatCarrier____T_15_)_1)_:
+1 flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_10_15_)_1)
-5.805 flow((_house_1____ResistiveHeater____heat_10_15_)_(_house_1____HeatCarrier____T_15_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____ResistiveHeater____heat_10_15_)_(_house_1____HeatCarrier____T_10_)_(_house_1____HeatCarrier____T_15_)_1)_:
+1 flow((_house_1____HeatCarrier____T_10_)_(_house_1____ResistiveHeater____heat_10_15_)_1)
-1 flow((_house_1____ResistiveHeater____heat_10_15_)_(_house_1____HeatCarrier____T_15_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____cop_20_40_)_(_house_1____HeatPump____Qin_20_)_(_house_1____HeatPump____Qout_40_)_1)_:
+1 flow((_house_1____HeatPump____Qin_20_)_(_house_1____HeatPump____cop_20_40_)_1)
-0.8923043081493822 flow((_house_1____HeatPump____cop_20_40_)_(_house_1____HeatPump____Qout_40_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____cop_20_40_)_(_house_1____HeatPump____electricity_)_(_house_1____HeatPump____Qout_40_)_1)_:
+1 flow((_house_1____HeatPump____electricity_)_(_house_1____HeatPump____cop_20_40_)_1)
-0.10769569185061777 flow((_house_1____HeatPump____cop_20_40_)_(_house_1____HeatPump____Qout_40_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____HeatPump____cop_20_40_)_(_house_1____HeatPump____heat_budget_)_(_house_1____HeatPump____Qout_40_)_1)_:
+1 flow((_house_1____HeatPump____heat_budget_)_(_house_1____HeatPump____cop_20_40_)_1)
-1 flow((_house_1____HeatPump____cop_20_40_)_(_house_1____HeatPump____Qout_40_)_1)
= 0

bounds
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____HeatPump____electricity_)_0) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____HeatPump____electricity_)_1) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____electricity_demand____input_)_0) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____electricity_demand____input_)_1) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____ResistiveHeater____heater_)_0) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____ResistiveHeater____heater_)_1) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_0) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_10_)_(_house_1____ResistiveHeater____heat_10_15_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_10_)_(_house_1____ResistiveHeater____heat_10_15_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_10_)_(_house_1____Air_HE____source_15_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_10_)_(_house_1____Air_HE____source_15_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_15_)_(_house_1____ResistiveHeater____heat_15_20_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_15_)_(_house_1____ResistiveHeater____heat_15_20_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_15_)_(_house_1____HeatPump____HE_in_15_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_15_)_(_house_1____HeatPump____HE_in_15_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_15_)_(_house_1____Air_HE____source_20_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_15_)_(_house_1____Air_HE____source_20_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____ResistiveHeater____heat_20_30_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____ResistiveHeater____heat_20_30_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____HeatPump____HE_in_20_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____HeatPump____HE_in_20_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____Air_HE____source_30_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____Air_HE____source_30_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_30_)_(_house_1____ResistiveHeater____heat_30_40_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_30_)_(_house_1____ResistiveHeater____heat_30_40_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_30_)_(_house_1____HeatPump____HE_out_40_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_30_)_(_house_1____HeatPump____HE_out_40_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_30_)_(_house_1____Air_HE____source_40_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_30_)_(_house_1____Air_HE____source_40_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_40_)_(_house_1____ResistiveHeater____heat_40_55_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_40_)_(_house_1____ResistiveHeater____heat_40_55_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_40_)_(_house_1____space_heating____heat_exchanger_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_40_)_(_house_1____space_heating____heat_exchanger_)_1) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_0) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_1) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_0) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_1) <= +inf
   0 <= flow((_house_1____HeatPump____electricity_)_(_house_1____HeatPump____cop_15_40_)_0) <= +inf
   0 <= flow((_house_1____HeatPump____electricity_)_(_house_1____HeatPump____cop_15_40_)_1) <= +inf
   0 <= flow((_house_1____HeatPump____electricity_)_(_house_1____HeatPump____cop_20_40_)_0) <= +inf
   0 <= flow((_house_1____HeatPump____electricity_)_(_house_1____HeatPump____cop_20_40_)_1) <= +inf
   0 <= flow((_house_1____HeatPump____heat_budget_)_(_house_1____HeatPump____cop_15_40_)_0) <= +inf
   0 <= flow((_house_1____HeatPump____heat_budget_)_(_house_1____HeatPump____cop_15_40_)_1) <= +inf
   0 <= flow((_house_1____HeatPump____heat_budget_)_(_house_1____HeatPump____cop_20_40_)_0) <= +inf
   0 <= flow((_house_1____HeatPump____heat_budget_)_(_house_1____HeatPump____cop_20_40_)_1) <= +inf
   0 <= flow((_house_1____HeatPump____heat_budget_source_)_(_house_1____HeatPump____heat_budget_)_0) <= +inf
   0 <= flow((_house_1____HeatPump____heat_budget_source_)_(_house_1____HeatPump____heat_budget_)_1) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_10_15_)_0) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_10_15_)_1) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_15_20_)_0) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_15_20_)_1) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_20_30_)_0) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_20_30_)_1) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_30_40_)_0) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_30_40_)_1) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_40_55_)_0) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heat_)_(_house_1____ResistiveHeater____heat_40_55_)_1) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heat_10_15_)_(_house_1____HeatCarrier____T_15_)_0) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heat_10_15_)_(_house_1____HeatCarrier____T_15_)_1) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heat_15_20_)_(_house_1____HeatCarrier____T_20_)_0) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heat_15_20_)_(_house_1____HeatCarrier____T_20_)_1) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heat_20_30_)_(_house_1____HeatCarrier____T_30_)_0) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heat_20_30_)_(_house_1____HeatCarrier____T_30_)_1) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heat_30_40_)_(_house_1____HeatCarrier____T_40_)_0) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heat_30_40_)_(_house_1____HeatCarrier____T_40_)_1) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heat_40_55_)_(_house_1____HeatCarrier____T_55_)_0) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heat_40_55_)_(_house_1____HeatCarrier____T_55_)_1) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heater_)_(_house_1____ResistiveHeater____heat_)_0) <= +inf
   0 <= flow((_house_1____ResistiveHeater____heater_)_(_house_1____ResistiveHeater____heat_)_1) <= +inf
   0 <= flow((_house_1____space_heating____heat_exchanger_)_(_house_1____space_heating____output_)_0) <= +inf
   0 <= flow((_house_1____space_heating____heat_exchanger_)_(_house_1____space_heating____output_)_1) <= +inf
   0 <= flow((_house_1____space_heating____heat_exchanger_)_(_house_1____HeatCarrier____T_30_)_0) <= +inf
   0 <= flow((_house_1____space_heating____heat_exchanger_)_(_house_1____HeatCarrier____T_30_)_1) <= +inf
   0 <= flow((_house_1____HeatPump____Qout_40_)_(_house_1____HeatPump____HE_out_40_)_0) <= +inf
   0 <= flow((_house_1____HeatPump____Qout_40_)_(_house_1____HeatPump____HE_out_40_)_1) <= +inf
   0 <= flow((_house_1____HeatPump____HE_out_40_)_(_house_1____HeatCarrier____T_40_)_0) <= +inf
   0 <= flow((_house_1____HeatPump____HE_out_40_)_(_house_1____HeatCarrier____T_40_)_1) <= +inf
   0 <= flow((_house_1____HeatPump____Qin_15_)_(_house_1____HeatPump____cop_15_40_)_0) <= +inf
   0 <= flow((_house_1____HeatPump____Qin_15_)_(_house_1____HeatPump____cop_15_40_)_1) <= +inf
   0 <= flow((_house_1____HeatPump____HE_in_15_)_(_house_1____HeatPump____Qin_15_)_0) <= +inf
   0 <= flow((_house_1____HeatPump____HE_in_15_)_(_house_1____HeatPump____Qin_15_)_1) <= +inf
   0 <= flow((_house_1____HeatPump____HE_in_15_)_(_house_1____HeatCarrier____T_10_)_0) <= +inf
   0 <= flow((_house_1____HeatPump____HE_in_15_)_(_house_1____HeatCarrier____T_10_)_1) <= +inf
   0 <= flow((_house_1____HeatPump____cop_15_40_)_(_house_1____HeatPump____Qout_40_)_0) <= +inf
   0 <= flow((_house_1____HeatPump____cop_15_40_)_(_house_1____HeatPump____Qout_40_)_1) <= +inf
   0 <= flow((_house_1____HeatPump____Qin_20_)_(_house_1____HeatPump____cop_20_40_)_0) <= +inf
   0 <= flow((_house_1____HeatPump____Qin_20_)_(_house_1____HeatPump____cop_20_40_)_1) <= +inf
   0 <= flow((_house_1____HeatPump____HE_in_20_)_(_house_1____HeatPump____Qin_20_)_0) <= +inf
   0 <= flow((_house_1____HeatPump____HE_in_20_)_(_house_1____HeatPump____Qin_20_)_1) <= +inf
   0 <= flow((_house_1____HeatPump____HE_in_20_)_(_house_1____HeatCarrier____T_15_)_0) <= +inf
   0 <= flow((_house_1____HeatPump____HE_in_20_)_(_house_1____HeatCarrier____T_15_)_1) <= +inf
   0 <= flow((_house_1____HeatPump____cop_20_40_)_(_house_1____HeatPump____Qout_40_)_0) <= +inf
   0 <= flow((_house_1____HeatPump____cop_20_40_)_(_house_1____HeatPump____Qout_40_)_1) <= +inf
   0.0 <= flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_40_)_0) <= 0.0
   0.0 <= flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_40_)_1) <= 0.0
   0.0 <= flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_30_)_0) <= 0.0
   0.0 <= flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_30_)_1) <= 0.0
   0.0 <= flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_20_)_0) <= 10000.0
   0.0 <= flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_20_)_1) <= 10000.0
   0.0 <= flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_15_)_0) <= 10000.0
   0.0 <= flow((_house_1____Air_HE____heat_source_)_(_house_1____Air_HE____source_15_)_1) <= 10000.0
   0.0 <= flow((_house_1____Air_HE____source_reservoir_)_(_house_1____Air_HE____heat_source_)_0) <= 10000.0
   0.0 <= flow((_house_1____Air_HE____source_reservoir_)_(_house_1____Air_HE____heat_source_)_1) <= 10000.0
   0 <= flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_40_)_0) <= +inf
   0 <= flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_40_)_1) <= +inf
   0 <= flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_30_)_0) <= +inf
   0 <= flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_30_)_1) <= +inf
   0 <= flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_20_)_0) <= +inf
   0 <= flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_20_)_1) <= +inf
   0 <= flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_15_)_0) <= +inf
   0 <= flow((_house_1____Air_HE____utilisation_)_(_house_1____Air_HE____source_15_)_1) <= +inf
   0 <= flow((_house_1____Air_HE____source_utilisation_)_(_house_1____Air_HE____utilisation_)_0) <= 1
   0 <= flow((_house_1____Air_HE____source_utilisation_)_(_house_1____Air_HE____utilisation_)_1) <= 1
   0 <= flow((_house_1____Air_HE____source_40_)_(_house_1____HeatCarrier____T_40_)_0) <= +inf
   0 <= flow((_house_1____Air_HE____source_40_)_(_house_1____HeatCarrier____T_40_)_1) <= +inf
   0 <= flow((_house_1____Air_HE____source_30_)_(_house_1____HeatCarrier____T_30_)_0) <= +inf
   0 <= flow((_house_1____Air_HE____source_30_)_(_house_1____HeatCarrier____T_30_)_1) <= +inf
   0 <= flow((_house_1____Air_HE____source_20_)_(_house_1____HeatCarrier____T_20_)_0) <= +inf
   0 <= flow((_house_1____Air_HE____source_20_)_(_house_1____HeatCarrier____T_20_)_1) <= +inf
   0 <= flow((_house_1____Air_HE____source_15_)_(_house_1____HeatCarrier____T_15_)_0) <= +inf
   0 <= flow((_house_1____Air_HE____source_15_)_(_house_1____HeatCarrier____T_15_)_1) <= +inf
end
