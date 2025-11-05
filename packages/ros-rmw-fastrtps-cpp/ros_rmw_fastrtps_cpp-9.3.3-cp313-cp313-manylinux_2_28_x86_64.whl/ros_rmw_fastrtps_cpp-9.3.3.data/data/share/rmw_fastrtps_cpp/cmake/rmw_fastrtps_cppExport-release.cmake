#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "rmw_fastrtps_cpp::rmw_fastrtps_cpp" for configuration "Release"
set_property(TARGET rmw_fastrtps_cpp::rmw_fastrtps_cpp APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rmw_fastrtps_cpp::rmw_fastrtps_cpp PROPERTIES
  IMPORTED_LINK_DEPENDENT_LIBRARIES_RELEASE "rcpputils::rcpputils;rcutils::rcutils;rmw_dds_common::rmw_dds_common_library;rosidl_dynamic_typesupport::rosidl_dynamic_typesupport;rosidl_dynamic_typesupport_fastrtps::rosidl_dynamic_typesupport_fastrtps;rosidl_typesupport_fastrtps_c::rosidl_typesupport_fastrtps_c;tracetools::tracetools"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/librmw_fastrtps_cpp.so"
  IMPORTED_SONAME_RELEASE "librmw_fastrtps_cpp.so"
  )

list(APPEND _cmake_import_check_targets rmw_fastrtps_cpp::rmw_fastrtps_cpp )
list(APPEND _cmake_import_check_files_for_rmw_fastrtps_cpp::rmw_fastrtps_cpp "${_IMPORT_PREFIX}/lib/librmw_fastrtps_cpp.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
