\* Source Pyomo model name=Model *\

min 
objective:
+0.0175 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_0)
+0.0175 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_1)
+0.0175 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_2)
+0.0175 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_3)

s.t.

c_u__(_house_1____H2_Storage____level_constraint_)_output_active_constraint_((_house_1____H2_Storage____out_5_)_0)_:
+0.07429344016873067 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_5_)_0)
-0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_1)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_active_constraint_((_house_1____H2_Storage____out_5_)_1)_:
+0.07429344016873067 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_5_)_1)
-0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_2)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_active_constraint_((_house_1____H2_Storage____out_5_)_2)_:
+0.07429344016873067 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_5_)_2)
-0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_3)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_active_constraint_((_house_1____H2_Storage____out_5_)_3)_:
+0.07429344016873067 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_5_)_3)
-0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_4)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_active_constraint_((_house_1____H2_Storage____out_30_)_0)_:
+0.43909235562154497 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_30_)_0)
-0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_1)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_active_constraint_((_house_1____H2_Storage____out_30_)_1)_:
+0.43909235562154497 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_30_)_1)
-0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_2)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_active_constraint_((_house_1____H2_Storage____out_30_)_2)_:
+0.43909235562154497 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_30_)_2)
-0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_3)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_active_constraint_((_house_1____H2_Storage____out_30_)_3)_:
+0.43909235562154497 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_30_)_3)
-0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_4)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_active_constraint_((_house_1____H2_Storage____out_40_)_0)_:
+0.5819242733929523 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_40_)_0)
-0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_1)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_active_constraint_((_house_1____H2_Storage____out_40_)_1)_:
+0.5819242733929523 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_40_)_1)
-0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_2)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_active_constraint_((_house_1____H2_Storage____out_40_)_2)_:
+0.5819242733929523 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_40_)_2)
-0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_3)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_active_constraint_((_house_1____H2_Storage____out_40_)_3)_:
+0.5819242733929523 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_40_)_3)
-0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_4)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_constraint_((_house_1____H2_Storage____out_5_)_0)_:
+0.1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_5_)_0)
-1 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_5_)_0)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_constraint_((_house_1____H2_Storage____out_5_)_1)_:
+0.1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_5_)_1)
-1 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_5_)_1)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_constraint_((_house_1____H2_Storage____out_5_)_2)_:
+0.1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_5_)_2)
-1 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_5_)_2)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_constraint_((_house_1____H2_Storage____out_5_)_3)_:
+0.1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_5_)_3)
-1 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_5_)_3)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_constraint_((_house_1____H2_Storage____out_30_)_0)_:
+0.1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_30_)_0)
-1 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_30_)_0)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_constraint_((_house_1____H2_Storage____out_30_)_1)_:
+0.1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_30_)_1)
-1 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_30_)_1)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_constraint_((_house_1____H2_Storage____out_30_)_2)_:
+0.1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_30_)_2)
-1 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_30_)_2)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_constraint_((_house_1____H2_Storage____out_30_)_3)_:
+0.1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_30_)_3)
-1 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_30_)_3)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_constraint_((_house_1____H2_Storage____out_40_)_0)_:
+0.1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_40_)_0)
-1 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_40_)_0)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_constraint_((_house_1____H2_Storage____out_40_)_1)_:
+0.1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_40_)_1)
-1 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_40_)_1)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_constraint_((_house_1____H2_Storage____out_40_)_2)_:
+0.1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_40_)_2)
-1 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_40_)_2)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_output_constraint_((_house_1____H2_Storage____out_40_)_3)_:
+0.1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_40_)_3)
-1 _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_40_)_3)
<= 0

c_u__(_house_1____H2_Storage____level_constraint_)_input_active_constraint_((_house_1____H2_Storage____in_5_)_0)_:
+0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_0)
-1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_5_)_0)
<= 0.07429344016873067

c_u__(_house_1____H2_Storage____level_constraint_)_input_active_constraint_((_house_1____H2_Storage____in_5_)_1)_:
+0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_1)
-1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_5_)_1)
<= 0.07429344016873067

c_u__(_house_1____H2_Storage____level_constraint_)_input_active_constraint_((_house_1____H2_Storage____in_5_)_2)_:
+0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_2)
-1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_5_)_2)
<= 0.07429344016873067

c_u__(_house_1____H2_Storage____level_constraint_)_input_active_constraint_((_house_1____H2_Storage____in_5_)_3)_:
+0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_3)
-1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_5_)_3)
<= 0.07429344016873067

c_u__(_house_1____H2_Storage____level_constraint_)_input_active_constraint_((_house_1____H2_Storage____in_30_)_0)_:
+0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_0)
-1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_30_)_0)
<= 0.43909235562154497

c_u__(_house_1____H2_Storage____level_constraint_)_input_active_constraint_((_house_1____H2_Storage____in_30_)_1)_:
+0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_1)
-1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_30_)_1)
<= 0.43909235562154497

c_u__(_house_1____H2_Storage____level_constraint_)_input_active_constraint_((_house_1____H2_Storage____in_30_)_2)_:
+0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_2)
-1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_30_)_2)
<= 0.43909235562154497

c_u__(_house_1____H2_Storage____level_constraint_)_input_active_constraint_((_house_1____H2_Storage____in_30_)_3)_:
+0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_3)
-1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_30_)_3)
<= 0.43909235562154497

c_u__(_house_1____H2_Storage____level_constraint_)_input_active_constraint_((_house_1____H2_Storage____in_40_)_0)_:
+0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_0)
-1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_40_)_0)
<= 0.5819242733929523

c_u__(_house_1____H2_Storage____level_constraint_)_input_active_constraint_((_house_1____H2_Storage____in_40_)_1)_:
+0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_1)
-1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_40_)_1)
<= 0.5819242733929523

c_u__(_house_1____H2_Storage____level_constraint_)_input_active_constraint_((_house_1____H2_Storage____in_40_)_2)_:
+0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_2)
-1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_40_)_2)
<= 0.5819242733929523

c_u__(_house_1____H2_Storage____level_constraint_)_input_active_constraint_((_house_1____H2_Storage____in_40_)_3)_:
+0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_3)
-1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_40_)_3)
<= 0.5819242733929523

c_u__(_house_1____H2_Storage____level_constraint_)_input_active_constraint_((_house_1____H2_Storage____in_70_)_0)_:
+0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_0)
-1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_70_)_0)
<= 1.0

c_u__(_house_1____H2_Storage____level_constraint_)_input_active_constraint_((_house_1____H2_Storage____in_70_)_1)_:
+0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_1)
-1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_70_)_1)
<= 1.0

c_u__(_house_1____H2_Storage____level_constraint_)_input_active_constraint_((_house_1____H2_Storage____in_70_)_2)_:
+0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_2)
-1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_70_)_2)
<= 1.0

c_u__(_house_1____H2_Storage____level_constraint_)_input_active_constraint_((_house_1____H2_Storage____in_70_)_3)_:
+0.03665172653544776 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_3)
-1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_70_)_3)
<= 1.0

c_u__(_house_1____H2_Storage____level_constraint_)_input_constraint_((_house_1____H2_Storage____in_5_)_0)_:
+0.1 flow((_house_1____H2_Storage____in_5_)_(_house_1____H2_Storage____multiplexer_)_0)
+1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_5_)_0)
<= 1

c_u__(_house_1____H2_Storage____level_constraint_)_input_constraint_((_house_1____H2_Storage____in_5_)_1)_:
+0.1 flow((_house_1____H2_Storage____in_5_)_(_house_1____H2_Storage____multiplexer_)_1)
+1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_5_)_1)
<= 1

c_u__(_house_1____H2_Storage____level_constraint_)_input_constraint_((_house_1____H2_Storage____in_5_)_2)_:
+0.1 flow((_house_1____H2_Storage____in_5_)_(_house_1____H2_Storage____multiplexer_)_2)
+1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_5_)_2)
<= 1

c_u__(_house_1____H2_Storage____level_constraint_)_input_constraint_((_house_1____H2_Storage____in_5_)_3)_:
+0.1 flow((_house_1____H2_Storage____in_5_)_(_house_1____H2_Storage____multiplexer_)_3)
+1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_5_)_3)
<= 1

c_u__(_house_1____H2_Storage____level_constraint_)_input_constraint_((_house_1____H2_Storage____in_30_)_0)_:
+0.1 flow((_house_1____H2_Storage____in_30_)_(_house_1____H2_Storage____multiplexer_)_0)
+1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_30_)_0)
<= 1

c_u__(_house_1____H2_Storage____level_constraint_)_input_constraint_((_house_1____H2_Storage____in_30_)_1)_:
+0.1 flow((_house_1____H2_Storage____in_30_)_(_house_1____H2_Storage____multiplexer_)_1)
+1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_30_)_1)
<= 1

c_u__(_house_1____H2_Storage____level_constraint_)_input_constraint_((_house_1____H2_Storage____in_30_)_2)_:
+0.1 flow((_house_1____H2_Storage____in_30_)_(_house_1____H2_Storage____multiplexer_)_2)
+1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_30_)_2)
<= 1

c_u__(_house_1____H2_Storage____level_constraint_)_input_constraint_((_house_1____H2_Storage____in_30_)_3)_:
+0.1 flow((_house_1____H2_Storage____in_30_)_(_house_1____H2_Storage____multiplexer_)_3)
+1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_30_)_3)
<= 1

c_u__(_house_1____H2_Storage____level_constraint_)_input_constraint_((_house_1____H2_Storage____in_40_)_0)_:
+0.1 flow((_house_1____H2_Storage____in_40_)_(_house_1____H2_Storage____multiplexer_)_0)
+1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_40_)_0)
<= 1

c_u__(_house_1____H2_Storage____level_constraint_)_input_constraint_((_house_1____H2_Storage____in_40_)_1)_:
+0.1 flow((_house_1____H2_Storage____in_40_)_(_house_1____H2_Storage____multiplexer_)_1)
+1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_40_)_1)
<= 1

c_u__(_house_1____H2_Storage____level_constraint_)_input_constraint_((_house_1____H2_Storage____in_40_)_2)_:
+0.1 flow((_house_1____H2_Storage____in_40_)_(_house_1____H2_Storage____multiplexer_)_2)
+1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_40_)_2)
<= 1

c_u__(_house_1____H2_Storage____level_constraint_)_input_constraint_((_house_1____H2_Storage____in_40_)_3)_:
+0.1 flow((_house_1____H2_Storage____in_40_)_(_house_1____H2_Storage____multiplexer_)_3)
+1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_40_)_3)
<= 1

c_u__(_house_1____H2_Storage____level_constraint_)_input_constraint_((_house_1____H2_Storage____in_70_)_0)_:
+0.1 flow((_house_1____H2_Storage____in_70_)_(_house_1____H2_Storage____multiplexer_)_0)
+1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_70_)_0)
<= 1

c_u__(_house_1____H2_Storage____level_constraint_)_input_constraint_((_house_1____H2_Storage____in_70_)_1)_:
+0.1 flow((_house_1____H2_Storage____in_70_)_(_house_1____H2_Storage____multiplexer_)_1)
+1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_70_)_1)
<= 1

c_u__(_house_1____H2_Storage____level_constraint_)_input_constraint_((_house_1____H2_Storage____in_70_)_2)_:
+0.1 flow((_house_1____H2_Storage____in_70_)_(_house_1____H2_Storage____multiplexer_)_2)
+1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_70_)_2)
<= 1

c_u__(_house_1____H2_Storage____level_constraint_)_input_constraint_((_house_1____H2_Storage____in_70_)_3)_:
+0.1 flow((_house_1____H2_Storage____in_70_)_(_house_1____H2_Storage____multiplexer_)_3)
+1 _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_70_)_3)
<= 1

c_e_BusBlock_balance((_house_1____AFC____heat_)_0)_:
-1 flow((_house_1____AFC____heat_)_(_house_1____AFC____heat_20_40_)_0)
+1 flow((_house_1____AFC____fuel_cell_)_(_house_1____AFC____heat_)_0)
= 0

c_e_BusBlock_balance((_house_1____AFC____heat_)_1)_:
-1 flow((_house_1____AFC____heat_)_(_house_1____AFC____heat_20_40_)_1)
+1 flow((_house_1____AFC____fuel_cell_)_(_house_1____AFC____heat_)_1)
= 0

c_e_BusBlock_balance((_house_1____AFC____heat_)_2)_:
-1 flow((_house_1____AFC____heat_)_(_house_1____AFC____heat_20_40_)_2)
+1 flow((_house_1____AFC____fuel_cell_)_(_house_1____AFC____heat_)_2)
= 0

c_e_BusBlock_balance((_house_1____AFC____heat_)_3)_:
-1 flow((_house_1____AFC____heat_)_(_house_1____AFC____heat_20_40_)_3)
+1 flow((_house_1____AFC____fuel_cell_)_(_house_1____AFC____heat_)_3)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_0)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____electricity_demand____input_)_0)
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____H2Compr____electrical_input_)_0)
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0)
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_0)
+1 flow((_house_1____AFC____fuel_cell_)_(_house_1____ElectricityCarrier____distribution_)_0)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_0)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_1)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____electricity_demand____input_)_1)
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____H2Compr____electrical_input_)_1)
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1)
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_1)
+1 flow((_house_1____AFC____fuel_cell_)_(_house_1____ElectricityCarrier____distribution_)_1)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_1)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_2)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____electricity_demand____input_)_2)
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____H2Compr____electrical_input_)_2)
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2)
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_2)
+1 flow((_house_1____AFC____fuel_cell_)_(_house_1____ElectricityCarrier____distribution_)_2)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_2)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_3)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____electricity_demand____input_)_3)
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____H2Compr____electrical_input_)_3)
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_3)
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_3)
+1 flow((_house_1____AFC____fuel_cell_)_(_house_1____ElectricityCarrier____distribution_)_3)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_3)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____feed_in_)_0)_:
-1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_0)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_0)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____feed_in_)_1)_:
-1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_1)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_1)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____feed_in_)_2)_:
-1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_2)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_2)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____feed_in_)_3)_:
-1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_3)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_3)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_0)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_0)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_0)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_1)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_1)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_1)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_2)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_2)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_2)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_3)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_3)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_3)
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

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_3)_:
-1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_3)
+1 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_3)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_30_)_0)_:
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasCarrier____Hydrogen_5_)_0)
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2Compr____compress_30_40_)_0)
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2_Storage____in_30_)_0)
+1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____GasCarrier____Hydrogen_30_)_0)
+1 flow((_house_1____H2Compr____compress_5_30_)_(_house_1____GasCarrier____Hydrogen_30_)_0)
+1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_30_)_0)
+1 flow((_house_1____H2_Storage____out_30_)_(_house_1____GasCarrier____Hydrogen_30_)_0)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_30_)_1)_:
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasCarrier____Hydrogen_5_)_1)
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2Compr____compress_30_40_)_1)
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2_Storage____in_30_)_1)
+1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____GasCarrier____Hydrogen_30_)_1)
+1 flow((_house_1____H2Compr____compress_5_30_)_(_house_1____GasCarrier____Hydrogen_30_)_1)
+1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_30_)_1)
+1 flow((_house_1____H2_Storage____out_30_)_(_house_1____GasCarrier____Hydrogen_30_)_1)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_30_)_2)_:
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasCarrier____Hydrogen_5_)_2)
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2Compr____compress_30_40_)_2)
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2_Storage____in_30_)_2)
+1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____GasCarrier____Hydrogen_30_)_2)
+1 flow((_house_1____H2Compr____compress_5_30_)_(_house_1____GasCarrier____Hydrogen_30_)_2)
+1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_30_)_2)
+1 flow((_house_1____H2_Storage____out_30_)_(_house_1____GasCarrier____Hydrogen_30_)_2)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_30_)_3)_:
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasCarrier____Hydrogen_5_)_3)
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2Compr____compress_30_40_)_3)
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2_Storage____in_30_)_3)
+1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____GasCarrier____Hydrogen_30_)_3)
+1 flow((_house_1____H2Compr____compress_5_30_)_(_house_1____GasCarrier____Hydrogen_30_)_3)
+1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_30_)_3)
+1 flow((_house_1____H2_Storage____out_30_)_(_house_1____GasCarrier____Hydrogen_30_)_3)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_40_)_0)_:
-1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____GasCarrier____Hydrogen_30_)_0)
-1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_demand____input_)_0)
-1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2Compr____compress_40_70_)_0)
-1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_Storage____in_40_)_0)
+1 flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____GasCarrier____Hydrogen_40_)_0)
+1 flow((_house_1____H2Compr____compress_30_40_)_(_house_1____GasCarrier____Hydrogen_40_)_0)
+1 flow((_house_1____H2_Storage____out_40_)_(_house_1____GasCarrier____Hydrogen_40_)_0)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_40_)_1)_:
-1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____GasCarrier____Hydrogen_30_)_1)
-1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_demand____input_)_1)
-1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2Compr____compress_40_70_)_1)
-1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_Storage____in_40_)_1)
+1 flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____GasCarrier____Hydrogen_40_)_1)
+1 flow((_house_1____H2Compr____compress_30_40_)_(_house_1____GasCarrier____Hydrogen_40_)_1)
+1 flow((_house_1____H2_Storage____out_40_)_(_house_1____GasCarrier____Hydrogen_40_)_1)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_40_)_2)_:
-1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____GasCarrier____Hydrogen_30_)_2)
-1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_demand____input_)_2)
-1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2Compr____compress_40_70_)_2)
-1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_Storage____in_40_)_2)
+1 flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____GasCarrier____Hydrogen_40_)_2)
+1 flow((_house_1____H2Compr____compress_30_40_)_(_house_1____GasCarrier____Hydrogen_40_)_2)
+1 flow((_house_1____H2_Storage____out_40_)_(_house_1____GasCarrier____Hydrogen_40_)_2)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_40_)_3)_:
-1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____GasCarrier____Hydrogen_30_)_3)
-1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_demand____input_)_3)
-1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2Compr____compress_40_70_)_3)
-1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_Storage____in_40_)_3)
+1 flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____GasCarrier____Hydrogen_40_)_3)
+1 flow((_house_1____H2Compr____compress_30_40_)_(_house_1____GasCarrier____Hydrogen_40_)_3)
+1 flow((_house_1____H2_Storage____out_40_)_(_house_1____GasCarrier____Hydrogen_40_)_3)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_5_)_0)_:
-1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____AFC____fuel_cell_)_0)
-1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2Compr____compress_5_30_)_0)
-1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2_Storage____in_5_)_0)
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasCarrier____Hydrogen_5_)_0)
+1 flow((_house_1____H2_Storage____out_5_)_(_house_1____GasCarrier____Hydrogen_5_)_0)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_5_)_1)_:
-1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____AFC____fuel_cell_)_1)
-1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2Compr____compress_5_30_)_1)
-1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2_Storage____in_5_)_1)
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasCarrier____Hydrogen_5_)_1)
+1 flow((_house_1____H2_Storage____out_5_)_(_house_1____GasCarrier____Hydrogen_5_)_1)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_5_)_2)_:
-1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____AFC____fuel_cell_)_2)
-1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2Compr____compress_5_30_)_2)
-1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2_Storage____in_5_)_2)
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasCarrier____Hydrogen_5_)_2)
+1 flow((_house_1____H2_Storage____out_5_)_(_house_1____GasCarrier____Hydrogen_5_)_2)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_5_)_3)_:
-1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____AFC____fuel_cell_)_3)
-1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2Compr____compress_5_30_)_3)
-1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2_Storage____in_5_)_3)
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasCarrier____Hydrogen_5_)_3)
+1 flow((_house_1____H2_Storage____out_5_)_(_house_1____GasCarrier____Hydrogen_5_)_3)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_70_)_0)_:
-1 flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____GasCarrier____Hydrogen_40_)_0)
-1 flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____H2_Storage____in_70_)_0)
+1 flow((_house_1____H2Compr____compress_40_70_)_(_house_1____GasCarrier____Hydrogen_70_)_0)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_70_)_1)_:
-1 flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____GasCarrier____Hydrogen_40_)_1)
-1 flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____H2_Storage____in_70_)_1)
+1 flow((_house_1____H2Compr____compress_40_70_)_(_house_1____GasCarrier____Hydrogen_70_)_1)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_70_)_2)_:
-1 flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____GasCarrier____Hydrogen_40_)_2)
-1 flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____H2_Storage____in_70_)_2)
+1 flow((_house_1____H2Compr____compress_40_70_)_(_house_1____GasCarrier____Hydrogen_70_)_2)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_70_)_3)_:
-1 flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____GasCarrier____Hydrogen_40_)_3)
-1 flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____H2_Storage____in_70_)_3)
+1 flow((_house_1____H2Compr____compress_40_70_)_(_house_1____GasCarrier____Hydrogen_70_)_3)
= 0

c_e_BusBlock_balance((_house_1____H2Compr____electrical_input_)_0)_:
+1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____H2Compr____electrical_input_)_0)
-1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_5_30_)_0)
-1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_30_40_)_0)
-1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_40_70_)_0)
= 0

c_e_BusBlock_balance((_house_1____H2Compr____electrical_input_)_1)_:
+1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____H2Compr____electrical_input_)_1)
-1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_5_30_)_1)
-1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_30_40_)_1)
-1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_40_70_)_1)
= 0

c_e_BusBlock_balance((_house_1____H2Compr____electrical_input_)_2)_:
+1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____H2Compr____electrical_input_)_2)
-1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_5_30_)_2)
-1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_30_40_)_2)
-1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_40_70_)_2)
= 0

c_e_BusBlock_balance((_house_1____H2Compr____electrical_input_)_3)_:
+1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____H2Compr____electrical_input_)_3)
-1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_5_30_)_3)
-1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_30_40_)_3)
-1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_40_70_)_3)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____in_30_)_0)_:
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2_Storage____in_30_)_0)
-1 flow((_house_1____H2_Storage____in_30_)_(_house_1____H2_Storage____multiplexer_)_0)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____in_30_)_1)_:
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2_Storage____in_30_)_1)
-1 flow((_house_1____H2_Storage____in_30_)_(_house_1____H2_Storage____multiplexer_)_1)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____in_30_)_2)_:
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2_Storage____in_30_)_2)
-1 flow((_house_1____H2_Storage____in_30_)_(_house_1____H2_Storage____multiplexer_)_2)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____in_30_)_3)_:
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2_Storage____in_30_)_3)
-1 flow((_house_1____H2_Storage____in_30_)_(_house_1____H2_Storage____multiplexer_)_3)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____in_40_)_0)_:
+1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_Storage____in_40_)_0)
-1 flow((_house_1____H2_Storage____in_40_)_(_house_1____H2_Storage____multiplexer_)_0)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____in_40_)_1)_:
+1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_Storage____in_40_)_1)
-1 flow((_house_1____H2_Storage____in_40_)_(_house_1____H2_Storage____multiplexer_)_1)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____in_40_)_2)_:
+1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_Storage____in_40_)_2)
-1 flow((_house_1____H2_Storage____in_40_)_(_house_1____H2_Storage____multiplexer_)_2)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____in_40_)_3)_:
+1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_Storage____in_40_)_3)
-1 flow((_house_1____H2_Storage____in_40_)_(_house_1____H2_Storage____multiplexer_)_3)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____in_5_)_0)_:
+1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2_Storage____in_5_)_0)
-1 flow((_house_1____H2_Storage____in_5_)_(_house_1____H2_Storage____multiplexer_)_0)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____in_5_)_1)_:
+1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2_Storage____in_5_)_1)
-1 flow((_house_1____H2_Storage____in_5_)_(_house_1____H2_Storage____multiplexer_)_1)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____in_5_)_2)_:
+1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2_Storage____in_5_)_2)
-1 flow((_house_1____H2_Storage____in_5_)_(_house_1____H2_Storage____multiplexer_)_2)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____in_5_)_3)_:
+1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2_Storage____in_5_)_3)
-1 flow((_house_1____H2_Storage____in_5_)_(_house_1____H2_Storage____multiplexer_)_3)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____in_70_)_0)_:
+1 flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____H2_Storage____in_70_)_0)
-1 flow((_house_1____H2_Storage____in_70_)_(_house_1____H2_Storage____multiplexer_)_0)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____in_70_)_1)_:
+1 flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____H2_Storage____in_70_)_1)
-1 flow((_house_1____H2_Storage____in_70_)_(_house_1____H2_Storage____multiplexer_)_1)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____in_70_)_2)_:
+1 flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____H2_Storage____in_70_)_2)
-1 flow((_house_1____H2_Storage____in_70_)_(_house_1____H2_Storage____multiplexer_)_2)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____in_70_)_3)_:
+1 flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____H2_Storage____in_70_)_3)
-1 flow((_house_1____H2_Storage____in_70_)_(_house_1____H2_Storage____multiplexer_)_3)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____multiplexer_)_0)_:
+1 flow((_house_1____H2_Storage____in_5_)_(_house_1____H2_Storage____multiplexer_)_0)
+1 flow((_house_1____H2_Storage____in_30_)_(_house_1____H2_Storage____multiplexer_)_0)
+1 flow((_house_1____H2_Storage____in_40_)_(_house_1____H2_Storage____multiplexer_)_0)
+1 flow((_house_1____H2_Storage____in_70_)_(_house_1____H2_Storage____multiplexer_)_0)
-1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_5_)_0)
-1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_30_)_0)
-1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_40_)_0)
-1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____storage_)_0)
+1 flow((_house_1____H2_Storage____storage_)_(_house_1____H2_Storage____multiplexer_)_0)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____multiplexer_)_1)_:
+1 flow((_house_1____H2_Storage____in_5_)_(_house_1____H2_Storage____multiplexer_)_1)
+1 flow((_house_1____H2_Storage____in_30_)_(_house_1____H2_Storage____multiplexer_)_1)
+1 flow((_house_1____H2_Storage____in_40_)_(_house_1____H2_Storage____multiplexer_)_1)
+1 flow((_house_1____H2_Storage____in_70_)_(_house_1____H2_Storage____multiplexer_)_1)
-1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_5_)_1)
-1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_30_)_1)
-1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_40_)_1)
-1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____storage_)_1)
+1 flow((_house_1____H2_Storage____storage_)_(_house_1____H2_Storage____multiplexer_)_1)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____multiplexer_)_2)_:
+1 flow((_house_1____H2_Storage____in_5_)_(_house_1____H2_Storage____multiplexer_)_2)
+1 flow((_house_1____H2_Storage____in_30_)_(_house_1____H2_Storage____multiplexer_)_2)
+1 flow((_house_1____H2_Storage____in_40_)_(_house_1____H2_Storage____multiplexer_)_2)
+1 flow((_house_1____H2_Storage____in_70_)_(_house_1____H2_Storage____multiplexer_)_2)
-1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_5_)_2)
-1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_30_)_2)
-1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_40_)_2)
-1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____storage_)_2)
+1 flow((_house_1____H2_Storage____storage_)_(_house_1____H2_Storage____multiplexer_)_2)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____multiplexer_)_3)_:
+1 flow((_house_1____H2_Storage____in_5_)_(_house_1____H2_Storage____multiplexer_)_3)
+1 flow((_house_1____H2_Storage____in_30_)_(_house_1____H2_Storage____multiplexer_)_3)
+1 flow((_house_1____H2_Storage____in_40_)_(_house_1____H2_Storage____multiplexer_)_3)
+1 flow((_house_1____H2_Storage____in_70_)_(_house_1____H2_Storage____multiplexer_)_3)
-1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_5_)_3)
-1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_30_)_3)
-1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_40_)_3)
-1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____storage_)_3)
+1 flow((_house_1____H2_Storage____storage_)_(_house_1____H2_Storage____multiplexer_)_3)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____out_30_)_0)_:
-1 flow((_house_1____H2_Storage____out_30_)_(_house_1____GasCarrier____Hydrogen_30_)_0)
+1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_30_)_0)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____out_30_)_1)_:
-1 flow((_house_1____H2_Storage____out_30_)_(_house_1____GasCarrier____Hydrogen_30_)_1)
+1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_30_)_1)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____out_30_)_2)_:
-1 flow((_house_1____H2_Storage____out_30_)_(_house_1____GasCarrier____Hydrogen_30_)_2)
+1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_30_)_2)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____out_30_)_3)_:
-1 flow((_house_1____H2_Storage____out_30_)_(_house_1____GasCarrier____Hydrogen_30_)_3)
+1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_30_)_3)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____out_40_)_0)_:
-1 flow((_house_1____H2_Storage____out_40_)_(_house_1____GasCarrier____Hydrogen_40_)_0)
+1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_40_)_0)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____out_40_)_1)_:
-1 flow((_house_1____H2_Storage____out_40_)_(_house_1____GasCarrier____Hydrogen_40_)_1)
+1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_40_)_1)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____out_40_)_2)_:
-1 flow((_house_1____H2_Storage____out_40_)_(_house_1____GasCarrier____Hydrogen_40_)_2)
+1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_40_)_2)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____out_40_)_3)_:
-1 flow((_house_1____H2_Storage____out_40_)_(_house_1____GasCarrier____Hydrogen_40_)_3)
+1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_40_)_3)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____out_5_)_0)_:
-1 flow((_house_1____H2_Storage____out_5_)_(_house_1____GasCarrier____Hydrogen_5_)_0)
+1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_5_)_0)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____out_5_)_1)_:
-1 flow((_house_1____H2_Storage____out_5_)_(_house_1____GasCarrier____Hydrogen_5_)_1)
+1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_5_)_1)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____out_5_)_2)_:
-1 flow((_house_1____H2_Storage____out_5_)_(_house_1____GasCarrier____Hydrogen_5_)_2)
+1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_5_)_2)
= 0

c_e_BusBlock_balance((_house_1____H2_Storage____out_5_)_3)_:
-1 flow((_house_1____H2_Storage____out_5_)_(_house_1____GasCarrier____Hydrogen_5_)_3)
+1 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_5_)_3)
= 0

c_e_BusBlock_balance((_house_1____H2_demand____input_)_0)_:
+1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_demand____input_)_0)
= 2.80659300184343

c_e_BusBlock_balance((_house_1____H2_demand____input_)_1)_:
+1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_demand____input_)_1)
= 3.197826887667179

c_e_BusBlock_balance((_house_1____H2_demand____input_)_2)_:
+1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_demand____input_)_2)
= 3.1864934102864937

c_e_BusBlock_balance((_house_1____H2_demand____input_)_3)_:
+1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_demand____input_)_3)
= 3.200124146498274

c_e_BusBlock_balance((_house_1____HeatCarrier____T_20_)_0)_:
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____AFC____heat_20_40_)_0)
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____PEM_Ely____heat_20_40_)_0)
+1 flow((_house_1____Heat_Sink____sink_40_)_(_house_1____HeatCarrier____T_20_)_0)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_20_)_1)_:
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____AFC____heat_20_40_)_1)
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____PEM_Ely____heat_20_40_)_1)
+1 flow((_house_1____Heat_Sink____sink_40_)_(_house_1____HeatCarrier____T_20_)_1)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_20_)_2)_:
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____AFC____heat_20_40_)_2)
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____PEM_Ely____heat_20_40_)_2)
+1 flow((_house_1____Heat_Sink____sink_40_)_(_house_1____HeatCarrier____T_20_)_2)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_20_)_3)_:
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____AFC____heat_20_40_)_3)
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____PEM_Ely____heat_20_40_)_3)
+1 flow((_house_1____Heat_Sink____sink_40_)_(_house_1____HeatCarrier____T_20_)_3)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_40_)_0)_:
-1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____Heat_Sink____sink_40_)_0)
+1 flow((_house_1____AFC____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_0)
+1 flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_0)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_40_)_1)_:
-1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____Heat_Sink____sink_40_)_1)
+1 flow((_house_1____AFC____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_1)
+1 flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_1)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_40_)_2)_:
-1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____Heat_Sink____sink_40_)_2)
+1 flow((_house_1____AFC____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_2)
+1 flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_2)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_40_)_3)_:
-1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____Heat_Sink____sink_40_)_3)
+1 flow((_house_1____AFC____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_3)
+1 flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_3)
= 0

c_e_BusBlock_balance((_house_1____Heat_Sink____output_)_0)_:
-1 flow((_house_1____Heat_Sink____output_)_(_house_1____Heat_Sink____sink_)_0)
+1 flow((_house_1____Heat_Sink____sink_40_)_(_house_1____Heat_Sink____output_)_0)
= 0

c_e_BusBlock_balance((_house_1____Heat_Sink____output_)_1)_:
-1 flow((_house_1____Heat_Sink____output_)_(_house_1____Heat_Sink____sink_)_1)
+1 flow((_house_1____Heat_Sink____sink_40_)_(_house_1____Heat_Sink____output_)_1)
= 0

c_e_BusBlock_balance((_house_1____Heat_Sink____output_)_2)_:
-1 flow((_house_1____Heat_Sink____output_)_(_house_1____Heat_Sink____sink_)_2)
+1 flow((_house_1____Heat_Sink____sink_40_)_(_house_1____Heat_Sink____output_)_2)
= 0

c_e_BusBlock_balance((_house_1____Heat_Sink____output_)_3)_:
-1 flow((_house_1____Heat_Sink____output_)_(_house_1____Heat_Sink____sink_)_3)
+1 flow((_house_1____Heat_Sink____sink_40_)_(_house_1____Heat_Sink____output_)_3)
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

c_e_BusBlock_balance((_house_1____PEM_Ely____heat_)_3)_:
-1 flow((_house_1____PEM_Ely____heat_)_(_house_1____PEM_Ely____heat_20_40_)_3)
+1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____PEM_Ely____heat_)_3)
= 0

c_e_BusBlock_balance((_house_1____electricity_demand____input_)_0)_:
+1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____electricity_demand____input_)_0)
= 28.0659300184343

c_e_BusBlock_balance((_house_1____electricity_demand____input_)_1)_:
+1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____electricity_demand____input_)_1)
= 31.97826887667179

c_e_BusBlock_balance((_house_1____electricity_demand____input_)_2)_:
+1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____electricity_demand____input_)_2)
= 31.864934102864936

c_e_BusBlock_balance((_house_1____electricity_demand____input_)_3)_:
+1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____electricity_demand____input_)_3)
= 32.00124146498274

c_e_BusBlock_balance((_house_1____pv0____connection_)_0)_:
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_0)
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_0)
+1 flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_0)
= 0

c_e_BusBlock_balance((_house_1____pv0____connection_)_1)_:
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_1)
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_1)
+1 flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_1)
= 0

c_e_BusBlock_balance((_house_1____pv0____connection_)_2)_:
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_2)
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_2)
+1 flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_2)
= 0

c_e_BusBlock_balance((_house_1____pv0____connection_)_3)_:
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_3)
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_3)
+1 flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____AFC____heat_20_40_)_(_house_1____AFC____heat_)_(_house_1____HeatCarrier____T_40_)_0)_:
+1 flow((_house_1____AFC____heat_)_(_house_1____AFC____heat_20_40_)_0)
-23.22 flow((_house_1____AFC____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____AFC____heat_20_40_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_40_)_0)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____AFC____heat_20_40_)_0)
-1 flow((_house_1____AFC____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_5_30_)_(_house_1____GasCarrier____Hydrogen_5_)_(_house_1____GasCarrier____Hydrogen_30_)_0)_:
+1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2Compr____compress_5_30_)_0)
-1 flow((_house_1____H2Compr____compress_5_30_)_(_house_1____GasCarrier____Hydrogen_30_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_5_30_)_(_house_1____H2Compr____electrical_input_)_(_house_1____GasCarrier____Hydrogen_30_)_0)_:
+1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_5_30_)_0)
-707.9352285650231 flow((_house_1____H2Compr____compress_5_30_)_(_house_1____GasCarrier____Hydrogen_30_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_30_40_)_(_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasCarrier____Hydrogen_40_)_0)_:
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2Compr____compress_30_40_)_0)
-1 flow((_house_1____H2Compr____compress_30_40_)_(_house_1____GasCarrier____Hydrogen_40_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_30_40_)_(_house_1____H2Compr____electrical_input_)_(_house_1____GasCarrier____Hydrogen_40_)_0)_:
+1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_30_40_)_0)
-113.66496296679492 flow((_house_1____H2Compr____compress_30_40_)_(_house_1____GasCarrier____Hydrogen_40_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____AFC____fuel_cell_)_(_house_1____GasCarrier____Hydrogen_5_)_(_house_1____ElectricityCarrier____distribution_)_0)_:
+12332.1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____AFC____fuel_cell_)_0)
-1 flow((_house_1____AFC____fuel_cell_)_(_house_1____ElectricityCarrier____distribution_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____AFC____fuel_cell_)_(_house_1____GasCarrier____Hydrogen_5_)_(_house_1____AFC____heat_)_0)_:
+14998.5 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____AFC____fuel_cell_)_0)
-1 flow((_house_1____AFC____fuel_cell_)_(_house_1____AFC____heat_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____PEM_Ely____heat_20_40_)_(_house_1____PEM_Ely____heat_)_(_house_1____HeatCarrier____T_40_)_0)_:
+1 flow((_house_1____PEM_Ely____heat_)_(_house_1____PEM_Ely____heat_20_40_)_0)
-23.22 flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_40_)_0)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____PEM_Ely____heat_20_40_)_0)
-1 flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_40_70_)_(_house_1____GasCarrier____Hydrogen_40_)_(_house_1____GasCarrier____Hydrogen_70_)_0)_:
+1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2Compr____compress_40_70_)_0)
-1 flow((_house_1____H2Compr____compress_40_70_)_(_house_1____GasCarrier____Hydrogen_70_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_40_70_)_(_house_1____H2Compr____electrical_input_)_(_house_1____GasCarrier____Hydrogen_70_)_0)_:
+1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_40_70_)_0)
-221.10765286556114 flow((_house_1____H2Compr____compress_40_70_)_(_house_1____GasCarrier____Hydrogen_70_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Heat_Sink____sink_40_)_(_house_1____HeatCarrier____T_40_)_(_house_1____HeatCarrier____T_20_)_0)_:
+1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____Heat_Sink____sink_40_)_0)
-1 flow((_house_1____Heat_Sink____sink_40_)_(_house_1____HeatCarrier____T_20_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Heat_Sink____sink_40_)_(_house_1____HeatCarrier____T_40_)_(_house_1____Heat_Sink____output_)_0)_:
+23.22 flow((_house_1____HeatCarrier____T_40_)_(_house_1____Heat_Sink____sink_40_)_0)
-1 flow((_house_1____Heat_Sink____sink_40_)_(_house_1____Heat_Sink____output_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____PEM_Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____GasCarrier____Hydrogen_30_)_0)_:
+1.89018901890189e-05 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0)
-1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_30_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____PEM_Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____heat_)_0)_:
+0.25 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0)
-1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____PEM_Ely____heat_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____AFC____heat_20_40_)_(_house_1____AFC____heat_)_(_house_1____HeatCarrier____T_40_)_1)_:
+1 flow((_house_1____AFC____heat_)_(_house_1____AFC____heat_20_40_)_1)
-23.22 flow((_house_1____AFC____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____AFC____heat_20_40_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_40_)_1)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____AFC____heat_20_40_)_1)
-1 flow((_house_1____AFC____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_5_30_)_(_house_1____GasCarrier____Hydrogen_5_)_(_house_1____GasCarrier____Hydrogen_30_)_1)_:
+1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2Compr____compress_5_30_)_1)
-1 flow((_house_1____H2Compr____compress_5_30_)_(_house_1____GasCarrier____Hydrogen_30_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_5_30_)_(_house_1____H2Compr____electrical_input_)_(_house_1____GasCarrier____Hydrogen_30_)_1)_:
+1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_5_30_)_1)
-707.9352285650231 flow((_house_1____H2Compr____compress_5_30_)_(_house_1____GasCarrier____Hydrogen_30_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_30_40_)_(_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasCarrier____Hydrogen_40_)_1)_:
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2Compr____compress_30_40_)_1)
-1 flow((_house_1____H2Compr____compress_30_40_)_(_house_1____GasCarrier____Hydrogen_40_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_30_40_)_(_house_1____H2Compr____electrical_input_)_(_house_1____GasCarrier____Hydrogen_40_)_1)_:
+1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_30_40_)_1)
-113.66496296679492 flow((_house_1____H2Compr____compress_30_40_)_(_house_1____GasCarrier____Hydrogen_40_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____AFC____fuel_cell_)_(_house_1____GasCarrier____Hydrogen_5_)_(_house_1____ElectricityCarrier____distribution_)_1)_:
+12332.1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____AFC____fuel_cell_)_1)
-1 flow((_house_1____AFC____fuel_cell_)_(_house_1____ElectricityCarrier____distribution_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____AFC____fuel_cell_)_(_house_1____GasCarrier____Hydrogen_5_)_(_house_1____AFC____heat_)_1)_:
+14998.5 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____AFC____fuel_cell_)_1)
-1 flow((_house_1____AFC____fuel_cell_)_(_house_1____AFC____heat_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____PEM_Ely____heat_20_40_)_(_house_1____PEM_Ely____heat_)_(_house_1____HeatCarrier____T_40_)_1)_:
+1 flow((_house_1____PEM_Ely____heat_)_(_house_1____PEM_Ely____heat_20_40_)_1)
-23.22 flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_40_)_1)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____PEM_Ely____heat_20_40_)_1)
-1 flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_40_70_)_(_house_1____GasCarrier____Hydrogen_40_)_(_house_1____GasCarrier____Hydrogen_70_)_1)_:
+1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2Compr____compress_40_70_)_1)
-1 flow((_house_1____H2Compr____compress_40_70_)_(_house_1____GasCarrier____Hydrogen_70_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_40_70_)_(_house_1____H2Compr____electrical_input_)_(_house_1____GasCarrier____Hydrogen_70_)_1)_:
+1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_40_70_)_1)
-221.10765286556114 flow((_house_1____H2Compr____compress_40_70_)_(_house_1____GasCarrier____Hydrogen_70_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____Heat_Sink____sink_40_)_(_house_1____HeatCarrier____T_40_)_(_house_1____HeatCarrier____T_20_)_1)_:
+1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____Heat_Sink____sink_40_)_1)
-1 flow((_house_1____Heat_Sink____sink_40_)_(_house_1____HeatCarrier____T_20_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____Heat_Sink____sink_40_)_(_house_1____HeatCarrier____T_40_)_(_house_1____Heat_Sink____output_)_1)_:
+23.22 flow((_house_1____HeatCarrier____T_40_)_(_house_1____Heat_Sink____sink_40_)_1)
-1 flow((_house_1____Heat_Sink____sink_40_)_(_house_1____Heat_Sink____output_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____PEM_Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____GasCarrier____Hydrogen_30_)_1)_:
+1.89018901890189e-05 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1)
-1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_30_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____PEM_Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____heat_)_1)_:
+0.25 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1)
-1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____PEM_Ely____heat_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____AFC____heat_20_40_)_(_house_1____AFC____heat_)_(_house_1____HeatCarrier____T_40_)_2)_:
+1 flow((_house_1____AFC____heat_)_(_house_1____AFC____heat_20_40_)_2)
-23.22 flow((_house_1____AFC____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____AFC____heat_20_40_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_40_)_2)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____AFC____heat_20_40_)_2)
-1 flow((_house_1____AFC____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_5_30_)_(_house_1____GasCarrier____Hydrogen_5_)_(_house_1____GasCarrier____Hydrogen_30_)_2)_:
+1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2Compr____compress_5_30_)_2)
-1 flow((_house_1____H2Compr____compress_5_30_)_(_house_1____GasCarrier____Hydrogen_30_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_5_30_)_(_house_1____H2Compr____electrical_input_)_(_house_1____GasCarrier____Hydrogen_30_)_2)_:
+1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_5_30_)_2)
-707.9352285650231 flow((_house_1____H2Compr____compress_5_30_)_(_house_1____GasCarrier____Hydrogen_30_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_30_40_)_(_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasCarrier____Hydrogen_40_)_2)_:
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2Compr____compress_30_40_)_2)
-1 flow((_house_1____H2Compr____compress_30_40_)_(_house_1____GasCarrier____Hydrogen_40_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_30_40_)_(_house_1____H2Compr____electrical_input_)_(_house_1____GasCarrier____Hydrogen_40_)_2)_:
+1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_30_40_)_2)
-113.66496296679492 flow((_house_1____H2Compr____compress_30_40_)_(_house_1____GasCarrier____Hydrogen_40_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____AFC____fuel_cell_)_(_house_1____GasCarrier____Hydrogen_5_)_(_house_1____ElectricityCarrier____distribution_)_2)_:
+12332.1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____AFC____fuel_cell_)_2)
-1 flow((_house_1____AFC____fuel_cell_)_(_house_1____ElectricityCarrier____distribution_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____AFC____fuel_cell_)_(_house_1____GasCarrier____Hydrogen_5_)_(_house_1____AFC____heat_)_2)_:
+14998.5 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____AFC____fuel_cell_)_2)
-1 flow((_house_1____AFC____fuel_cell_)_(_house_1____AFC____heat_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____PEM_Ely____heat_20_40_)_(_house_1____PEM_Ely____heat_)_(_house_1____HeatCarrier____T_40_)_2)_:
+1 flow((_house_1____PEM_Ely____heat_)_(_house_1____PEM_Ely____heat_20_40_)_2)
-23.22 flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_40_)_2)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____PEM_Ely____heat_20_40_)_2)
-1 flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_40_70_)_(_house_1____GasCarrier____Hydrogen_40_)_(_house_1____GasCarrier____Hydrogen_70_)_2)_:
+1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2Compr____compress_40_70_)_2)
-1 flow((_house_1____H2Compr____compress_40_70_)_(_house_1____GasCarrier____Hydrogen_70_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_40_70_)_(_house_1____H2Compr____electrical_input_)_(_house_1____GasCarrier____Hydrogen_70_)_2)_:
+1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_40_70_)_2)
-221.10765286556114 flow((_house_1____H2Compr____compress_40_70_)_(_house_1____GasCarrier____Hydrogen_70_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____Heat_Sink____sink_40_)_(_house_1____HeatCarrier____T_40_)_(_house_1____HeatCarrier____T_20_)_2)_:
+1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____Heat_Sink____sink_40_)_2)
-1 flow((_house_1____Heat_Sink____sink_40_)_(_house_1____HeatCarrier____T_20_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____Heat_Sink____sink_40_)_(_house_1____HeatCarrier____T_40_)_(_house_1____Heat_Sink____output_)_2)_:
+23.22 flow((_house_1____HeatCarrier____T_40_)_(_house_1____Heat_Sink____sink_40_)_2)
-1 flow((_house_1____Heat_Sink____sink_40_)_(_house_1____Heat_Sink____output_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____PEM_Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____GasCarrier____Hydrogen_30_)_2)_:
+1.89018901890189e-05 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2)
-1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_30_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____PEM_Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____heat_)_2)_:
+0.25 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2)
-1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____PEM_Ely____heat_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____AFC____heat_20_40_)_(_house_1____AFC____heat_)_(_house_1____HeatCarrier____T_40_)_3)_:
+1 flow((_house_1____AFC____heat_)_(_house_1____AFC____heat_20_40_)_3)
-23.22 flow((_house_1____AFC____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____AFC____heat_20_40_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_40_)_3)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____AFC____heat_20_40_)_3)
-1 flow((_house_1____AFC____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_5_30_)_(_house_1____GasCarrier____Hydrogen_5_)_(_house_1____GasCarrier____Hydrogen_30_)_3)_:
+1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2Compr____compress_5_30_)_3)
-1 flow((_house_1____H2Compr____compress_5_30_)_(_house_1____GasCarrier____Hydrogen_30_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_5_30_)_(_house_1____H2Compr____electrical_input_)_(_house_1____GasCarrier____Hydrogen_30_)_3)_:
+1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_5_30_)_3)
-707.9352285650231 flow((_house_1____H2Compr____compress_5_30_)_(_house_1____GasCarrier____Hydrogen_30_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_30_40_)_(_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasCarrier____Hydrogen_40_)_3)_:
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2Compr____compress_30_40_)_3)
-1 flow((_house_1____H2Compr____compress_30_40_)_(_house_1____GasCarrier____Hydrogen_40_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_30_40_)_(_house_1____H2Compr____electrical_input_)_(_house_1____GasCarrier____Hydrogen_40_)_3)_:
+1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_30_40_)_3)
-113.66496296679492 flow((_house_1____H2Compr____compress_30_40_)_(_house_1____GasCarrier____Hydrogen_40_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____AFC____fuel_cell_)_(_house_1____GasCarrier____Hydrogen_5_)_(_house_1____ElectricityCarrier____distribution_)_3)_:
+12332.1 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____AFC____fuel_cell_)_3)
-1 flow((_house_1____AFC____fuel_cell_)_(_house_1____ElectricityCarrier____distribution_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____AFC____fuel_cell_)_(_house_1____GasCarrier____Hydrogen_5_)_(_house_1____AFC____heat_)_3)_:
+14998.5 flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____AFC____fuel_cell_)_3)
-1 flow((_house_1____AFC____fuel_cell_)_(_house_1____AFC____heat_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____PEM_Ely____heat_20_40_)_(_house_1____PEM_Ely____heat_)_(_house_1____HeatCarrier____T_40_)_3)_:
+1 flow((_house_1____PEM_Ely____heat_)_(_house_1____PEM_Ely____heat_20_40_)_3)
-23.22 flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_40_)_3)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____PEM_Ely____heat_20_40_)_3)
-1 flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_40_70_)_(_house_1____GasCarrier____Hydrogen_40_)_(_house_1____GasCarrier____Hydrogen_70_)_3)_:
+1 flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2Compr____compress_40_70_)_3)
-1 flow((_house_1____H2Compr____compress_40_70_)_(_house_1____GasCarrier____Hydrogen_70_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____H2Compr____compress_40_70_)_(_house_1____H2Compr____electrical_input_)_(_house_1____GasCarrier____Hydrogen_70_)_3)_:
+1 flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_40_70_)_3)
-221.10765286556114 flow((_house_1____H2Compr____compress_40_70_)_(_house_1____GasCarrier____Hydrogen_70_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____Heat_Sink____sink_40_)_(_house_1____HeatCarrier____T_40_)_(_house_1____HeatCarrier____T_20_)_3)_:
+1 flow((_house_1____HeatCarrier____T_40_)_(_house_1____Heat_Sink____sink_40_)_3)
-1 flow((_house_1____Heat_Sink____sink_40_)_(_house_1____HeatCarrier____T_20_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____Heat_Sink____sink_40_)_(_house_1____HeatCarrier____T_40_)_(_house_1____Heat_Sink____output_)_3)_:
+23.22 flow((_house_1____HeatCarrier____T_40_)_(_house_1____Heat_Sink____sink_40_)_3)
-1 flow((_house_1____Heat_Sink____sink_40_)_(_house_1____Heat_Sink____output_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____PEM_Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____GasCarrier____Hydrogen_30_)_3)_:
+1.89018901890189e-05 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_3)
-1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_30_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____PEM_Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____heat_)_3)_:
+0.25 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_3)
-1 flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____PEM_Ely____heat_)_3)
= 0

c_e_GenericStorageBlock_losses((_house_1____H2_Storage____storage_)_0)_:
-1 GenericStorageBlock_storage_losses((_house_1____H2_Storage____storage_)_0)
= 0

c_e_GenericStorageBlock_losses((_house_1____H2_Storage____storage_)_1)_:
-1 GenericStorageBlock_storage_losses((_house_1____H2_Storage____storage_)_1)
= 0

c_e_GenericStorageBlock_losses((_house_1____H2_Storage____storage_)_2)_:
-1 GenericStorageBlock_storage_losses((_house_1____H2_Storage____storage_)_2)
= 0

c_e_GenericStorageBlock_losses((_house_1____H2_Storage____storage_)_3)_:
-1 GenericStorageBlock_storage_losses((_house_1____H2_Storage____storage_)_3)
= 0

c_e_GenericStorageBlock_balance((_house_1____H2_Storage____storage_)_0)_:
+0.25 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____storage_)_0)
-0.25 flow((_house_1____H2_Storage____storage_)_(_house_1____H2_Storage____multiplexer_)_0)
+1 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_0)
-1 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_1)
-1 GenericStorageBlock_storage_losses((_house_1____H2_Storage____storage_)_0)
= 0

c_e_GenericStorageBlock_balance((_house_1____H2_Storage____storage_)_1)_:
+0.25 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____storage_)_1)
-0.25 flow((_house_1____H2_Storage____storage_)_(_house_1____H2_Storage____multiplexer_)_1)
+1 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_1)
-1 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_2)
-1 GenericStorageBlock_storage_losses((_house_1____H2_Storage____storage_)_1)
= 0

c_e_GenericStorageBlock_balance((_house_1____H2_Storage____storage_)_2)_:
+0.25 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____storage_)_2)
-0.25 flow((_house_1____H2_Storage____storage_)_(_house_1____H2_Storage____multiplexer_)_2)
+1 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_2)
-1 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_3)
-1 GenericStorageBlock_storage_losses((_house_1____H2_Storage____storage_)_2)
= 0

c_e_GenericStorageBlock_balance((_house_1____H2_Storage____storage_)_3)_:
+0.25 flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____storage_)_3)
-0.25 flow((_house_1____H2_Storage____storage_)_(_house_1____H2_Storage____multiplexer_)_3)
+1 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_3)
-1 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_4)
-1 GenericStorageBlock_storage_losses((_house_1____H2_Storage____storage_)_3)
= 0

c_e_GenericStorageBlock_balanced_cstr((_house_1____H2_Storage____storage_))_:
-1 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_0)
+1 GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_4)
= 0

bounds
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____electricity_demand____input_)_0) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____electricity_demand____input_)_1) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____electricity_demand____input_)_2) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____electricity_demand____input_)_3) <= +inf
   0.0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____H2Compr____electrical_input_)_0) <= 50000.0
   0.0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____H2Compr____electrical_input_)_1) <= 50000.0
   0.0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____H2Compr____electrical_input_)_2) <= 50000.0
   0.0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____H2Compr____electrical_input_)_3) <= 50000.0
   0.0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_0) <= 1500000.0
   0.0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_1) <= 1500000.0
   0.0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_2) <= 1500000.0
   0.0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____PEM_Ely____electrolyser_)_3) <= 1500000.0
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_0) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_1) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_2) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_3) <= +inf
   0.0 <= flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____AFC____fuel_cell_)_0) <= 0.8108919000008109
   0.0 <= flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____AFC____fuel_cell_)_1) <= 0.8108919000008109
   0.0 <= flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____AFC____fuel_cell_)_2) <= 0.8108919000008109
   0.0 <= flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____AFC____fuel_cell_)_3) <= 0.8108919000008109
   0 <= flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2Compr____compress_5_30_)_0) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2Compr____compress_5_30_)_1) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2Compr____compress_5_30_)_2) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2Compr____compress_5_30_)_3) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2_Storage____in_5_)_0) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2_Storage____in_5_)_1) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2_Storage____in_5_)_2) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_5_)_(_house_1____H2_Storage____in_5_)_3) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasCarrier____Hydrogen_5_)_0) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasCarrier____Hydrogen_5_)_1) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasCarrier____Hydrogen_5_)_2) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasCarrier____Hydrogen_5_)_3) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2Compr____compress_30_40_)_0) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2Compr____compress_30_40_)_1) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2Compr____compress_30_40_)_2) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2Compr____compress_30_40_)_3) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2_Storage____in_30_)_0) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2_Storage____in_30_)_1) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2_Storage____in_30_)_2) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____H2_Storage____in_30_)_3) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____GasCarrier____Hydrogen_30_)_0) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____GasCarrier____Hydrogen_30_)_1) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____GasCarrier____Hydrogen_30_)_2) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____GasCarrier____Hydrogen_30_)_3) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_demand____input_)_0) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_demand____input_)_1) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_demand____input_)_2) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_demand____input_)_3) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2Compr____compress_40_70_)_0) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2Compr____compress_40_70_)_1) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2Compr____compress_40_70_)_2) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2Compr____compress_40_70_)_3) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_Storage____in_40_)_0) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_Storage____in_40_)_1) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_Storage____in_40_)_2) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_40_)_(_house_1____H2_Storage____in_40_)_3) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____GasCarrier____Hydrogen_40_)_0) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____GasCarrier____Hydrogen_40_)_1) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____GasCarrier____Hydrogen_40_)_2) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____GasCarrier____Hydrogen_40_)_3) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____H2_Storage____in_70_)_0) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____H2_Storage____in_70_)_1) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____H2_Storage____in_70_)_2) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_70_)_(_house_1____H2_Storage____in_70_)_3) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____AFC____heat_20_40_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____AFC____heat_20_40_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____AFC____heat_20_40_)_2) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____AFC____heat_20_40_)_3) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____PEM_Ely____heat_20_40_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____PEM_Ely____heat_20_40_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____PEM_Ely____heat_20_40_)_2) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____PEM_Ely____heat_20_40_)_3) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_40_)_(_house_1____Heat_Sink____sink_40_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_40_)_(_house_1____Heat_Sink____sink_40_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_40_)_(_house_1____Heat_Sink____sink_40_)_2) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_40_)_(_house_1____Heat_Sink____sink_40_)_3) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_0) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_1) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_2) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_3) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_0) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_1) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_2) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_3) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_0) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_1) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_2) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_3) <= +inf
   0 <= flow((_house_1____AFC____heat_)_(_house_1____AFC____heat_20_40_)_0) <= +inf
   0 <= flow((_house_1____AFC____heat_)_(_house_1____AFC____heat_20_40_)_1) <= +inf
   0 <= flow((_house_1____AFC____heat_)_(_house_1____AFC____heat_20_40_)_2) <= +inf
   0 <= flow((_house_1____AFC____heat_)_(_house_1____AFC____heat_20_40_)_3) <= +inf
   0 <= flow((_house_1____AFC____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_0) <= +inf
   0 <= flow((_house_1____AFC____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_1) <= +inf
   0 <= flow((_house_1____AFC____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_2) <= +inf
   0 <= flow((_house_1____AFC____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_3) <= +inf
   0 <= flow((_house_1____AFC____fuel_cell_)_(_house_1____ElectricityCarrier____distribution_)_0) <= +inf
   0 <= flow((_house_1____AFC____fuel_cell_)_(_house_1____ElectricityCarrier____distribution_)_1) <= +inf
   0 <= flow((_house_1____AFC____fuel_cell_)_(_house_1____ElectricityCarrier____distribution_)_2) <= +inf
   0 <= flow((_house_1____AFC____fuel_cell_)_(_house_1____ElectricityCarrier____distribution_)_3) <= +inf
   0 <= flow((_house_1____AFC____fuel_cell_)_(_house_1____AFC____heat_)_0) <= +inf
   0 <= flow((_house_1____AFC____fuel_cell_)_(_house_1____AFC____heat_)_1) <= +inf
   0 <= flow((_house_1____AFC____fuel_cell_)_(_house_1____AFC____heat_)_2) <= +inf
   0 <= flow((_house_1____AFC____fuel_cell_)_(_house_1____AFC____heat_)_3) <= +inf
   0 <= flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_5_30_)_0) <= +inf
   0 <= flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_5_30_)_1) <= +inf
   0 <= flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_5_30_)_2) <= +inf
   0 <= flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_5_30_)_3) <= +inf
   0 <= flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_30_40_)_0) <= +inf
   0 <= flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_30_40_)_1) <= +inf
   0 <= flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_30_40_)_2) <= +inf
   0 <= flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_30_40_)_3) <= +inf
   0 <= flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_40_70_)_0) <= +inf
   0 <= flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_40_70_)_1) <= +inf
   0 <= flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_40_70_)_2) <= +inf
   0 <= flow((_house_1____H2Compr____electrical_input_)_(_house_1____H2Compr____compress_40_70_)_3) <= +inf
   0 <= flow((_house_1____H2Compr____compress_5_30_)_(_house_1____GasCarrier____Hydrogen_30_)_0) <= +inf
   0 <= flow((_house_1____H2Compr____compress_5_30_)_(_house_1____GasCarrier____Hydrogen_30_)_1) <= +inf
   0 <= flow((_house_1____H2Compr____compress_5_30_)_(_house_1____GasCarrier____Hydrogen_30_)_2) <= +inf
   0 <= flow((_house_1____H2Compr____compress_5_30_)_(_house_1____GasCarrier____Hydrogen_30_)_3) <= +inf
   0 <= flow((_house_1____H2Compr____compress_30_40_)_(_house_1____GasCarrier____Hydrogen_40_)_0) <= +inf
   0 <= flow((_house_1____H2Compr____compress_30_40_)_(_house_1____GasCarrier____Hydrogen_40_)_1) <= +inf
   0 <= flow((_house_1____H2Compr____compress_30_40_)_(_house_1____GasCarrier____Hydrogen_40_)_2) <= +inf
   0 <= flow((_house_1____H2Compr____compress_30_40_)_(_house_1____GasCarrier____Hydrogen_40_)_3) <= +inf
   0 <= flow((_house_1____H2Compr____compress_40_70_)_(_house_1____GasCarrier____Hydrogen_70_)_0) <= +inf
   0 <= flow((_house_1____H2Compr____compress_40_70_)_(_house_1____GasCarrier____Hydrogen_70_)_1) <= +inf
   0 <= flow((_house_1____H2Compr____compress_40_70_)_(_house_1____GasCarrier____Hydrogen_70_)_2) <= +inf
   0 <= flow((_house_1____H2Compr____compress_40_70_)_(_house_1____GasCarrier____Hydrogen_70_)_3) <= +inf
   0 <= flow((_house_1____PEM_Ely____heat_)_(_house_1____PEM_Ely____heat_20_40_)_0) <= +inf
   0 <= flow((_house_1____PEM_Ely____heat_)_(_house_1____PEM_Ely____heat_20_40_)_1) <= +inf
   0 <= flow((_house_1____PEM_Ely____heat_)_(_house_1____PEM_Ely____heat_20_40_)_2) <= +inf
   0 <= flow((_house_1____PEM_Ely____heat_)_(_house_1____PEM_Ely____heat_20_40_)_3) <= +inf
   0 <= flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_0) <= +inf
   0 <= flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_1) <= +inf
   0 <= flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_2) <= +inf
   0 <= flow((_house_1____PEM_Ely____heat_20_40_)_(_house_1____HeatCarrier____T_40_)_3) <= +inf
   0 <= flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_30_)_0) <= +inf
   0 <= flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_30_)_1) <= +inf
   0 <= flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_30_)_2) <= +inf
   0 <= flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_30_)_3) <= +inf
   0 <= flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____PEM_Ely____heat_)_0) <= +inf
   0 <= flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____PEM_Ely____heat_)_1) <= +inf
   0 <= flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____PEM_Ely____heat_)_2) <= +inf
   0 <= flow((_house_1____PEM_Ely____electrolyser_)_(_house_1____PEM_Ely____heat_)_3) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_0) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_1) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_2) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_3) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_0) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_1) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_2) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_3) <= +inf
   0.0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_0) <= 38300147.20992288
   0.0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_1) <= 41361462.58747426
   0.0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_2) <= 44277706.82770886
   0.0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_3) <= 47042094.28474373
   0 <= flow((_house_1____H2_Storage____in_5_)_(_house_1____H2_Storage____multiplexer_)_0) <= 10
   0 <= flow((_house_1____H2_Storage____in_5_)_(_house_1____H2_Storage____multiplexer_)_1) <= 10
   0 <= flow((_house_1____H2_Storage____in_5_)_(_house_1____H2_Storage____multiplexer_)_2) <= 10
   0 <= flow((_house_1____H2_Storage____in_5_)_(_house_1____H2_Storage____multiplexer_)_3) <= 10
   0 <= flow((_house_1____H2_Storage____out_5_)_(_house_1____GasCarrier____Hydrogen_5_)_0) <= +inf
   0 <= flow((_house_1____H2_Storage____out_5_)_(_house_1____GasCarrier____Hydrogen_5_)_1) <= +inf
   0 <= flow((_house_1____H2_Storage____out_5_)_(_house_1____GasCarrier____Hydrogen_5_)_2) <= +inf
   0 <= flow((_house_1____H2_Storage____out_5_)_(_house_1____GasCarrier____Hydrogen_5_)_3) <= +inf
   0 <= flow((_house_1____H2_Storage____in_30_)_(_house_1____H2_Storage____multiplexer_)_0) <= 10
   0 <= flow((_house_1____H2_Storage____in_30_)_(_house_1____H2_Storage____multiplexer_)_1) <= 10
   0 <= flow((_house_1____H2_Storage____in_30_)_(_house_1____H2_Storage____multiplexer_)_2) <= 10
   0 <= flow((_house_1____H2_Storage____in_30_)_(_house_1____H2_Storage____multiplexer_)_3) <= 10
   0 <= flow((_house_1____H2_Storage____out_30_)_(_house_1____GasCarrier____Hydrogen_30_)_0) <= +inf
   0 <= flow((_house_1____H2_Storage____out_30_)_(_house_1____GasCarrier____Hydrogen_30_)_1) <= +inf
   0 <= flow((_house_1____H2_Storage____out_30_)_(_house_1____GasCarrier____Hydrogen_30_)_2) <= +inf
   0 <= flow((_house_1____H2_Storage____out_30_)_(_house_1____GasCarrier____Hydrogen_30_)_3) <= +inf
   0 <= flow((_house_1____H2_Storage____in_40_)_(_house_1____H2_Storage____multiplexer_)_0) <= 10
   0 <= flow((_house_1____H2_Storage____in_40_)_(_house_1____H2_Storage____multiplexer_)_1) <= 10
   0 <= flow((_house_1____H2_Storage____in_40_)_(_house_1____H2_Storage____multiplexer_)_2) <= 10
   0 <= flow((_house_1____H2_Storage____in_40_)_(_house_1____H2_Storage____multiplexer_)_3) <= 10
   0 <= flow((_house_1____H2_Storage____out_40_)_(_house_1____GasCarrier____Hydrogen_40_)_0) <= +inf
   0 <= flow((_house_1____H2_Storage____out_40_)_(_house_1____GasCarrier____Hydrogen_40_)_1) <= +inf
   0 <= flow((_house_1____H2_Storage____out_40_)_(_house_1____GasCarrier____Hydrogen_40_)_2) <= +inf
   0 <= flow((_house_1____H2_Storage____out_40_)_(_house_1____GasCarrier____Hydrogen_40_)_3) <= +inf
   0 <= flow((_house_1____H2_Storage____in_70_)_(_house_1____H2_Storage____multiplexer_)_0) <= 10
   0 <= flow((_house_1____H2_Storage____in_70_)_(_house_1____H2_Storage____multiplexer_)_1) <= 10
   0 <= flow((_house_1____H2_Storage____in_70_)_(_house_1____H2_Storage____multiplexer_)_2) <= 10
   0 <= flow((_house_1____H2_Storage____in_70_)_(_house_1____H2_Storage____multiplexer_)_3) <= 10
   0 <= flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_5_)_0) <= 10
   0 <= flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_5_)_1) <= 10
   0 <= flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_5_)_2) <= 10
   0 <= flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_5_)_3) <= 10
   0 <= flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_30_)_0) <= 10
   0 <= flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_30_)_1) <= 10
   0 <= flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_30_)_2) <= 10
   0 <= flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_30_)_3) <= 10
   0 <= flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_40_)_0) <= 10
   0 <= flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_40_)_1) <= 10
   0 <= flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_40_)_2) <= 10
   0 <= flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____out_40_)_3) <= 10
   0 <= flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____storage_)_0) <= +inf
   0 <= flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____storage_)_1) <= +inf
   0 <= flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____storage_)_2) <= +inf
   0 <= flow((_house_1____H2_Storage____multiplexer_)_(_house_1____H2_Storage____storage_)_3) <= +inf
   0 <= flow((_house_1____H2_Storage____storage_)_(_house_1____H2_Storage____multiplexer_)_0) <= +inf
   0 <= flow((_house_1____H2_Storage____storage_)_(_house_1____H2_Storage____multiplexer_)_1) <= +inf
   0 <= flow((_house_1____H2_Storage____storage_)_(_house_1____H2_Storage____multiplexer_)_2) <= +inf
   0 <= flow((_house_1____H2_Storage____storage_)_(_house_1____H2_Storage____multiplexer_)_3) <= +inf
   0 <= flow((_house_1____Heat_Sink____output_)_(_house_1____Heat_Sink____sink_)_0) <= +inf
   0 <= flow((_house_1____Heat_Sink____output_)_(_house_1____Heat_Sink____sink_)_1) <= +inf
   0 <= flow((_house_1____Heat_Sink____output_)_(_house_1____Heat_Sink____sink_)_2) <= +inf
   0 <= flow((_house_1____Heat_Sink____output_)_(_house_1____Heat_Sink____sink_)_3) <= +inf
   0 <= flow((_house_1____Heat_Sink____sink_40_)_(_house_1____HeatCarrier____T_20_)_0) <= +inf
   0 <= flow((_house_1____Heat_Sink____sink_40_)_(_house_1____HeatCarrier____T_20_)_1) <= +inf
   0 <= flow((_house_1____Heat_Sink____sink_40_)_(_house_1____HeatCarrier____T_20_)_2) <= +inf
   0 <= flow((_house_1____Heat_Sink____sink_40_)_(_house_1____HeatCarrier____T_20_)_3) <= +inf
   0.0 <= flow((_house_1____Heat_Sink____sink_40_)_(_house_1____Heat_Sink____output_)_0) <= 20000000.0
   0.0 <= flow((_house_1____Heat_Sink____sink_40_)_(_house_1____Heat_Sink____output_)_1) <= 20000000.0
   0.0 <= flow((_house_1____Heat_Sink____sink_40_)_(_house_1____Heat_Sink____output_)_2) <= 20000000.0
   0.0 <= flow((_house_1____Heat_Sink____sink_40_)_(_house_1____Heat_Sink____output_)_3) <= 20000000.0
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_5_)_0) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_5_)_1) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_5_)_2) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_5_)_3) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_30_)_0) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_30_)_1) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_30_)_2) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_30_)_3) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_40_)_0) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_40_)_1) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_40_)_2) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_40_)_3) <= 1
   0.0 <= GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_0) <= 27.28384429674408
   0.0 <= GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_1) <= 27.28384429674408
   0.0 <= GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_2) <= 27.28384429674408
   0.0 <= GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_3) <= 27.28384429674408
   0.0 <= GenericStorageBlock_storage_content((_house_1____H2_Storage____storage_)_4) <= 27.28384429674408
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_5_)_0) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_5_)_1) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_5_)_2) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_5_)_3) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_30_)_0) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_30_)_1) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_30_)_2) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_30_)_3) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_40_)_0) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_40_)_1) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_40_)_2) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_40_)_3) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_70_)_0) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_70_)_1) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_70_)_2) <= 1
   0 <= _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_70_)_3) <= 1
   -inf <= GenericStorageBlock_storage_losses((_house_1____H2_Storage____storage_)_0) <= +inf
   -inf <= GenericStorageBlock_storage_losses((_house_1____H2_Storage____storage_)_1) <= +inf
   -inf <= GenericStorageBlock_storage_losses((_house_1____H2_Storage____storage_)_2) <= +inf
   -inf <= GenericStorageBlock_storage_losses((_house_1____H2_Storage____storage_)_3) <= +inf
binary
  _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_5_)_0)
  _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_5_)_1)
  _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_5_)_2)
  _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_5_)_3)
  _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_30_)_0)
  _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_30_)_1)
  _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_30_)_2)
  _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_30_)_3)
  _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_40_)_0)
  _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_40_)_1)
  _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_40_)_2)
  _(_house_1____H2_Storage____level_constraint_)_active_output_((_house_1____H2_Storage____out_40_)_3)
  _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_5_)_0)
  _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_5_)_1)
  _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_5_)_2)
  _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_5_)_3)
  _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_30_)_0)
  _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_30_)_1)
  _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_30_)_2)
  _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_30_)_3)
  _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_40_)_0)
  _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_40_)_1)
  _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_40_)_2)
  _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_40_)_3)
  _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_70_)_0)
  _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_70_)_1)
  _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_70_)_2)
  _(_house_1____H2_Storage____level_constraint_)_active_input_((_house_1____H2_Storage____in_70_)_3)
end
