#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "shape_msgs::shape_msgs__rosidl_generator_py" for configuration "Release"
set_property(TARGET shape_msgs::shape_msgs__rosidl_generator_py APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(shape_msgs::shape_msgs__rosidl_generator_py PROPERTIES
  IMPORTED_LINK_DEPENDENT_LIBRARIES_RELEASE "shape_msgs::shape_msgs__rosidl_generator_c;shape_msgs::shape_msgs__rosidl_typesupport_c;geometry_msgs::geometry_msgs__rosidl_generator_c;geometry_msgs::geometry_msgs__rosidl_typesupport_fastrtps_c;geometry_msgs::geometry_msgs__rosidl_typesupport_introspection_c;geometry_msgs::geometry_msgs__rosidl_typesupport_c;geometry_msgs::geometry_msgs__rosidl_typesupport_fastrtps_cpp;geometry_msgs::geometry_msgs__rosidl_typesupport_introspection_cpp;geometry_msgs::geometry_msgs__rosidl_typesupport_cpp;geometry_msgs::geometry_msgs__rosidl_generator_py;std_msgs::std_msgs__rosidl_generator_c;std_msgs::std_msgs__rosidl_typesupport_fastrtps_c;std_msgs::std_msgs__rosidl_typesupport_fastrtps_cpp;std_msgs::std_msgs__rosidl_typesupport_introspection_c;std_msgs::std_msgs__rosidl_typesupport_c;std_msgs::std_msgs__rosidl_typesupport_introspection_cpp;std_msgs::std_msgs__rosidl_typesupport_cpp;std_msgs::std_msgs__rosidl_generator_py"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libshape_msgs__rosidl_generator_py.so"
  IMPORTED_SONAME_RELEASE "libshape_msgs__rosidl_generator_py.so"
  )

list(APPEND _cmake_import_check_targets shape_msgs::shape_msgs__rosidl_generator_py )
list(APPEND _cmake_import_check_files_for_shape_msgs::shape_msgs__rosidl_generator_py "${_IMPORT_PREFIX}/lib/libshape_msgs__rosidl_generator_py.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
