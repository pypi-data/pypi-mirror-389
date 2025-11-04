\* Source Pyomo model name=Model *\

min 
objective:
+1000000000.0 flow((_house_1____HeatCarrier____T_20_)_(_house_1____SlackNode____excess_energy_)_0)
+1000000000.0 flow((_house_1____HeatCarrier____T_20_)_(_house_1____SlackNode____excess_energy_)_1)
+1000000000.0 flow((_house_1____HeatCarrier____T_20_)_(_house_1____SlackNode____excess_energy_)_2)
+1000000000.0 flow((_house_1____HeatCarrier____T_40_)_(_house_1____SlackNode____excess_energy_)_0)
+1000000000.0 flow((_house_1____HeatCarrier____T_40_)_(_house_1____SlackNode____excess_energy_)_1)
+1000000000.0 flow((_house_1____HeatCarrier____T_40_)_(_house_1____SlackNode____excess_energy_)_2)
+7e-05 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_0)
+7e-05 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_1)
+7e-05 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_2)
+1000000000.0 flow((_house_1____SlackNode____missing_energy_)_(_house_1____HeatCarrier____T_20_)_0)
+1000000000.0 flow((_house_1____SlackNode____missing_energy_)_(_house_1____HeatCarrier____T_20_)_1)
+1000000000.0 flow((_house_1____SlackNode____missing_energy_)_(_house_1____HeatCarrier____T_20_)_2)
+1000000000.0 flow((_house_1____SlackNode____missing_energy_)_(_house_1____HeatCarrier____T_40_)_0)
+1000000000.0 flow((_house_1____SlackNode____missing_energy_)_(_house_1____HeatCarrier____T_40_)_1)
+1000000000.0 flow((_house_1____SlackNode____missing_energy_)_(_house_1____HeatCarrier____T_40_)_2)

s.t.

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_0)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0)
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_0)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_1)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1)
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_1)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_2)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2)
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_2)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____feed_in_)_0)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_0)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____feed_in_)_1)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_1)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____feed_in_)_2)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_2)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_0)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_0)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_1)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_1)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_2)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_2)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_0)_:
-1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_0)
+1 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_0)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_1)_:
-1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_1)
+1 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_1)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_2)_:
-1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_2)
+1 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_2)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_30_)_0)_:
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2_demand____input_)_0)
+1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_30_)_0)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_30_)_1)_:
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2_demand____input_)_1)
+1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_30_)_1)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_30_)_2)_:
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2_demand____input_)_2)
+1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_30_)_2)
= 0

c_e_BusBlock_balance((_house_1____H2_demand____input_)_0)_:
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2_demand____input_)_0)
= 0.5

c_e_BusBlock_balance((_house_1____H2_demand____input_)_1)_:
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2_demand____input_)_1)
= 2.5

c_e_BusBlock_balance((_house_1____H2_demand____input_)_2)_:
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2_demand____input_)_2)
= 1.5

c_e_BusBlock_balance((_house_1____HeatCarrier____T_20_)_0)_:
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____PEM_Ely____heat_20_40_)_0)
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____SlackNode____excess_energy_)_0)
+1 flow((_house_1____heating_demand____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_0)
+1 flow((_house_1____SlackNode____missing_energy_)_(_house_1____HeatCarrier____T_20_)_0)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_20_)_1)_:
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____PEM_Ely____heat_20_40_)_1)
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____SlackNode____excess_energy_)_1)
+1 flow((_house_1____heating_demand____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_1)
+1 flow((_house_1____SlackNode____missing_energy_)_(_house_1____HeatCarrier____T_20_)_1)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_20_)_2)_:
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____PEM_Ely____heat_20_40_)_2)
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____SlackNode____excess_energy_)_2)
+1 flow((_house_1____heating_demand____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_2)
+1 flow((_house_1____SlackNode____missing_energy_)_(_house_1____HeatCarrier____T_20_)_2)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_40_)_0)_:
-1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____heating_demand____heat_exchanger_)_0)
-1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____SlackNode____excess_energy_)_0)
+1 flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_0)
+1 flow((_house_1____SlackNode____missing_energy_)_(_house_1____HeatCarrier____T_40_)_0)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_40_)_1)_:
-1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____heating_demand____heat_exchanger_)_1)
-1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____SlackNode____excess_energy_)_1)
+1 flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_1)
+1 flow((_house_1____SlackNode____missing_energy_)_(_house_1____HeatCarrier____T_40_)_1)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_40_)_2)_:
-1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____heating_demand____heat_exchanger_)_2)
-1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____SlackNode____excess_energy_)_2)
+1 flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_2)
+1 flow((_house_1____SlackNode____missing_energy_)_(_house_1____HeatCarrier____T_40_)_2)
= 0

c_e_BusBlock_balance((_house_1____PEM_Ely____heat_)_0)_:
-1 flow((_house_1____PEM_Ely____heat_)_(_house_1____PEM_Ely____heat_20_40_)_0)
+1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____PEM_Ely____heat_)_0)
= 0

c_e_BusBlock_balance((_house_1____PEM_Ely____heat_)_1)_:
-1 flow((_house_1____PEM_Ely____heat_)_(_house_1____PEM_Ely____heat_20_40_)_1)
+1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____PEM_Ely____heat_)_1)
= 0

c_e_BusBlock_balance((_house_1____PEM_Ely____heat_)_2)_:
-1 flow((_house_1____PEM_Ely____heat_)_(_house_1____PEM_Ely____heat_20_40_)_2)
+1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____PEM_Ely____heat_)_2)
= 0

c_e_BusBlock_balance((_house_1____heating_demand____output_)_0)_:
+1 flow((_house_1____heating_demand____heat_exchanger_)_(_house_1____heating_demand____output_)_0)
= 3000

c_e_BusBlock_balance((_house_1____heating_demand____output_)_1)_:
+1 flow((_house_1____heating_demand____heat_exchanger_)_(_house_1____heating_demand____output_)_1)
= 3000

c_e_BusBlock_balance((_house_1____heating_demand____output_)_2)_:
+1 flow((_house_1____heating_demand____heat_exchanger_)_(_house_1____heating_demand____output_)_2)
= 3000

c_e_ConverterBlock_relation((_house_1____PEM_Ely____heat_20_40_)_(_house_1____PEM_Ely____heat_)_(_house_1____HeatCarrier____T_40_)_0)_:
+1 flow((_house_1____PEM_Ely____heat_)_(_house_1____PEM_Ely____heat_20_40_)_0)
-23.22 flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_40_)_0)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____PEM_Ely____heat_20_40_)_0)
-1 flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____heating_demand____heat_exchanger_)_(_house_1____HeatCarrier____T_40_)_(_house_1____heating_demand____output_)_0)_:
+23.22 flow((_house_1____HeatCarrier____T_40_)_(_house_1____heating_demand____heat_exchanger_)_0)
-1 flow((_house_1____heating_demand____heat_exchanger_)_(_house_1____heating_demand____output_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____heating_demand____heat_exchanger_)_(_house_1____HeatCarrier____T_40_)_(_house_1____HeatCarrier____T_20_)_0)_:
+1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____heating_demand____heat_exchanger_)_0)
-1 flow((_house_1____heating_demand____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____PEM_Ely____heat_20_40_)_(_house_1____PEM_Ely____heat_)_(_house_1____HeatCarrier____T_40_)_1)_:
+1 flow((_house_1____PEM_Ely____heat_)_(_house_1____PEM_Ely____heat_20_40_)_1)
-23.22 flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_40_)_1)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____PEM_Ely____heat_20_40_)_1)
-1 flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____heating_demand____heat_exchanger_)_(_house_1____HeatCarrier____T_40_)_(_house_1____heating_demand____output_)_1)_:
+23.22 flow((_house_1____HeatCarrier____T_40_)_(_house_1____heating_demand____heat_exchanger_)_1)
-1 flow((_house_1____heating_demand____heat_exchanger_)_(_house_1____heating_demand____output_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____heating_demand____heat_exchanger_)_(_house_1____HeatCarrier____T_40_)_(_house_1____HeatCarrier____T_20_)_1)_:
+1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____heating_demand____heat_exchanger_)_1)
-1 flow((_house_1____heating_demand____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____PEM_Ely____heat_20_40_)_(_house_1____PEM_Ely____heat_)_(_house_1____HeatCarrier____T_40_)_2)_:
+1 flow((_house_1____PEM_Ely____heat_)_(_house_1____PEM_Ely____heat_20_40_)_2)
-23.22 flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_40_)_2)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____PEM_Ely____heat_20_40_)_2)
-1 flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____heating_demand____heat_exchanger_)_(_house_1____HeatCarrier____T_40_)_(_house_1____heating_demand____output_)_2)_:
+23.22 flow((_house_1____HeatCarrier____T_40_)_(_house_1____heating_demand____heat_exchanger_)_2)
-1 flow((_house_1____heating_demand____heat_exchanger_)_(_house_1____heating_demand____output_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____heating_demand____heat_exchanger_)_(_house_1____HeatCarrier____T_40_)_(_house_1____HeatCarrier____T_20_)_2)_:
+1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____heating_demand____heat_exchanger_)_2)
-1 flow((_house_1____heating_demand____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_2)
= 0

c_e_NonConvexFlowBlock_status_nominal_constraint((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0)_:
+1 NonConvexFlowBlock_status_nominal((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0)
-150000.0 NonConvexFlowBlock_status((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0)
= 0

c_e_NonConvexFlowBlock_status_nominal_constraint((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1)_:
+1 NonConvexFlowBlock_status_nominal((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1)
-150000.0 NonConvexFlowBlock_status((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1)
= 0

c_e_NonConvexFlowBlock_status_nominal_constraint((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2)_:
+1 NonConvexFlowBlock_status_nominal((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2)
-150000.0 NonConvexFlowBlock_status((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2)
= 0

c_u_NonConvexFlowBlock_min((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0)
+0.15 NonConvexFlowBlock_status_nominal((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0)
<= 0

c_u_NonConvexFlowBlock_min((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1)
+0.15 NonConvexFlowBlock_status_nominal((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1)
<= 0

c_u_NonConvexFlowBlock_min((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2)
+0.15 NonConvexFlowBlock_status_nominal((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2)
<= 0

c_u_NonConvexFlowBlock_max((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0)_:
+1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0)
-1 NonConvexFlowBlock_status_nominal((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0)
<= 0

c_u_NonConvexFlowBlock_max((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1)_:
+1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1)
-1 NonConvexFlowBlock_status_nominal((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1)
<= 0

c_u_NonConvexFlowBlock_max((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2)_:
+1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2)
-1 NonConvexFlowBlock_status_nominal((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2)
<= 0

c_e_OffsetConverterBlock_relation((_house_1____PEM_Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____GasCarrier____Hydrogen_30_)_0)_:
+1.8531264891195e-05 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0)
-1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_30_)_0)
+3.7062529782390055e-07 NonConvexFlowBlock_status_nominal((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0)
= 0

c_e_OffsetConverterBlock_relation((_house_1____PEM_Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____heat_)_0)_:
+0.25882352941176473 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0)
-1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____PEM_Ely____heat_)_0)
-0.00882352941176473 NonConvexFlowBlock_status_nominal((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0)
= 0

c_e_OffsetConverterBlock_relation((_house_1____PEM_Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____GasCarrier____Hydrogen_30_)_1)_:
+1.8531264891195e-05 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1)
-1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_30_)_1)
+3.7062529782390055e-07 NonConvexFlowBlock_status_nominal((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1)
= 0

c_e_OffsetConverterBlock_relation((_house_1____PEM_Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____heat_)_1)_:
+0.25882352941176473 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1)
-1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____PEM_Ely____heat_)_1)
-0.00882352941176473 NonConvexFlowBlock_status_nominal((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1)
= 0

c_e_OffsetConverterBlock_relation((_house_1____PEM_Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____GasCarrier____Hydrogen_30_)_2)_:
+1.8531264891195e-05 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2)
-1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_30_)_2)
+3.7062529782390055e-07 NonConvexFlowBlock_status_nominal((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2)
= 0

c_e_OffsetConverterBlock_relation((_house_1____PEM_Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____heat_)_2)_:
+0.25882352941176473 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2)
-1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____PEM_Ely____heat_)_2)
-0.00882352941176473 NonConvexFlowBlock_status_nominal((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2)
= 0

bounds
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0) <= 150000.0
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1) <= 150000.0
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2) <= 150000.0
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_0) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_1) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_2) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2_demand____input_)_0) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2_demand____input_)_1) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2_demand____input_)_2) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____PEM_Ely____heat_20_40_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____PEM_Ely____heat_20_40_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____PEM_Ely____heat_20_40_)_2) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____SlackNode____excess_energy_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____SlackNode____excess_energy_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____SlackNode____excess_energy_)_2) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_40_)_(_house_1____heating_demand____heat_exchanger_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_40_)_(_house_1____heating_demand____heat_exchanger_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_40_)_(_house_1____heating_demand____heat_exchanger_)_2) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_40_)_(_house_1____SlackNode____excess_energy_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_40_)_(_house_1____SlackNode____excess_energy_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_40_)_(_house_1____SlackNode____excess_energy_)_2) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_0) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_1) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_2) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_0) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_1) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_2) <= +inf
   0 <= flow((_house_1____PEM_Ely____heat_)_(_house_1____PEM_Ely____heat_20_40_)_0) <= +inf
   0 <= flow((_house_1____PEM_Ely____heat_)_(_house_1____PEM_Ely____heat_20_40_)_1) <= +inf
   0 <= flow((_house_1____PEM_Ely____heat_)_(_house_1____PEM_Ely____heat_20_40_)_2) <= +inf
   0 <= flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_0) <= +inf
   0 <= flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_1) <= +inf
   0 <= flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_2) <= +inf
   0 <= flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_30_)_0) <= +inf
   0 <= flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_30_)_1) <= +inf
   0 <= flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_30_)_2) <= +inf
   0 <= flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____PEM_Ely____heat_)_0) <= +inf
   0 <= flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____PEM_Ely____heat_)_1) <= +inf
   0 <= flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____PEM_Ely____heat_)_2) <= +inf
   0 <= flow((_house_1____heating_demand____heat_exchanger_)_(_house_1____heating_demand____output_)_0) <= +inf
   0 <= flow((_house_1____heating_demand____heat_exchanger_)_(_house_1____heating_demand____output_)_1) <= +inf
   0 <= flow((_house_1____heating_demand____heat_exchanger_)_(_house_1____heating_demand____output_)_2) <= +inf
   0 <= flow((_house_1____heating_demand____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_0) <= +inf
   0 <= flow((_house_1____heating_demand____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_1) <= +inf
   0 <= flow((_house_1____heating_demand____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_2) <= +inf
   0 <= flow((_house_1____SlackNode____missing_energy_)_(_house_1____HeatCarrier____T_20_)_0) <= +inf
   0 <= flow((_house_1____SlackNode____missing_energy_)_(_house_1____HeatCarrier____T_20_)_1) <= +inf
   0 <= flow((_house_1____SlackNode____missing_energy_)_(_house_1____HeatCarrier____T_20_)_2) <= +inf
   0 <= flow((_house_1____SlackNode____missing_energy_)_(_house_1____HeatCarrier____T_40_)_0) <= +inf
   0 <= flow((_house_1____SlackNode____missing_energy_)_(_house_1____HeatCarrier____T_40_)_1) <= +inf
   0 <= flow((_house_1____SlackNode____missing_energy_)_(_house_1____HeatCarrier____T_40_)_2) <= +inf
   0 <= NonConvexFlowBlock_status_nominal((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0) <= +inf
   0 <= NonConvexFlowBlock_status_nominal((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1) <= +inf
   0 <= NonConvexFlowBlock_status_nominal((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2) <= +inf
   0 <= NonConvexFlowBlock_status((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0) <= 1
   0 <= NonConvexFlowBlock_status((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1) <= 1
   0 <= NonConvexFlowBlock_status((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2) <= 1
binary
  NonConvexFlowBlock_status((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0)
  NonConvexFlowBlock_status((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1)
  NonConvexFlowBlock_status((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2)
end
